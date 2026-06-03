import base64
import json
import os
import time
from datetime import datetime, timezone
from typing import Any

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
    "huevo_gallina",     # huevo entero normal en nidal/bandeja/gallinero
    "huevo_incubacion",  # huevo en incubadora eléctrica o bajo gallina clueca
    "huevo_roto",        # huevo partido con contenido visible
}

# Una detección individual debe superar este umbral para ser guardada
CONFIANZA_MINIMA_DETECCION = 0.70

# Temperatura 0 = determinista, sin creatividad ni alucinaciones
TEMPERATURE = 0.0


# ─────────────────────────────────────────────
# HELPERS INTERNOS
# ─────────────────────────────────────────────

def _extraer_json(texto: str) -> dict[str, Any]:
    """Extrae el primer objeto JSON válido del texto devuelto por el modelo."""
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
    """
    Filtra y normaliza la lista de detecciones del modelo.
    Descarta:
      - coordenadas fuera del rango 0-1
      - confidence por debajo del umbral mínimo
      - labels que no estén en LABELS_VALIDOS
    """
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
    """
    Devuelve (pollitos, gallinas, gallos, huevos_gallina, huevos_incubacion, huevos_rotos).

    Reglas de seguridad:
      1. es_imagen_valida=False  → todo 0.
      2. confianza baja          → todo 0.
      3. hay_contexto_avicola=False para huevos → huevos en 0.
      4. Conteo final nunca supera las detecciones reales con ese label.
    """
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

    # Si el modelo indica que NO hay contexto avícola confirmado → huevos en 0
    if datos.get("hay_contexto_avicola") is False:
        huevos_gallina    = 0
        huevos_incubacion = 0
        huevos_rotos      = 0

    # Conteo real de detecciones filtradas por label
    det: dict[str, int] = {}
    for d in detecciones:
        det[d["label"]] = det.get(d["label"], 0) + 1

    # El conteo nunca puede ser mayor que las detecciones reales
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
    "Eres un clasificador avícola de precisión industrial. "
    "Detectas ÚNICAMENTE: pollitos, gallinas, gallos y huevos de gallina doméstica "
    "en fotografías reales de granjas o corrales.\n\n"

    "REGLAS ABSOLUTAS — nunca se rompen:\n"
    "  1. Solo analizas FOTOGRAFÍAS REALES. "
    "     Dibujos, caricaturas, animaciones, renders 3D, videojuegos, imágenes IA → "
    "     es_imagen_valida=false, todos los conteos en 0.\n"
    "  2. Solo cuentas Gallus gallus domesticus. "
    "     Cualquier otra ave o animal → no se cuenta.\n"
    "  3. Para contar HUEVOS es OBLIGATORIO que en la misma imagen aparezcan "
    "     gallinas/gallos/pollitos visibles O un gallinero/nidal/incubadora claramente identificable. "
    "     Si no hay ese contexto, hay_contexto_avicola=false y todos los huevos en 0. "
    "     NUNCA identifiques un huevo solo por su forma — el contexto es obligatorio.\n"
    "  4. Ante cualquier duda → conteo 0. Prefiere falso negativo a falso positivo.\n"
    "  5. Responde ÚNICAMENTE con el JSON solicitado. Sin markdown ni texto extra."
)

