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

# Labels aceptados — cualquier otra etiqueta del modelo se descarta
LABELS_VALIDOS = {
    "pollito",
    "gallina",
    "gallo",
    "huevo_gallina",       # huevo blanco/marrón claro de gallina doméstica
    "huevo_incubacion",    # huevo marcado o en incubadora
    "huevo_roto",          # huevo partido / con contenido visible
}

# Confianza mínima que debe tener una detección individual para ser guardada
CONFIANZA_MINIMA_DETECCION = 0.65

# Temperatura 0 = respuestas deterministas, sin alucinaciones creativas
TEMPERATURE = 0.0


# ─────────────────────────────────────────────
# HELPERS INTERNOS
# ─────────────────────────────────────────────

def _extraer_json(texto: str) -> dict[str, Any]:
    """Extrae el primer objeto JSON válido del texto del modelo."""
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
    Filtra y normaliza la lista de detecciones devuelta por el modelo.
    Descarta:
      - items sin coordenadas válidas (0-1)
      - items con confidence < CONFIANZA_MINIMA_DETECCION
      - items cuyo label no esté en LABELS_VALIDOS
    """
    if not isinstance(raw, list):
        return []

    detecciones: list[dict[str, Any]] = []
    for item in raw[:120]:
        if not isinstance(item, dict):
            continue

        # Coordenadas obligatorias y dentro de rango
        try:
            x = float(item.get("x"))
            y = float(item.get("y"))
        except (TypeError, ValueError):
            continue
        if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
            continue

        # Confianza (opcional; si existe debe superar el umbral)
        confidence = item.get("confidence")
        try:
            confidence = float(confidence) if confidence is not None else None
        except (TypeError, ValueError):
            confidence = None
        if confidence is not None and confidence < CONFIANZA_MINIMA_DETECCION:
            continue

        # Label debe ser uno de los reconocidos
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

    Reglas:
      1. Si el modelo marcó es_imagen_valida=False → todo 0.
      2. Confianza baja → todo 0 (evita falsos positivos).
      3. El conteo final nunca puede superar las detecciones reales con ese label.
    """
    if datos.get("es_imagen_valida") is False:
        return 0, 0, 0, 0, 0, 0
    if confianza == "baja":
        return 0, 0, 0, 0, 0, 0

    # Conteos crudos del modelo
    pollitos          = max(0, int(datos.get("conteo_pollitos",          0) or 0))
    gallinas          = max(0, int(datos.get("conteo_gallinas",          0) or 0))
    gallos            = max(0, int(datos.get("conteo_gallos",            0) or 0))
    huevos_gallina    = max(0, int(datos.get("conteo_huevos_gallina",    0) or 0))
    huevos_incubacion = max(0, int(datos.get("conteo_huevos_incubacion", 0) or 0))
    huevos_rotos      = max(0, int(datos.get("conteo_huevos_rotos",      0) or 0))

    # Conteo real de detecciones por label (sólo las que pasaron el filtro)
    det: dict[str, int] = {}
    for d in detecciones:
        det[d["label"]] = det.get(d["label"], 0) + 1

    # El conteo nunca puede ser mayor que las detecciones reales
    # (si el modelo reportó 10 pero sólo hay 6 detecciones válidas, usamos 6)
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

SYSTEM_MESSAGE = """Eres un clasificador avícola de precisión industrial entrenado EXCLUSIVAMENTE para detectar:
  • Pollitos reales (crías de Gallus gallus domesticus)
  • Gallinas reales adultas (Gallus gallus domesticus hembra)
  • Gallos reales adultos (Gallus gallus domesticus macho)
  • Huevos reales de gallina doméstica (sin cocinar, en entorno de granja)

REGLAS ABSOLUTAS que NUNCA puedes romper:
  1. Solo analizas FOTOGRAFÍAS REALES. Dibujos, caricaturas, animaciones, renders 3D, capturas de videojuegos, imágenes generadas por IA → conteos en 0, es_imagen_valida=false.
  2. Solo cuentas aves de la especie Gallus gallus domesticus. Canarios, pajaritos, loros, periquitos, patos, pavos, palomas, faisanes, avestruces ni ninguna otra ave o animal → conteos en 0.
  3. Solo cuentas huevos de gallina doméstica sin cocinar en contexto de granja. Huevos cocinados, de Pascua, de otras especies o fuera de contexto → conteo 0.
  4. Ante cualquier duda, el conteo es 0. Es preferible un falso negativo que un falso positivo.
  5. Tu respuesta es ÚNICAMENTE el JSON solicitado. Sin texto adicional, sin markdown, sin explicaciones fuera del campo "notas"."""

