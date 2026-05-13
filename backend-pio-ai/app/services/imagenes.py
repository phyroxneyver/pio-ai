import cloudinary
import cloudinary.uploader
import cv2
import hashlib
import numpy as np
import os
import uuid
from typing import Optional, List
from datetime import datetime, timezone
from io import BytesIO

from pillow_heif import register_heif_opener
register_heif_opener()

from PIL import Image
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ..models.imagenes import Imagen, ResultadoIA

cloudinary.config(
    cloudinary_url=os.getenv("CLOUDINARY_URL"),
    secure=True,
)

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/heic", "image/heif"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".heif"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
BRILLO_MINIMO = 40
NITIDEZ_MINIMA = 50.0


def _get_file_extension(filename: str) -> str:
    _, ext = os.path.splitext(filename)
    return ext.lower()


def _validate_file(file: UploadFile, file_size: int) -> None:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no permitido: {file.content_type}. Se acepta: JPG, PNG, HEIC."
        )
    ext = _get_file_extension(file.filename or "")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extensión no permitida: {ext}. Se acepta: .jpg, .png, .heic"
        )
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="El archivo excede el tamaño máximo permitido (10 MB)."
        )


def _verificar_calidad(content: bytes, filename: str) -> None:
    ext = _get_file_extension(filename)

    if ext in {".heic", ".heif"}:
        img_pil = Image.open(BytesIO(content)).convert("RGB")
        img_array = np.array(img_pil)
        img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    else:
        nparr = np.frombuffer(content, np.uint8)
        img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img_cv is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo leer la imagen. Verifica que el archivo no esté corrupto."
        )

    gris = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    brillo = float(gris.mean())
    if brillo < BRILLO_MINIMO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Imagen demasiado oscura (brillo: {brillo:.1f}/255). Toma la foto con mejor iluminación."
        )

    nitidez = float(cv2.Laplacian(gris, cv2.CV_64F).var())
    if nitidez < NITIDEZ_MINIMA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Imagen demasiado borrosa (nitidez: {nitidez:.1f}). Mantén el teléfono firme al tomar la foto."
        )


def _convertir_heic_a_jpg(content: bytes) -> bytes:
    img = Image.open(BytesIO(content)).convert("RGB")
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=95)
    buffer.seek(0)
    return buffer.read()


def _compute_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _generate_unique_name(original_filename: str) -> str:
    ext = _get_file_extension(original_filename)
    if ext in {".heic", ".heif"}:
        ext = ".jpg"
    return f"{uuid.uuid4().hex}{ext}"


async def upload_imagen(db: Session, file: UploadFile, usuario_id: int) -> Imagen:
    content = await file.read()
    file_size = len(content)

    _validate_file(file, file_size)
    _verificar_calidad(content, file.filename or "imagen.jpg")

    ext = _get_file_extension(file.filename or "")
    content_a_subir = content
    content_type_final = file.content_type or "image/jpeg"
    if ext in {".heic", ".heif"}:
        content_a_subir = _convertir_heic_a_jpg(content)
        content_type_final = "image/jpeg"

    file_hash = _compute_hash(content)

    existing = db.query(Imagen).filter(Imagen.hash_archivo == file_hash).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Esta imagen ya fue subida anteriormente (ID: {existing.id})."
        )

    try:
        nombre_publico = f"pio-ai/imagenes/{uuid.uuid4().hex}"
        result = cloudinary.uploader.upload(
            content_a_subir,
            public_id=nombre_publico,
            resource_type="image"
        )
        cloudinary_url = result["secure_url"]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al subir imagen a Cloudinary: {str(e)}"
        )

    try:
        nombre_almacenado = _generate_unique_name(file.filename or "image.jpg")
        db_imagen = Imagen(
            nombre_original=file.filename or "unknown",
            nombre_almacenado=nombre_almacenado,
            ruta=cloudinary_url,
            content_type=content_type_final,
            tamaño_bytes=file_size,
            hash_archivo=file_hash,
            usuario_id=usuario_id,
        )
        db.add(db_imagen)
        db.flush()

        db_resultado = ResultadoIA(imagen_id=db_imagen.id, estado="pendiente")
        db.add(db_resultado)
        db.commit()
        db.refresh(db_imagen)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar en BD: {str(e)}"
        )

    print(f"🤖 [IA] Iniciando análisis para imagen ID: {db_imagen.id}...")
    try:
        from .ia_service import analizar_imagen_con_ia
        res = analizar_imagen_con_ia(db=db, imagen_id=db_imagen.id)
        # Extraer conteos extras de las notas si es posible
        try:
            import json
            notas = json.loads(res.notas_ia or "{}")
            c_gallinas = notas.get("conteo_gallinas", 0)
            c_gallos = notas.get("conteo_gallos", 0)
            c_huevos = notas.get("conteo_huevos", 0)
        except Exception:
            c_gallinas = "?"
            c_gallos = "?"
            c_huevos = "?"
            
        print(f"✅ [IA] Análisis completado ID {db_imagen.id}: {res.conteo_pollitos} pollitos, {c_gallinas} gallinas, {c_gallos} gallos, {c_huevos} huevos.")
    except Exception as e:
        print(f"❌ [IA ERROR] Error en análisis: {e}")

    return db_imagen


def get_imagenes(db: Session, usuario_id: Optional[int] = None, skip: int = 0, limit: int = 50) -> tuple[List[Imagen], int]:
    query = db.query(Imagen)
    if usuario_id is not None:
        query = query.filter(Imagen.usuario_id == usuario_id)
    total = query.count()
    imagenes = query.order_by(Imagen.created_at.desc()).offset(skip).limit(limit).all()
    return imagenes, total


def get_imagen_by_id(db: Session, imagen_id: int) -> Optional[Imagen]:
    return db.query(Imagen).filter(Imagen.id == imagen_id).first()


def delete_imagen(db: Session, imagen_id: int) -> bool:
    db_imagen = db.query(Imagen).filter(Imagen.id == imagen_id).first()
    if not db_imagen:
        return False
    try:
        public_id = db_imagen.ruta.split("/upload/")[1].split(".")[0]
        cloudinary.uploader.destroy(public_id)
    except Exception:
        pass
    db.delete(db_imagen)
    db.commit()
    return True


def cleanup_temp_files(max_age_hours: int = 24) -> int:
    return 0