import anthropic
import base64
import re
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ..models.imagenes import Imagen, ResultadoIA

client = anthropic.Anthropic() 

def analizar_imagen_con_ia(db: Session, imagen_id: int) -> ResultadoIA:
    """Analiza una imagen con Claude Vision y actualiza el ResultadoIA."""
    
    imagen = db.query(Imagen).filter(Imagen.id == imagen_id).first()
    resultado = db.query(ResultadoIA).filter(ResultadoIA.imagen_id == imagen_id).first()
    
    if not imagen or not resultado:
        raise ValueError("Imagen o ResultadoIA no encontrado")
    
   
    resultado.estado = "procesando"
    db.commit()
    
    try:
        # Leer imagen del disco
        ruta = Path(imagen.ruta)
        image_data = base64.standard_b64encode(ruta.read_bytes()).decode("utf-8")
        media_type = imagen.content_type  # "image/jpeg" o "image/png"
        
        # Llamar a Claude Vision
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=256,
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
                            "Cuenta cuántos pollitos (polluelos de pollo) hay en esta imagen. "
                            "Responde SOLO con este formato JSON: "
                            '{"conteo": <número>, "confianza": "alta|media|baja", "notas": "<observación breve>"}'
                        )
                    }
                ],
            }]
        )
        
        import json
        texto = response.content[0].text.strip()
        datos = json.loads(texto)
        
        resultado.conteo_pollitos = datos.get("conteo", 0)
        resultado.confianza = datos.get("confianza", "baja")
        resultado.estado = "completado"
        resultado.procesado_at = datetime.now(timezone.utc)
        
    except Exception as e:
        resultado.estado = "error"
        resultado.error_detalle = str(e)
    
    db.commit()
    db.refresh(resultado)
    return resultado