USER_PROMPT = """Analiza esta imagen siguiendo ESTRICTAMENTE los pasos en orden:

══════════════════════════════════════════
PASO 1 — VALIDACIÓN DE LA IMAGEN
══════════════════════════════════════════
Responde internamente estas 3 preguntas:
  A) ¿Es una fotografía real (no dibujo, caricatura, animación, render, meme ni imagen IA)?
  B) ¿Muestra un entorno real de granja, corral, gallinero o cría avícola?
  C) ¿Hay presencia visible de Gallus gallus domesticus real o sus huevos?

Si cualquiera de A, B o C es NO → retorna INMEDIATAMENTE:
{"es_imagen_valida": false, "conteo_pollitos": 0, "conteo_gallinas": 0, "conteo_gallos": 0,
 "conteo_huevos_gallina": 0, "conteo_huevos_incubacion": 0, "conteo_huevos_rotos": 0,
 "confianza": "baja", "precision_estimada": 0.0,
 "notas": "Imagen no válida: [motivo específico]", "detecciones": []}

IMÁGENES QUE SIEMPRE FALLAN LA VALIDACIÓN (ejemplos no exhaustivos):
  ✗ Personajes animados: Piolín, Tweety, Chicken Run, Looney Tunes, etc.
  ✗ Fotos de aves silvestres o domésticas que no sean gallinas/gallos/pollitos
  ✗ Pajaritos amarillos, canarios, jilgueros, naranjeros u otras aves de color amarillo
  ✗ Patos, gansos, pavos, faisanes, palomas, loros, periquitos, cacatúas
  ✗ Pinturas, ilustraciones, íconos, logos, emojis con forma de gallina o huevo
  ✗ Huevos de Pascua pintados o decorados
  ✗ Pollo asado, huevos fritos, tortillas u otros alimentos preparados
  ✗ Imágenes sin aves ni huevos (personas, paisajes, objetos)

══════════════════════════════════════════
PASO 2 — DETECCIÓN (solo si PASO 1 fue válido)
══════════════════════════════════════════

Detecta y cuenta estas categorías CON CRITERIOS ESTRICTOS:

▸ POLLITO
  ✓ Cría REAL de gallina doméstica (días o pocas semanas de vida)
  ✓ Cuerpo muy pequeño y redondeado, menor a una palma de mano
  ✓ Plumón suave y esponjoso (puede ser amarillo, marrón, blanco, negro o moteado)
  ✓ Pico corto y recto, ojos grandes proporcionalmente, sin cresta visible
  ✓ Patas muy delgadas, rosadas o grises
  ✗ RECHAZA: cualquier pájaro silvestre aunque sea amarillo o pequeño
  ✗ RECHAZA: canarios, jilgueros, gorriones, pinzones u otras aves pequeñas
  ✗ RECHAZA: aves con pico curvo, alas de vuelo largas, cresta plumosa
  ✗ RECHAZA: si no estás 100% seguro de que es cría de gallina doméstica

▸ GALLINA
  ✓ Hembra adulta real de Gallus gallus domesticus
  ✓ Cresta roja pequeña y erecta, barbilla (papada) roja
  ✓ Cuerpo robusto y redondeado, plumaje denso (blanco, marrón, negro, barrado o mixto)
  ✓ Patas gruesas con escamas visibles, sin espolones prominentes
  ✓ Presente en corral, gallinero o granja real
  ✗ RECHAZA: pata, ganso, pavo, faisán, pavo real, avestruz, emu
  ✗ RECHAZA: aves sin cresta roja visible en contexto adulto

▸ GALLO
  ✓ Macho adulto real de Gallus gallus domesticus
  ✓ Cresta roja grande, erecta y prominente
  ✓ Barbilla roja larga y colgante
  ✓ Plumas largas y brillantes en cuello (hackles), lomo y cola
  ✓ Espolones visibles en patas
  ✓ Postura erguida y dominante
  ✗ RECHAZA: si no tiene cresta grande y espolones claramente visibles

▸ HUEVO DE GALLINA — diferencia el subtipo:

  • huevo_gallina: huevo sin cocinar de gallina doméstica
    ✓ Forma oval característica, tamaño mediano (~5-6 cm largo)
    ✓ Color blanco, blanco-cremoso o marrón (desde muy claro hasta café oscuro)
    ✓ Superficie lisa, sin decoración ni marcas artificiales
    ✓ Contexto: nidal, bandeja de cartón/plástico, suelo de gallinero, cesta
    ✗ RECHAZA: huevos de otras aves (pato, codorniz, avestruz, etc.)
    ✗ RECHAZA: huevos pintados, decorados, de Pascua o de colores artificiales

  • huevo_incubacion: huevo en proceso de incubación
    ✓ Huevo de gallina en incubadora eléctrica o bajo gallina clueca
    ✓ Puede tener marcas de lápiz/bolígrafo para seguimiento de rotación
    ✓ Tamaño y forma igual al huevo normal de gallina
    ✗ RECHAZA: si no está claramente en incubadora o bajo ave clueca

  • huevo_roto: huevo de gallina partido o con contenido visible
    ✓ Cáscara rota con albúmina (clara) o yema visibles
    ✓ En suelo de gallinero o nidal, con residuos de cáscara
    ✗ RECHAZA: si no se ven claramente los restos de cáscara o el contenido

══════════════════════════════════════════
PASO 3 — CONFIANZA Y COORDENADAS
══════════════════════════════════════════

Para cada elemento detectado, marca el centro aproximado con coordenadas normalizadas (0.0 a 1.0):
  • x=0 es borde izquierdo, x=1 es borde derecho
  • y=0 es borde superior, y=1 es borde inferior

Asigna confianza global:
  • "alta": imagen clara, elementos 100% identificables, sin ninguna duda
  • "media": imagen con algo de ambigüedad (poca luz, oclusión parcial, ángulo difícil)
  • "baja": imagen muy dudosa → usa esto y retorna conteos en 0

══════════════════════════════════════════
FORMATO DE RESPUESTA OBLIGATORIO
══════════════════════════════════════════

Responde ÚNICAMENTE con este JSON válido, sin markdown, sin texto extra:

{
  "es_imagen_valida": true,
  "conteo_pollitos": 0,
  "conteo_gallinas": 0,
  "conteo_gallos": 0,
  "conteo_huevos_gallina": 0,
  "conteo_huevos_incubacion": 0,
  "conteo_huevos_rotos": 0,
  "confianza": "alta|media|baja",
  "precision_estimada": 0.0,
  "notas": "descripción breve de lo observado y razonamiento de conteos",
  "detecciones": [
    {"x": 0.25, "y": 0.40, "label": "pollito|gallina|gallo|huevo_gallina|huevo_incubacion|huevo_roto", "confidence": 0.90}
  ]
}"""