USER_PROMPT = (
    "Analiza esta imagen siguiendo los pasos en orden estricto:\n\n"

    "══════════════════════════════════════════\n"
    "PASO 1 — VALIDACIÓN DE LA IMAGEN\n"
    "══════════════════════════════════════════\n"
    "Responde internamente:\n"
    "  A) ¿Es una fotografía real? (no dibujo, caricatura, animación, render, meme, IA)\n"
    "  B) ¿Muestra un entorno real de granja, corral, gallinero o cría avícola?\n"
    "  C) ¿Hay presencia de Gallus gallus domesticus real O sus huevos en contexto avícola?\n\n"

    "Si A o B es NO → retorna INMEDIATAMENTE con es_imagen_valida=false y todo en 0.\n\n"

    "IMÁGENES QUE SIEMPRE DAN CONTEO 0:\n"
    "  ✗ Dibujos, caricaturas, animaciones (Piolín, Tweety, Chicken Run, emojis, logos)\n"
    "  ✗ Aves que NO son gallinas/gallos/pollitos: canarios, loros, patos, pavos,\n"
    "    palomas, faisanes, flamencos, avestruces, periquitos, cacatúas, gorriones,\n"
    "    jilgueros, pinzones, naranjeros, o cualquier pájaro silvestre o de jaula\n"
    "  ✗ Pajaritos amarillos de cualquier especie que no sea pollito de gallina\n"
    "  ✗ Huevos de Pascua, huevos pintados o decorados\n"
    "  ✗ Alimentos preparados (pollo asado, huevos fritos, tortillas)\n"
    "  ✗ Personas, paisajes, objetos sin aves\n\n"

    "══════════════════════════════════════════\n"
    "PASO 2 — VERIFICACIÓN DE CONTEXTO AVÍCOLA PARA HUEVOS\n"
    "══════════════════════════════════════════\n"
    "Antes de contar huevos, determina si hay contexto avícola confirmado:\n"
    "  hay_contexto_avicola = true SI en la imagen se ve AL MENOS UNO de:\n"
    "    • Una o más gallinas/gallos/pollitos reales visibles\n"
    "    • Un nidal o caja de postura de gallinero\n"
    "    • Una incubadora eléctrica\n"
    "    • Suelo de gallinero con paja/viruta y excrementos típicos\n"
    "    • Bandeja de cartón con huevos blancos/marrones en gallinero\n"
    "  hay_contexto_avicola = false en todos los demás casos.\n\n"
    "  Si hay_contexto_avicola=false → conteo_huevos_gallina=0, "
    "conteo_huevos_incubacion=0, conteo_huevos_rotos=0.\n\n"

    "══════════════════════════════════════════\n"
    "PASO 3 — DETECCIÓN DE AVES\n"
    "══════════════════════════════════════════\n\n"

    "▸ POLLITO\n"
    "  ✓ Cría REAL de gallina doméstica (días o pocas semanas de vida)\n"
    "  ✓ Cuerpo pequeño y redondeado, cabe en una mano\n"
    "  ✓ Plumón suave (amarillo, marrón, blanco, negro o moteado)\n"
    "  ✓ Pico corto recto, ojos grandes, sin cresta, patas muy delgadas rosadas/grises\n"
    "  ✗ RECHAZA: cualquier pájaro que no sea cría de gallina doméstica\n"
    "  ✗ RECHAZA: canarios, jilgueros, gorriones u otras aves pequeñas aunque sean amarillas\n"
    "  ✗ RECHAZA: aves con pico curvo, plumas de vuelo largas o cresta plumosa\n\n"

    "▸ GALLINA\n"
    "  ✓ Hembra adulta de Gallus gallus domesticus\n"
    "  ✓ Cresta roja pequeña y erecta + barbilla (papada) roja\n"
    "  ✓ Cuerpo robusto, plumaje denso (blanco, marrón, negro, barrado o mixto)\n"
    "  ✓ Patas gruesas con escamas, sin espolones prominentes\n"
    "  ✗ RECHAZA: pato, ganso, pavo, faisán, pavo real, avestruz, emu\n\n"

    "▸ GALLO\n"
    "  ✓ Macho adulto de Gallus gallus domesticus\n"
    "  ✓ Cresta roja grande y erecta + barbilla roja larga y colgante\n"
    "  ✓ Plumas largas y brillantes en cuello, lomo y cola + espolones en patas\n"
    "  ✗ RECHAZA: si no tiene cresta grande Y espolones claramente visibles\n\n"

    "══════════════════════════════════════════\n"
    "PASO 4 — DETECCIÓN DE HUEVOS (solo si hay_contexto_avicola=true)\n"
    "══════════════════════════════════════════\n\n"

    "REGLA CRÍTICA PARA HUEVOS:\n"
    "  • NUNCA cuentes un huevo solo por su forma oval. El contexto avícola es OBLIGATORIO.\n"
    "  • Si tienes duda de si es huevo de gallina u otra especie → NO lo cuentes.\n"
    "  • Huevo de gallina: tamaño mediano ~5-6 cm, color blanco/cremoso/marrón.\n"
    "    Un huevo muy grande (avestruz ~15 cm) o muy pequeño (codorniz ~3 cm) → RECHAZA.\n\n"

    "▸ huevo_gallina\n"
    "  ✓ Huevo entero sin cocinar, tamaño mediano, blanco/cremoso/marrón liso\n"
    "  ✓ En nidal, bandeja de cartón/plástico, suelo de gallinero o cesta\n"
    "  ✓ Hay gallinas visibles en la misma imagen O contexto de gallinero confirmado\n"
    "  ✗ RECHAZA: si no hay contexto avícola\n"
    "  ✗ RECHAZA: huevos pintados, de Pascua, cocinados o de otras especies\n"
    "  ✗ RECHAZA: huevo muy grande (avestruz) o muy pequeño (codorniz, pájaro)\n\n"

    "▸ huevo_incubacion\n"
    "  ✓ Huevo de gallina DENTRO de incubadora eléctrica visible en la foto\n"
    "  ✓ O huevo bajo gallina clueca claramente posada sobre él\n"
    "  ✓ Puede tener marcas de lápiz/bolígrafo para rotación\n"
    "  ✗ RECHAZA: si no ves claramente la incubadora o la gallina clueca\n\n"

    "▸ huevo_roto\n"
    "  ✓ Cáscara partida con clara (albúmina) o yema visibles\n"
    "  ✓ En suelo de gallinero con restos de cáscara\n"
    "  ✗ RECHAZA: si no se ven claramente cáscara rota Y contenido\n\n"

    "══════════════════════════════════════════\n"
    "PASO 5 — COORDENADAS Y CONFIANZA\n"
    "══════════════════════════════════════════\n"
    "Marca el centro de cada elemento con coordenadas normalizadas 0.0-1.0:\n"
    "  x=0 borde izquierdo, x=1 borde derecho\n"
    "  y=0 borde superior, y=1 borde inferior\n\n"
    "Confianza global:\n"
    "  'alta'  → imagen clara, todo 100% identificable, cero dudas\n"
    "  'media' → algo de ambigüedad (poca luz, oclusión, ángulo difícil)\n"
    "  'baja'  → imagen muy dudosa → retorna conteos en 0\n\n"

    "══════════════════════════════════════════\n"
    "FORMATO DE RESPUESTA — SOLO ESTE JSON, SIN NADA MÁS\n"
    "══════════════════════════════════════════\n\n"
    "{\n"
    "  \"es_imagen_valida\": true,\n"
    "  \"hay_contexto_avicola\": true,\n"
    "  \"conteo_pollitos\": 0,\n"
    "  \"conteo_gallinas\": 0,\n"
    "  \"conteo_gallos\": 0,\n"
    "  \"conteo_huevos_gallina\": 0,\n"
    "  \"conteo_huevos_incubacion\": 0,\n"
    "  \"conteo_huevos_rotos\": 0,\n"
    "  \"confianza\": \"alta|media|baja\",\n"
    "  \"precision_estimada\": 0.0,\n"
    "  \"notas\": \"descripcion breve: que se ve, por que se asignaron esos conteos y que se rechazo\",\n"
    "  \"detecciones\": [\n"
    "    {\"x\": 0.25, \"y\": 0.40, "
    "\"label\": \"pollito|gallina|gallo|huevo_gallina|huevo_incubacion|huevo_roto\", "
    "\"confidence\": 0.90}\n"
    "  ]\n"
    "}"
)


