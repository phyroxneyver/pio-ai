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
    mapa = {
        "alta": 0.92,
        "media": 0.72,
        "baja": 0.45,
    }

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

        if not (0 <= x <= 1 and 0 <= y <= 1):
            continue

        confidence = item.get("confidence")

        try:
            confidence = float(confidence) if confidence is not None else None
        except (TypeError, ValueError):
            confidence = None

        detecciones.append({
            "x": x,
            "y": y,
            "label": str(item.get("label") or "pollito"),
            "confidence": confidence,
        })

    return detecciones


def analizar_imagen_con_ia(db: Session, imagen_id: int) -> ResultadoIA:
    """Analiza una imagen con Gemini Vision y actualiza el ResultadoIA."""
    import google.generativeai as genai

    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

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

        model = genai.GenerativeModel("gemini-2.0-flash")

        image_part = {
            "mime_type": imagen.content_type,
            "data": image_data,
        }

        prompt = (
            "Cuenta cuántos pollitos hay en esta imagen. "
            "Además, entrega puntos aproximados del centro de cada pollito para dibujar un comparador visual. "
            "Usa coordenadas normalizadas entre 0 y 1, donde x=0 es izquierda, x=1 derecha, y=0 arriba, y=1 abajo. "
            "Responde SOLO JSON válido, sin markdown, con este formato exacto: "
            "{\"conteo\": 0, \"confianza\": \"alta|media|baja\", \"precision_estimada\": 0.0, "
            "\"notas\": \"observación breve\", "
            "\"detecciones\": [{\"x\": 0.5, \"y\": 0.5, \"label\": \"pollito\", \"confidence\": 0.8}]}"
        )

        response = model.generate_content([image_part, prompt])

        texto = response.text.strip()
        datos = _extraer_json(texto)

        conteo = int(datos.get("conteo", 0) or 0)
        confianza = _normalizar_confianza(datos.get("confianza"))

        precision = datos.get("precision_estimada")

        try:
            precision_float = float(precision)
        except (TypeError, ValueError):
            precision_float = _precision_desde_confianza(confianza)

        precision_float = max(0.0, min(1.0, precision_float))

        detecciones = _limpiar_detecciones(datos.get("detecciones"))

        resultado.conteo_pollitos = conteo
        resultado.confianza = confianza
        resultado.precision_estimada = precision_float
        resultado.notas_ia = str(datos.get("notas") or "")[:1000]
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