"""
Servicio de gestión de imágenes con Cloudinary.
"""
import cloudinary
import cloudinary.uploader
import hashlib
import os
import uuid
from typing import Optional, List
from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ..models.imagenes import Imagen, ResultadoIA

# ---------------------------------------------------------------------------
# Configuración Cloudinary
# ---------------------------------------------------------------------------
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# ---------------------------------------------------------------------------
# Configuración validación
# ---------------------------------------------------------------------------
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------
def _get_file_extension(filename: str) -> str:
    _, ext = os.path.splitext(filename)
    return ext.lower()


def _validate_file(file: UploadFile, file_size: int) -> None:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no permitido: {file.content_type}."
        )
    ext = _get_file_extension(file.filename or "")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extensión no permitida: {ext}."
        )
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="El archivo excede el tamaño máximo permitido (10 MB)."
        )


def _compute_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _generate_unique_name(original_filename: str) -> str:
    ext = _get_file_extension(original_filename)
    return f"{uuid.uuid4().hex}{ext}"


# ---------------------------------------------------------------------------
# Operaciones CRUD
# ---------------------------------------------------------------------------
async def upload_imagen(
    db: Session,
    file: UploadFile,
    usuario_id: int,
) -> Imagen:
    print(f"📥 [UPLOAD] Recibiendo: {file.filename} de usuario ID: {usuario_id}")

    # 1. Leer contenido
    content = await file.read()
    file_size = len(content)

    # 2. Validar
    _validate_file(file, file_size)

    # 3. Calcular hash
    file_hash = _compute_hash(content)

    # 4. Verificar duplicado
    existing = db.query(Imagen).filter(Imagen.hash_archivo == file_hash).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Esta imagen ya fue subida (ID: {existing.id})."
        )

    # 5. Subir a Cloudinary
    try:
        nombre_publico = f"pio-ai/imagenes/{uuid.uuid4().hex}"
        result = cloudinary.uploader.upload(
            content,
            public_id=nombre_publico,
            resource_type="image"
        )
        cloudinary_url = result["secure_url"]
        print(f"✅ [CLOUDINARY] Imagen subida: {cloudinary_url}")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al subir imagen a Cloudinary: {str(e)}"
        )

    # 6. Registrar en BD
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
        )
        db.add(db_imagen)
        db.flush()

        # 7. Crear resultado IA en estado pendiente
        db_resultado = ResultadoIA(
            imagen_id=db_imagen.id,
            estado="pendiente",
        )
        db.add(db_resultado)
        db.commit()
        db.refresh(db_imagen)
        print(f"✅ [UPLOAD] Imagen registrada en BD (ID: {db_imagen.id})")

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar en BD: {str(e)}"
        )

    # 8. Analizar con IA automáticamente (fuera del bloque de BD para no afectar la subida)
    print(f"🤖 [IA] Iniciando análisis para imagen ID: {db_imagen.id}...")
    try:
        from .ia_service import analizar_imagen_con_ia
        analizar_imagen_con_ia(db=db, imagen_id=db_imagen.id)
        print(f"✅ [IA] Análisis completado para imagen ID: {db_imagen.id}")
    except Exception as e:
        print(f"❌ [IA ERROR] Error en análisis: {e}")

    return db_imagen


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

    # Eliminar de Cloudinary
    try:
        public_id = db_imagen.ruta.split("/upload/")[1].split(".")[0]
        cloudinary.uploader.destroy(public_id)
    except Exception:
        pass

    db.delete(db_imagen)
    db.commit()
    return True

def cleanup_temp_files(max_age_hours: int = 24) -> int:
    # En Cloudinary no hay archivos temporales locales
    return 0