# ─────────────────────────────────────────────
# FUNCIÓN PRINCIPAL
# ─────────────────────────────────────────────

def analizar_imagen_con_ia(db: Session, imagen_id: int) -> ResultadoIA:
    """
    Analiza una imagen con Groq Vision (Llama 4 Scout) y persiste el ResultadoIA.

    Detecta: pollitos, gallinas, gallos y tres subtipos de huevo de gallina.
    Rechaza cualquier otra ave, animal, objeto o imagen no fotográfica.
    Los huevos solo se cuentan si hay contexto avícola confirmado en la imagen.
    """
    from groq import Groq

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
        # Descargar imagen desde la URL almacenada
        response_img = httpx.get(imagen.ruta, timeout=15.0)
        response_img.raise_for_status()
        image_data = base64.standard_b64encode(response_img.content).decode("utf-8")

        # Llamada al modelo
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

        # Confianza global
        confianza = _normalizar_confianza(datos.get("confianza"))

        # Precisión estimada
        try:
            precision_float = float(datos.get("precision_estimada"))
        except (TypeError, ValueError):
            precision_float = _precision_desde_confianza(confianza)
        precision_float = max(0.0, min(1.0, precision_float))

        # Detecciones individuales filtradas
        detecciones = _limpiar_detecciones(datos.get("detecciones"))

        # Conteos validados y ajustados
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

        # Notas enriquecidas guardadas en notas_ia
        notas_extra = json.dumps(
            {
                "es_imagen_valida":       datos.get("es_imagen_valida"),
                "hay_contexto_avicola":   datos.get("hay_contexto_avicola"),
                "conteo_gallinas":        conteo_gallinas,
                "conteo_gallos":          conteo_gallos,
                "conteo_huevos_total":    conteo_huevos_total,
                "conteo_huevos_gallina":  conteo_huevos_gallina,
                "conteo_huevos_incubacion": conteo_huevos_incubacion,
                "conteo_huevos_rotos":    conteo_huevos_rotos,
                "notas": str(datos.get("notas") or ""),
            },
            ensure_ascii=False,
        )

        # Persistir — conteo_pollitos usa la columna existente
        resultado.conteo_pollitos    = conteo_pollitos
        resultado.confianza          = confianza
        resultado.precision_estimada = precision_float
        resultado.notas_ia           = notas_extra[:1000]
        resultado.detecciones_json   = json.dumps(detecciones, ensure_ascii=False)
        resultado.estado             = "completado"
        resultado.procesado_at       = datetime.now(timezone.utc)

    except Exception as e:
        resultado.estado       = "error"
        resultado.error_detalle = str(e)

    finally:
        resultado.duracion_ms = int((time.perf_counter() - inicio) * 1000)
        db.commit()
        db.refresh(resultado)

    return resultado