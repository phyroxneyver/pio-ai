"""
Servicio de gestión de imágenes con Cloudinary.
"""
import hashlib
import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional

import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ..models.imagenes import Imagen, ResultadoIA


load_dotenv(override=True)


def _env_required(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(f"Falta la variable de entorno: {name}")

    return value.strip()


cloudinary.config(
    cloud_name=_env_required("CLOUDINARY_CLOUD_NAME"),
    api_key=_env_required("CLOUDINARY_API_KEY"),
    api_secret=_env_required("CLOUDINARY_API_SECRET"),
    secure=True,
)


ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


def _get_file_extension(filename: str) -> str:
    _, ext = os.path.splitext(filename)
    return ext.lower()


def _validate_file(file: UploadFile, file_size: int) -> None:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no permitido: {file.content_type}.",
        )

    ext = _get_file_extension(file.filename or "")

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extensión no permitida: {ext}.",
        )

    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="El archivo excede el tamaño máximo permitido (10 MB).",
        )


def _compute_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _generate_unique_name(original_filename: str) -> str:
    ext = _get_file_extension(original_filename)

    if not ext:
        ext = ".jpg"

    return f"{uuid.uuid4().hex}{ext}"


async def upload_imagen(db: Session, file: UploadFile, usuario_id: int) -> Imagen:
    print(f"📥 [UPLOAD] Recibiendo: {file.filename} de usuario ID: {usuario_id}")

    content = await file.read()
    file_size = len(content)

    _validate_file(file, file_size)

    file_hash = _compute_hash(content)

    existing = db.query(Imagen).filter(Imagen.hash_archivo == file_hash).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Esta imagen ya fue subida (ID: {existing.id}). Toma una nueva foto o limpia la captura.",
        )

    try:
        nombre_publico = f"pio-ai/imagenes/{uuid.uuid4().hex}"

        result = cloudinary.uploader.upload(
            content,
            public_id=nombre_publico,
            resource_type="image",
        )

        cloudinary_url = result["secure_url"]

        print(f"✅ [CLOUDINARY] Imagen subida: {cloudinary_url}")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al subir imagen a Cloudinary: {str(e)}",
        )

    try:
        nombre_almacenado = _generate_unique_name(file.filename or "image.jpg")

        db_imagen = Imagen(
            nombre_original=file.filename or "unknown",
            nombre_almacenado=nombre_almacenado,
            ruta=cloudinary_url,
            content_type=file.content_type or "image/jpeg",
            tamaño_bytes=file_size,
            hash_archivo=file_hash,
            usuario_id=usuario_id,
            created_at=datetime.now(timezone.utc),
        )

        db.add(db_imagen)
        db.flush()

        db_resultado = ResultadoIA(
            imagen_id=db_imagen.id,
            estado="pendiente",
        )

        db.add(db_resultado)
        db.commit()
        db.refresh(db_imagen)

        print(f"✅ [UPLOAD] Imagen registrada en BD (ID: {db_imagen.id})")

        return db_imagen

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar en BD: {str(e)}",
        )


def get_imagenes(
    db: Session,
    usuario_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[List[Imagen], int]:
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