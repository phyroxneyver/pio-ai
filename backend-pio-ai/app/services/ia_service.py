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
        label = str(item.get("label") or "desconocido").lower()
        if label not in {"pollito", "gallina", "gallo", "huevo"}:
            label = "desconocido"
            
        detecciones.append({
            "x": x,
            "y": y,
            "label": label,
            "confidence": confidence,
        })
    return detecciones


def analizar_imagen_con_ia(db: Session, imagen_id: int) -> ResultadoIA:
    """Analiza una imagen con Groq Vision y actualiza el ResultadoIA."""
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

        prompt = (
            "Eres un sistema experto en detección avícola de granja. "
            "Analiza ÚNICAMENTE si la imagen es de un entorno de granja o corral con aves de corral. "
            "Si la imagen NO contiene un entorno avícola (granja, corral, gallinero, nido), retorna todos los conteos en 0. "
            "\n\n"
            "DETECTA SOLO estas 4 categorías exactas:\n"
            "1. POLLITO: cría de gallina de pocos días/semanas de vida. Tiene cuerpo redondeado pequeño, "
            "pico corto, patas delgadas, plumón suave (puede ser amarillo, marrón o blanco). "
            "NUNCA confundir con pajaritos silvestres, canarios, loros, ni ningún ave que no sea cría de gallina.\n"
            "2. GALLINA: ave doméstica adulta hembra. Tiene cresta roja pequeña, cuerpo robusto, plumaje denso. "
            "NUNCA confundir con patos, pavos ni otras aves.\n"
            "3. GALLO: ave doméstica adulta macho. Tiene cresta y barbilla rojas mucho más grandes y llamativas que la gallina, "
            "plumas largas y coloridas en la cola, postura erguida y espolones prominentes.\n"
            "4. HUEVO: huevo oval de gallina en entorno de granja.\n"
            "\n"
            "Si ves aves que NO son claramente de la especie Gallus gallus domesticus, NO las cuentes. "
            "Responde SOLO con JSON válido sin markdown con este formato:\n"
            "{\"conteo_pollitos\": 0, \"conteo_gallinas\": 0, \"conteo_gallos\": 0, \"conteo_huevos\": 0, "
            "\"confianza\": \"alta|media|baja\", \"precision_estimada\": 0.0, "
            "\"notas\": \"descripcion breve\", "
            "\"detecciones\": [{\"x\": 0.5, \"y\": 0.5, \"label\": \"pollito|gallina|gallo|huevo\", \"confidence\": 0.8}]}"
        )

        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{
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
            }],
            max_tokens=1200,
        )

        texto = response.choices[0].message.content.strip()
        datos = _extraer_json(texto)

        conteo_pollitos = int(datos.get("conteo_pollitos", 0) or 0)
        conteo_gallinas = int(datos.get("conteo_gallinas", 0) or 0)
        conteo_gallos = int(datos.get("conteo_gallos", 0) or 0)
        conteo_huevos = int(datos.get("conteo_huevos", 0) or 0)
        confianza = _normalizar_confianza(datos.get("confianza"))

        precision = datos.get("precision_estimada")
        try:
            precision_float = float(precision)
        except (TypeError, ValueError):
            precision_float = _precision_desde_confianza(confianza)
        precision_float = max(0.0, min(1.0, precision_float))

        detecciones = _limpiar_detecciones(datos.get("detecciones"))

        notas_extra = json.dumps({
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