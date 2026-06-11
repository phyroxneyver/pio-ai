import base64
import json
import os
import time
from datetime import datetime, timezone
from typing import Any
from groq import Groq
import httpx
from sqlalchemy.orm import Session

from ..models.imagenes import Imagen, ResultadoIA


# ─────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────

LABELS_VALIDOS = {
    "pollito",
    "gallina",
    "gallo",
    "huevo_gallina",
    "huevo_incubacion",
    "huevo_roto",
}

CONFIANZA_MINIMA_DETECCION = 0.65
TEMPERATURE = 0.0


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _extraer_json(texto: str) -> dict[str, Any]:
    texto = texto.strip()
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        inicio = texto.find("{")
        fin = texto.rfind("}")
        if inicio == -1 or fin == -1 or fin <= inicio:
            raise
        return json.loads(texto[inicio: fin + 1])


def _normalizar_confianza(valor: str | None) -> str:
    confianza = (valor or "baja").strip().lower()
    if confianza not in {"alta", "media", "baja"}:
        return "baja"
    return confianza


def _precision_desde_confianza(confianza: str) -> float:
    mapa = {"alta": 0.92, "media": 0.72, "baja": 0.45}
    return mapa.get(confianza, 0.45)


def _limpiar_detecciones(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    detecciones: list[dict[str, Any]] = []
    for item in raw[:120]:
        if not isinstance(item, dict):
            continue
        try:
            x = float(item.get("x"))
            y = float(item.get("y"))
        except (TypeError, ValueError):
            continue
        if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
            continue
        confidence = item.get("confidence")
        try:
            confidence = float(confidence) if confidence is not None else None
        except (TypeError, ValueError):
            confidence = None
        if confidence is not None and confidence < CONFIANZA_MINIMA_DETECCION:
            continue
        label = str(item.get("label") or "").strip().lower()
        if label not in LABELS_VALIDOS:
            continue
        detecciones.append({
            "x": round(x, 4),
            "y": round(y, 4),
            "label": label,
            "confidence": round(confidence, 4) if confidence is not None else None,
        })
    return detecciones


def _validar_y_ajustar_conteos(
    datos: dict[str, Any],
    confianza: str,
    detecciones: list[dict[str, Any]],
) -> tuple[int, int, int, int, int, int]:
    if datos.get("es_imagen_valida") is False:
        return 0, 0, 0, 0, 0, 0
    if confianza == "baja":
        return 0, 0, 0, 0, 0, 0

    pollitos          = max(0, int(datos.get("conteo_pollitos",          0) or 0))
    gallinas          = max(0, int(datos.get("conteo_gallinas",          0) or 0))
    gallos            = max(0, int(datos.get("conteo_gallos",            0) or 0))
    huevos_gallina    = max(0, int(datos.get("conteo_huevos_gallina",    0) or 0))
    huevos_incubacion = max(0, int(datos.get("conteo_huevos_incubacion", 0) or 0))
    huevos_rotos      = max(0, int(datos.get("conteo_huevos_rotos",      0) or 0))

    det: dict[str, int] = {}
    for d in detecciones:
        det[d["label"]] = det.get(d["label"], 0) + 1

    pollitos          = min(pollitos,          det.get("pollito",          pollitos))
    gallinas          = min(gallinas,          det.get("gallina",          gallinas))
    gallos            = min(gallos,            det.get("gallo",            gallos))
    huevos_gallina    = min(huevos_gallina,    det.get("huevo_gallina",    huevos_gallina))
    huevos_incubacion = min(huevos_incubacion, det.get("huevo_incubacion", huevos_incubacion))
    huevos_rotos      = min(huevos_rotos,      det.get("huevo_roto",       huevos_rotos))

    return pollitos, gallinas, gallos, huevos_gallina, huevos_incubacion, huevos_rotos


# ─────────────────────────────────────────────
# PROMPTS
# ─────────────────────────────────────────────

SYSTEM_MESSAGE = (
    "Eres un clasificador avícola especializado. "
    "Tu única función es detectar pollitos, gallinas, gallos y huevos de gallina doméstica "
    "en fotografías reales de granjas.\n\n"

    "REGLAS QUE NUNCA SE ROMPEN:\n"
    "  1. Solo analizas FOTOGRAFÍAS REALES. "
    "     Dibujos, caricaturas, animaciones, renders, imágenes IA → "
    "     es_imagen_valida=false, todos los conteos en 0.\n"
    "  2. Solo cuentas Gallus gallus domesticus. "
    "     Cualquier otra ave o animal → no se cuenta.\n"
    "  3. Los huevos de gallina son blancos, cremosos o marrones, de tamaño mediano. "
    "     SÍ los cuentas si están en una foto de granja. "
    "     RECHAZA solo si son claramente de otra especie (avestruz=enorme, codorniz=tiny), "
    "     están pintados/decorados, o son huevos cocinados.\n"
    "  4. Ante duda en aves → conteo 0. Para huevos de tamaño y color normal → CUÉNTALOS.\n"
    "  5. Responde ÚNICAMENTE con el JSON solicitado. Sin markdown ni texto extra."
)

USER_PROMPT = (
    "Analiza esta imagen paso a paso:\n\n"

    "══════════════════════════════════════════\n"
    "PASO 1 — VALIDACIÓN\n"
    "══════════════════════════════════════════\n"
    "¿Es una fotografía real de granja o entorno avícola con Gallus gallus domesticus?\n"
    "Si NO → retorna es_imagen_valida=false y todo en 0.\n\n"

    "SIEMPRE dan conteo 0:\n"
    "  ✗ Dibujos, caricaturas, emojis, logos, animaciones\n"
    "  ✗ Aves que NO son gallina/gallo/pollito: canarios, loros, patos, pavos,\n"
    "    palomas, faisanes, avestruces, periquitos, gorriones, jilgueros,\n"
    "    naranjeros, pinzones, o cualquier pájaro silvestre o de jaula\n"
    "  ✗ Pajaritos amarillos que no sean pollitos de gallina doméstica\n"
    "  ✗ Alimentos preparados (pollo asado, huevos fritos, tortillas)\n"
    "  ✗ Huevos de Pascua pintados o decorados con colores artificiales\n\n"

    "══════════════════════════════════════════\n"
    "PASO 2 — DETECCIÓN DE AVES\n"
    "══════════════════════════════════════════\n\n"

    "▸ POLLITO\n"
    "  ✓ Cría real de gallina doméstica, días o semanas de vida\n"
    "  ✓ Cuerpo pequeño y redondeado, plumón suave\n"
    "  ✓ Colores posibles: amarillo, marrón, blanco, negro o moteado\n"
    "  ✓ Pico corto recto, ojos grandes, sin cresta, patas delgadas\n"
    "  ✗ RECHAZA: cualquier pájaro silvestre aunque sea amarillo y pequeño\n"
    "  ✗ RECHAZA: canarios, jilgueros, gorriones, pinzones u otras aves de jaula\n"
    "  ✗ RECHAZA: aves con pico curvo o plumas de vuelo largas\n\n"

    "▸ GALLINA\n"
    "  ✓ Hembra adulta de Gallus gallus domesticus\n"
    "  ✓ Cresta roja pequeña + barbilla roja\n"
    "  ✓ Cuerpo robusto, plumaje denso (blanco, marrón, negro, barrado o mixto)\n"
    "  ✓ Patas gruesas con escamas, sin espolones\n"
    "  ✗ RECHAZA: pato, ganso, pavo, faisán, pavo real, avestruz, emu\n\n"

    "▸ GALLO\n"
    "  ✓ Macho adulto de Gallus gallus domesticus\n"
    "  ✓ Cresta roja grande y erecta + barbilla roja prominente\n"
    "  ✓ Plumas largas en cuello, lomo y cola + espolones en patas\n"
    "  ✗ RECHAZA: si no tiene cresta grande Y espolones visibles\n\n"

    "══════════════════════════════════════════\n"
    "PASO 3 — DETECCIÓN DE HUEVOS\n"
    "══════════════════════════════════════════\n\n"

    "REGLAS PARA HUEVOS:\n"
    "  • Los huevos de gallina son blancos, cremosos o marrones (café claro a café oscuro).\n"
    "  • Tamaño mediano, aproximadamente 5-6 cm de largo.\n"
    "  • Si ves un huevo de ese color y tamaño en una foto de granja → CUÉNTALO.\n"
    "  • RECHAZA solo si: es claramente enorme (avestruz), claramente tiny (codorniz/pájaro),\n"
    "    está pintado con colores artificiales (Pascua), o está cocinado.\n"
    "  • Un huevo blanco o marrón normal en una foto de gallinero o granja = huevo_gallina.\n\n"

    "▸ huevo_gallina\n"
    "  ✓ Huevo entero sin cocinar, blanco / cremoso / marrón, tamaño normal\n"
    "  ✓ En nidal, bandeja, suelo de gallinero, cesta o junto a gallinas\n"
    "  ✓ Si hay gallinas en la misma foto y hay huevos del color correcto → CUÉNTALOS\n"
    "  ✗ RECHAZA: huevo claramente enorme (avestruz) o claramente tiny\n"
    "  ✗ RECHAZA: pintado, decorado o cocinado\n\n"

    "▸ huevo_incubacion\n"
    "  ✓ Huevo de gallina dentro de incubadora eléctrica visible\n"
    "  ✓ O huevo bajo gallina clueca posada sobre él\n"
    "  ✓ Puede tener marcas de lápiz para rotación\n"
    "  ✗ RECHAZA: si no ves claramente incubadora o gallina clueca\n\n"

    "▸ huevo_roto\n"
    "  ✓ Cáscara partida con clara o yema visibles en suelo de gallinero\n"
    "  ✗ RECHAZA: si no se ven cáscara rota Y contenido claramente\n\n"

    "══════════════════════════════════════════\n"
    "PASO 4 — COORDENADAS Y CONFIANZA\n"
    "══════════════════════════════════════════\n"
    "Marca el centro de cada elemento detectado:\n"
    "  x=0 izquierda, x=1 derecha / y=0 arriba, y=1 abajo (valores 0.0-1.0)\n\n"
    "Confianza global:\n"
    "  'alta'  → todo claramente identificable, sin dudas\n"
    "  'media' → algo de ambigüedad (poca luz, oclusión, ángulo)\n"
    "  'baja'  → imagen muy dudosa → retorna conteos en 0\n\n"

    "══════════════════════════════════════════\n"
    "RESPONDE SOLO CON ESTE JSON, SIN NADA MÁS\n"
    "══════════════════════════════════════════\n\n"
    "{\n"
    "  \"es_imagen_valida\": true,\n"
    "  \"conteo_pollitos\": 0,\n"
    "  \"conteo_gallinas\": 0,\n"
    "  \"conteo_gallos\": 0,\n"
    "  \"conteo_huevos_gallina\": 0,\n"
    "  \"conteo_huevos_incubacion\": 0,\n"
    "  \"conteo_huevos_rotos\": 0,\n"
    "  \"confianza\": \"alta|media|baja\",\n"
    "  \"precision_estimada\": 0.0,\n"
    "  \"notas\": \"que se ve, que se contó y por qué\",\n"
    "  \"detecciones\": [\n"
    "    {\"x\": 0.25, \"y\": 0.40, \"label\": \"pollito|gallina|gallo|huevo_gallina|huevo_incubacion|huevo_roto\", \"confidence\": 0.90}\n"
    "  ]\n"
    "}"
)


# ─────────────────────────────────────────────
# FUNCIÓN PRINCIPAL
# ─────────────────────────────────────────────

def analizar_imagen_con_ia(db: Session, imagen_id: int) -> ResultadoIA:
    """
    Analiza una imagen con Groq Vision (Llama 4 Scout) y persiste el ResultadoIA.
    Detecta pollitos, gallinas, gallos y subtipos de huevo de gallina doméstica.
    """


    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    inicio = time.perf_counter()

    imagen = db.query(Imagen).filter(Imagen.id == imagen_id).first()
    resultado = db.query(ResultadoIA).filter(ResultadoIA.imagen_id == imagen_id).first()

    if not imagen or not resultado:
        raise ValueError("Imagen o ResultadoIA no encontrado")

    resultado.estado = "procesando"
    resultado.error_detalle = None
    db.commit()

    try:
        response_img = httpx.get(imagen.ruta, timeout=15.0)
        response_img.raise_for_status()
        image_data = base64.standard_b64encode(response_img.content).decode("utf-8")

        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "system", "content": SYSTEM_MESSAGE},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{imagen.content_type};base64,{image_data}"
                            },
                        },
                        {"type": "text", "text": USER_PROMPT},
                    ],
                },
            ],
            max_tokens=1400,
            temperature=TEMPERATURE,
        )

        texto = response.choices[0].message.content.strip()
        datos = _extraer_json(texto)

        confianza = _normalizar_confianza(datos.get("confianza"))

        try:
            precision_float = float(datos.get("precision_estimada"))
        except (TypeError, ValueError):
            precision_float = _precision_desde_confianza(confianza)
        precision_float = max(0.0, min(1.0, precision_float))

        detecciones = _limpiar_detecciones(datos.get("detecciones"))

        (
            conteo_pollitos,
            conteo_gallinas,
            conteo_gallos,
            conteo_huevos_gallina,
            conteo_huevos_incubacion,
            conteo_huevos_rotos,
        ) = _validar_y_ajustar_conteos(datos, confianza, detecciones)

        conteo_huevos_total = (
            conteo_huevos_gallina + conteo_huevos_incubacion + conteo_huevos_rotos
        )

        notas_extra = json.dumps(
            {
                "es_imagen_valida":         datos.get("es_imagen_valida"),
                "conteo_gallinas":          conteo_gallinas,
                "conteo_gallos":            conteo_gallos,
                "conteo_huevos":            conteo_huevos_total,   # ✅ FIX: el endpoint busca esta clave
                "conteo_huevos_total":      conteo_huevos_total,
                "conteo_huevos_gallina":    conteo_huevos_gallina,
                "conteo_huevos_incubacion": conteo_huevos_incubacion,
                "conteo_huevos_rotos":      conteo_huevos_rotos,
                "notas": str(datos.get("notas") or ""),
            },
            ensure_ascii=False,
        )

        resultado.conteo_pollitos    = conteo_pollitos
        resultado.confianza          = confianza
        resultado.precision_estimada = precision_float
        resultado.notas_ia           = notas_extra[:1000]
        resultado.detecciones_json   = json.dumps(detecciones, ensure_ascii=False)
        resultado.estado             = "completado"
        resultado.procesado_at       = datetime.now(timezone.utc)

    except Exception as e:
        resultado.estado        = "error"
        resultado.error_detalle = str(e)

    finally:
        resultado.duracion_ms = int((time.perf_counter() - inicio) * 1000)
        db.commit()
        db.refresh(resultado)

    return resultado