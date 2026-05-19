import base64
import json
import os
import time
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy.orm import Session

from ..models.imagenes import Imagen, ResultadoIA


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


LABELS_VALIDOS = {"pollito", "gallina", "gallo", "huevo"}
CONFIANZA_MINIMA_DETECCION = 0.65


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
        if not (0 <= x <= 1 and 0 <= y <= 1):
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
            "x": x,
            "y": y,
            "label": label,
            "confidence": confidence,
        })
    return detecciones


def _validar_y_ajustar_conteos(
    datos: dict[str, Any],
    confianza: str,
    detecciones: list[dict[str, Any]],
) -> tuple[int, int, int, int]:
    es_valida = datos.get("es_imagen_valida")
    if es_valida is False:
        return 0, 0, 0, 0
    if confianza == "baja":
        return 0, 0, 0, 0

    conteo_pollitos = int(datos.get("conteo_pollitos", 0) or 0)
    conteo_gallinas = int(datos.get("conteo_gallinas", 0) or 0)
    conteo_gallos   = int(datos.get("conteo_gallos",   0) or 0)
    conteo_huevos   = int(datos.get("conteo_huevos",   0) or 0)

    det_por_label: dict[str, int] = {}
    for d in detecciones:
        det_por_label[d["label"]] = det_por_label.get(d["label"], 0) + 1

    conteo_pollitos = min(conteo_pollitos, det_por_label.get("pollito", conteo_pollitos))
    conteo_gallinas = min(conteo_gallinas, det_por_label.get("gallina", conteo_gallinas))
    conteo_gallos   = min(conteo_gallos,   det_por_label.get("gallo",   conteo_gallos))
    conteo_huevos   = min(conteo_huevos,   det_por_label.get("huevo",   conteo_huevos))

    return conteo_pollitos, conteo_gallinas, conteo_gallos, conteo_huevos


