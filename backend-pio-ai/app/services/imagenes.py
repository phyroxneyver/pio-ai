"""
Servicio de gestión de imágenes.

Responsabilidades:
- Validar tipo de archivo (jpg/png)
- Generar nombre único (UUID + extensión)
- Calcular hash SHA-256 para evitar duplicados
- Guardar archivo en disco
- Registrar metadatos en base de datos
- Crear registro de ResultadoIA en estado 'pendiente'
- Limpieza de archivos temporales
"""
import hashlib
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ..models.imagenes import Imagen, ResultadoIA

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
# Tipos MIME permitidos
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}
# Extensiones permitidas
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
# Tamaño máximo: 10 MB
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
# Directorio base de almacenamiento
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads/imagenes"))


# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------
def _get_file_extension(filename: str) -> str:
    """Extrae la extensión del archivo en minúsculas."""
    _, ext = os.path.splitext(filename)
    return ext.lower()


def _validate_file(file: UploadFile, file_size: int) -> None:
    """
    Valida tipo MIME, extensión y tamaño del archivo.
    Lanza HTTPException si no cumple.
    """
    # Validar content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Tipo de archivo no permitido: {file.content_type}. "
                f"Solo se aceptan: {', '.join(ALLOWED_CONTENT_TYPES)}"
            ),
        )

    # Validar extensión
    ext = _get_file_extension(file.filename or "")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Extensión no permitida: {ext}. "
                f"Solo se aceptan: {', '.join(ALLOWED_EXTENSIONS)}"
            ),
        )

    # Validar tamaño
    if file_size > MAX_FILE_SIZE_BYTES:
        max_mb = MAX_FILE_SIZE_BYTES / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo excede el tamaño máximo permitido ({max_mb:.0f} MB).",
        )


def _compute_hash(content: bytes) -> str:
    """Calcula el hash SHA-256 del contenido del archivo."""
    return hashlib.sha256(content).hexdigest()


def _generate_unique_name(original_filename: str) -> str:
    """Genera un nombre único con UUID4 conservando la extensión original."""
    ext = _get_file_extension(original_filename)
    return f"{uuid.uuid4().hex}{ext}"


def _ensure_upload_dir() -> Path:
    """Crea el directorio de uploads si no existe y retorna su path."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOAD_DIR


# ---------------------------------------------------------------------------
# Operaciones CRUD
# ---------------------------------------------------------------------------
async def upload_imagen(
    db: Session,
    file: UploadFile,
    usuario_id: int,
) -> Imagen:
    """
    Sube una imagen al sistema.

    Flujo:
    1. Lee el contenido completo del archivo
    2. Valida tipo, extensión y tamaño
    3. Calcula hash SHA-256
    4. Verifica duplicados (mismo hash)
    5. Genera nombre único y guarda en disco
    6. Registra metadatos en BD
    7. Crea ResultadoIA en estado 'pendiente'
    """
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
            detail=(
                f"Esta imagen ya fue subida anteriormente "
                f"(ID: {existing.id}, archivo: {existing.nombre_original})."
            ),
        )

    # 5. Generar nombre único y guardar en disco
    upload_dir = _ensure_upload_dir()
    nombre_almacenado = _generate_unique_name(file.filename or "image.jpg")
    ruta_archivo = upload_dir / nombre_almacenado

    try:
        with open(ruta_archivo, "wb") as buffer:
            buffer.write(content)
    except OSError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar el archivo en disco: {str(e)}",
        )

    # 6. Registrar en BD
    try:
        db_imagen = Imagen(
            nombre_original=file.filename or "unknown",
            nombre_almacenado=nombre_almacenado,
            ruta=str(ruta_archivo),
            content_type=file.content_type or "image/jpeg",
            tamaño_bytes=file_size,
            hash_archivo=file_hash,
            usuario_id=usuario_id,
        )
        db.add(db_imagen)
        db.flush()  # Obtener el ID antes del commit

        # 7. Crear resultado IA en estado 'pendiente'
        db_resultado = ResultadoIA(
            imagen_id=db_imagen.id,
            estado="pendiente",
        )
        db.add(db_resultado)
        db.commit()
        db.refresh(db_imagen)

        return db_imagen

    except Exception as e:
        db.rollback()
        # Limpiar archivo del disco si falla la BD
        if ruta_archivo.exists():
            ruta_archivo.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar la imagen en la base de datos: {str(e)}",
        )


def get_imagenes(
    db: Session,
    usuario_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[List[Imagen], int]:
    """
    Lista imágenes con paginación.
    Si se proporciona usuario_id, filtra por usuario.
    Retorna (lista_imagenes, total).
    """
    query = db.query(Imagen)
    if usuario_id is not None:
        query = query.filter(Imagen.usuario_id == usuario_id)

    total = query.count()
    imagenes = (
        query.order_by(Imagen.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return imagenes, total


def get_imagen_by_id(db: Session, imagen_id: int) -> Optional[Imagen]:
    """Obtiene una imagen por su ID."""
    return db.query(Imagen).filter(Imagen.id == imagen_id).first()


def delete_imagen(db: Session, imagen_id: int) -> bool:
    """
    Elimina una imagen de la BD y del disco.
    Retorna True si se eliminó, False si no existía.
    """
    db_imagen = db.query(Imagen).filter(Imagen.id == imagen_id).first()
    if not db_imagen:
        return False

    # Eliminar archivo del disco
    ruta = Path(db_imagen.ruta)
    if ruta.exists():
        try:
            ruta.unlink()
        except OSError:
            pass  # Log en producción, no bloquear eliminación de BD

    # Eliminar de BD (cascade elimina ResultadoIA)
    db.delete(db_imagen)
    db.commit()
    return True


def cleanup_temp_files(max_age_hours: int = 24) -> int:
    """
    Limpieza automática de archivos huérfanos en el directorio de uploads.
    Elimina archivos que no tienen registro en BD y son más antiguos que max_age_hours.
    Retorna el número de archivos eliminados.
    """
    upload_dir = UPLOAD_DIR
    if not upload_dir.exists():
        return 0

    from ..core.database import SessionLocal

    db = SessionLocal()
    removed = 0

    try:
        cutoff = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)

        for archivo in upload_dir.iterdir():
            if not archivo.is_file():
                continue

            # Solo procesar archivos más antiguos que el cutoff
            if archivo.stat().st_mtime > cutoff:
                continue

            # Verificar si existe en BD
            exists_in_db = (
                db.query(Imagen)
                .filter(Imagen.nombre_almacenado == archivo.name)
                .first()
            )

            if not exists_in_db:
                try:
                    archivo.unlink()
                    removed += 1
                except OSError:
                    pass
    finally:
        db.close()

    return removed
