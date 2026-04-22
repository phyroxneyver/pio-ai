import anthropic
import base64
import gc
import httpx
import json
import numpy as np
from datetime import datetime, timezone
from io import BytesIO
from PIL import Image
from sqlalchemy.orm import Session

from ..models.imagenes import Imagen, ResultadoIA

client = anthropic.Anthropic()
TARGET_SIZE = (640, 640)


def _descargar_imagen(url: str) -> bytes:
    response = httpx.get(url, timeout=15.0)
    response.raise_for_status()
    content = response.content
    del response
    return content


def _preprocesar_imagen(content: bytes) -> tuple[str, str]:
    img = Image.open(BytesIO(content)).convert("RGB")
    img_resized = img.resize(TARGET_SIZE, Image.LANCZOS)
    tensor = np.array(img_resized, dtype=np.float32) / 255.0
    img_final = Image.fromarray((tensor * 255).astype(np.uint8))
    buffer = BytesIO()
    img_final.save(buffer, format="PNG")
    buffer.seek(0)
    encoded = base64.standard_b64encode(buffer.read()).decode("utf-8")
    del img, img_resized, tensor, img_final, buffer
    gc.collect()
    return encoded, "image/png"


def analizar_imagen_con_ia(db: Session, imagen_id: int) -> ResultadoIA:
    imagen = db.query(Imagen).filter(Imagen.id == imagen_id).first()
    resultado = db.query(ResultadoIA).filter(ResultadoIA.imagen_id == imagen_id).first()

    if not imagen or not resultado:
        raise ValueError("Imagen o ResultadoIA no encontrado")

    resultado.estado = "procesando"
    db.commit()

    content_raw = None

    try:
        content_raw = _descargar_imagen(imagen.ruta)
        image_data, media_type = _preprocesar_imagen(content_raw)

        del content_raw
        content_raw = None
        gc.collect()

        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "Analiza esta imagen de pollitos (polluelos de pollo). "
                            "Cuenta cuántos pollitos hay y estima la posición de cada uno "
                            "como porcentaje del ancho (x) y alto (y) de la imagen, "
                            "donde 0.0 es el borde izquierdo/superior y 1.0 es el derecho/inferior. "
                            "Responde ÚNICAMENTE con este JSON sin texto adicional ni backticks: "
                            '{"conteo": <número entero>, '
                            '"confianza": "alta|media|baja", '
                            '"notas": "<observación breve>", '
                            '"coordenadas": [{"x": 0.45, "y": 0.30}, ...]}'
                        )
                    }
                ],
            }]
        )

        texto = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
        datos = json.loads(texto)
        coordenadas = datos.get("coordenadas", [])

        resultado.conteo_pollitos = datos.get("conteo", 0)
        resultado.confianza = datos.get("confianza", "baja")
        resultado.coordenadas = json.dumps(coordenadas)
        resultado.estado = "completado"
        resultado.procesado_at = datetime.now(timezone.utc)

        del image_data, response, datos, coordenadas
        gc.collect()

    except json.JSONDecodeError as e:
        resultado.estado = "error"
        resultado.error_detalle = f"Error parseando respuesta IA: {str(e)}"
    except Exception as e:
        resultado.estado = "error"
        resultado.error_detalle = str(e)
    finally:
        if content_raw is not None:
            del content_raw
            gc.collect()

    db.commit()
    db.refresh(resultado)
    return resultado