def analizar_imagen_con_ia(db: Session, imagen_id: int) -> ResultadoIA:
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
        response_img = httpx.get(imagen.ruta, timeout=15.0)
        response_img.raise_for_status()
        image_data = base64.standard_b64encode(response_img.content).decode("utf-8")

        system_message = (
            "Eres un clasificador avícola de precisión industrial. "
            "SOLO reconoces gallinas, gallos, pollitos y huevos en fotografías reales de granjas. "
            "NUNCA identificas aves de dibujos, caricaturas, animaciones ni ilustraciones como aves reales. "
            "Si la imagen no es una fotografía real de una granja con Gallus gallus domesticus, "
            "devuelves SIEMPRE es_imagen_valida=false y todos los conteos en 0. "
            "Tu prioridad es la precisión: es preferible devolver 0 que un falso positivo."
        )

        prompt = (
            "Eres un sistema de visión especializado EXCLUSIVAMENTE en avicultura de granja real. "
            "Tu única función es detectar gallinas, gallos, pollitos y huevos en fotografías reales de granjas.\n\n"

            "═══ PASO 1: VERIFICACIÓN DE IMAGEN ═══\n"
            "ANTES de analizar cualquier objeto, determina si la imagen cumple TODOS estos requisitos:\n"
            "  a) Es una FOTOGRAFÍA REAL (no un dibujo, caricatura, animación, ilustración, render 3D, pintura, meme, captura de pantalla de videojuego ni imagen generada por IA).\n"
            "  b) Muestra un entorno REAL de granja, corral, gallinero o zona de cría avícola.\n"
            "  c) Contiene aves que son FÍSICAMENTE de la especie Gallus gallus domesticus (gallina doméstica real).\n"
            "Si la imagen FALLA cualquiera de estos puntos, retorna INMEDIATAMENTE todos los conteos en 0, "
            "\"es_imagen_valida\": false y confianza 'baja'.\n\n"

            "EJEMPLOS DE IMÁGENES QUE DEBEN DAR CONTEO 0:\n"
            "  - Caricaturas o personajes animados (por ejemplo: Piolín, Looney Tunes, Chicken Run, cualquier ave dibujada).\n"
            "  - Fotos de aves silvestres, canarios, loros, periquitos, patos, pavos, avestruces, flamencos u otras especies.\n"
            "  - Imágenes de juguetes, figuras de plástico o estatuas de gallinas.\n"
            "  - Fotos de alimentos preparados (pollo asado, huevos fritos, etc.).\n"
            "  - Imágenes de personas, paisajes sin aves, o ambientes urbanos.\n\n"

            "═══ PASO 2: DETECCIÓN (solo si pasó el PASO 1) ═══\n"
            "Detecta ÚNICAMENTE estas 4 categorías en fotografías reales de granja:\n\n"

            "1. POLLITO: Cría REAL de gallina doméstica, de días o pocas semanas de vida. "
            "Características físicas: cuerpo muy pequeño y redondeado, plumón suave (amarillo, marrón, blanco o negro), "
            "pico corto recto, ojos grandes en proporción a la cabeza, patas muy delgadas rosadas o grises, sin cresta visible aún. "
            "RECHAZA si: tiene plumas largas, cresta, espuelas, o si es cualquier pájaro que no sea cría de gallina doméstica. "
            "RECHAZA si: es un dibujo, caricatura o imagen no fotográfica.\n\n"

            "2. GALLINA: Hembra adulta de gallina doméstica REAL. "
            "Características: cresta roja pequeña erecta, barbilla roja, cuerpo robusto y redondeado, plumaje denso uniforme, "
            "patas gruesas con escamas, presente en corral o granja real. "
            "RECHAZA si: es pata, pavo, faisán, pavo real u otra ave distinta a Gallus gallus domesticus.\n\n"

            "3. GALLO: Macho adulto de gallina doméstica REAL. "
            "Características: cresta roja grande y erguida, barbilla roja prominente, plumas largas y coloridas en cola y cuello, "
            "espolones en las patas, postura erguida dominante. "
            "RECHAZA si no es claramente un gallo de granja real.\n\n"

            "4. HUEVO: Huevo oval sin cocinar de gallina, en entorno de granja real (nidal, bandeja, suelo de gallinero). "
            "RECHAZA si es huevo cocinado, huevo de Pascua decorado, huevo de otra especie, o si está fuera de contexto avícola.\n\n"

            "═══ REGLA CRÍTICA ═══\n"
            "Si tienes CUALQUIER duda de que un objeto sea lo que parece, NO lo cuentes. "
            "Es preferible un conteo menor que un falso positivo. "
            "La confianza debe ser 'alta' solo si estás completamente seguro. "
            "Usa 'media' si hay algo de ambigüedad. Usa 'baja' o retorna 0 si la imagen es dudosa.\n\n"

            "Responde SOLO con JSON válido sin markdown, sin explicaciones adicionales, con este formato exacto:\n"
            "{\"es_imagen_valida\": true, \"conteo_pollitos\": 0, \"conteo_gallinas\": 0, \"conteo_gallos\": 0, \"conteo_huevos\": 0, "
            "\"confianza\": \"alta|media|baja\", \"precision_estimada\": 0.0, "
            "\"notas\": \"descripcion breve de lo que se ve y por qué se asignaron esos conteos\", "
            "\"detecciones\": [{\"x\": 0.5, \"y\": 0.5, \"label\": \"pollito|gallina|gallo|huevo\", \"confidence\": 0.8}]}"
        )

        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "system", "content": system_message},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{imagen.content_type};base64,{image_data}"
                            }
                        },
                        {"type": "text", "text": prompt}
                    ]
                }
            ],
            max_tokens=1200,
            temperature=0.0,
        )

        texto = response.choices[0].message.content.strip()
        datos = _extraer_json(texto)

        confianza = _normalizar_confianza(datos.get("confianza"))

        precision = datos.get("precision_estimada")
        try:
            precision_float = float(precision)
        except (TypeError, ValueError):
            precision_float = _precision_desde_confianza(confianza)
        precision_float = max(0.0, min(1.0, precision_float))

        detecciones = _limpiar_detecciones(datos.get("detecciones"))

        conteo_pollitos, conteo_gallinas, conteo_gallos, conteo_huevos = (
            _validar_y_ajustar_conteos(datos, confianza, detecciones)
        )

        notas_extra = json.dumps({
            "es_imagen_valida": datos.get("es_imagen_valida"),
            "conteo_gallinas": conteo_gallinas,
            "conteo_gallos": conteo_gallos,
            "conteo_huevos": conteo_huevos,
            "notas": str(datos.get("notas") or ""),
        }, ensure_ascii=False)

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