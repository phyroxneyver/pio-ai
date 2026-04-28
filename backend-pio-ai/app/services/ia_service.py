import base64
import httpx
import json
import os
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ..models.imagenes import Imagen, ResultadoIA


def analizar_imagen_con_ia(db: Session, imagen_id: int) -> ResultadoIA:
    """Analiza una imagen con Gemini Vision y actualiza el ResultadoIA."""
    import google.generativeai as genai

    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    imagen = db.query(Imagen).filter(Imagen.id == imagen_id).first()
    resultado = db.query(ResultadoIA).filter(ResultadoIA.imagen_id == imagen_id).first()

    if not imagen or not resultado:
        raise ValueError("Imagen o ResultadoIA no encontrado")

    resultado.estado = "procesando"
    db.commit()

    try:
        response_img = httpx.get(imagen.ruta, timeout=10.0)
        response_img.raise_for_status()

        model = genai.GenerativeModel("gemini-1.5-flash")

        image_part = {
            "mime_type": imagen.content_type,
            "data": base64.standard_b64encode(response_img.content).decode("utf-8"),
        }

        response = model.generate_content([
            image_part,
            (
                "Cuenta cuántos pollitos (polluelos de pollo) hay en esta imagen. "
                "Responde SOLO con este formato JSON sin markdown: "
                '{"conteo": <número>, "confianza": "alta|media|baja", "notas": "<observación breve>"}'
            ),
        ])

        texto = response.text.strip()
        if "```" in texto:
            texto = texto.split("```")[1].split("```")[0].replace("json", "").strip()

        datos = json.loads(texto)

        resultado.conteo_pollitos = int(datos.get("conteo", 0))
        resultado.confianza = datos.get("confianza", "baja")
        resultado.estado = "completado"
        resultado.procesado_at = datetime.now(timezone.utc)

    except Exception as e:
        resultado.estado = "error"
        resultado.error_detalle = str(e)

    db.commit()
    db.refresh(resultado)
    return resultado