# ─────────────────────────────────────────────
# FUNCIÓN PRINCIPAL
# ─────────────────────────────────────────────

def analizar_imagen_con_ia(db: Session, imagen_id: int) -> ResultadoIA:
    """
    Analiza una imagen con Groq Vision (Llama 4 Scout) y persiste el ResultadoIA.

    Detecta: pollitos, gallinas, gallos y tres subtipos de huevo de gallina.
    Rechaza cualquier otra ave, animal, objeto o imagen no fotográfica.
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
        # Descargar la imagen desde la URL almacenada
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

        # ── Confianza global ──
        confianza = _normalizar_confianza(datos.get("confianza"))

        # ── Precisión estimada ──
        try:
            precision_float = float(datos.get("precision_estimada"))
        except (TypeError, ValueError):
            precision_float = _precision_desde_confianza(confianza)
        precision_float = max(0.0, min(1.0, precision_float))

        # ── Detecciones individuales (filtradas) ──
        detecciones = _limpiar_detecciones(datos.get("detecciones"))

        # ── Conteos validados y ajustados ──
        (
            conteo_pollitos,
            conteo_gallinas,
            conteo_gallos,
            conteo_huevos_gallina,
            conteo_huevos_incubacion,
            conteo_huevos_rotos,
        ) = _validar_y_ajustar_conteos(datos, confianza, detecciones)

        # Conteo total de huevos (suma de subtipos)
        conteo_huevos_total = conteo_huevos_gallina + conteo_huevos_incubacion + conteo_huevos_rotos

        # ── Notas enriquecidas ──
        notas_extra = json.dumps(
            {
                "es_imagen_valida": datos.get("es_imagen_valida"),
                "conteo_gallinas": conteo_gallinas,
                "conteo_gallos": conteo_gallos,
                "conteo_huevos_total": conteo_huevos_total,
                "conteo_huevos_gallina": conteo_huevos_gallina,
                "conteo_huevos_incubacion": conteo_huevos_incubacion,
                "conteo_huevos_rotos": conteo_huevos_rotos,
                "notas": str(datos.get("notas") or ""),
            },
            ensure_ascii=False,
        )

        # ── Persistir resultado ──
        # conteo_pollitos → columna existente (se mantiene compatibilidad)
        resultado.conteo_pollitos = conteo_pollitos
        resultado.confianza = confianza
        resultado.precision_estimada = precision_float
        resultado.notas_ia = notas_extra[:1000]
        resultado.detecciones_json = json.dumps(detecciones, ensure_ascii=False)
        resultado.estado = "completado"
        resultado.procesado_at = datetime.now(timezone.utc)

    except Exception as e:
        resultado.estado = "error"
        resultado.error_detalle = str(e)

    finally:
        resultado.duracion_ms = int((time.perf_counter() - inicio) * 1000)
        db.commit()
        db.refresh(resultado)

    return resultado