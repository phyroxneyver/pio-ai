import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session
import io
from starlette.datastructures import Headers
from app.models.imagenes import Imagen, ResultadoIA
from app.models.users import User
from app.services.imagenes import (
    _get_file_extension,
    _validate_file,
    _compute_hash,
    _generate_unique_name,
    upload_imagen,
    get_imagenes,
    get_imagen_by_id,
    delete_imagen
)

def test_file_validation_helpers():
    assert _get_file_extension("test.PNG") == ".png"
    assert _get_file_extension("no_ext") == ""
    
    # Hash check
    assert len(_compute_hash(b"hello world")) == 64
    
    # Generate unique name
    name = _generate_unique_name("photo.heic")
    assert name.endswith(".jpg")
    
    # Validate file exceptions
    mock_file = MagicMock(spec=UploadFile)
    mock_file.content_type = "image/gif"
    mock_file.filename = "test.gif"
    
    with pytest.raises(HTTPException) as exc_info:
        _validate_file(mock_file, 500)
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

@patch("app.services.imagenes._verificar_calidad")
@patch("app.services.imagenes.cloudinary.uploader.upload")
@patch("app.services.ia_service.analizar_imagen_con_ia")
@pytest.mark.asyncio
async def test_upload_imagen_service(mock_analizar, mock_upload, mock_quality, db_session: Session):
    # 1. Configurar mocks
    mock_quality.return_value = None
    mock_upload.return_value = {"secure_url": "https://res.cloudinary.com/pio-ai/test.jpg"}
    mock_analizar.return_value = MagicMock(spec=ResultadoIA, conteo_pollitos=3, notas_ia='{"conteo_gallinas": 1}')
    
    # 2. Configurar usuario
    user = User(email="img_test@test.com", hashed_password="pw", role="usuario")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # 3. Simular archivo (Pasando el content-type correctamente a través de Headers)
    file_content = b"fake_jpg_bytes_that_are_valid"
    upload_file = UploadFile(
        file=io.BytesIO(file_content),
        filename="chickens.jpg",
        size=len(file_content),
        headers=Headers({"content-type": "image/jpeg"})  # <-- Solución aquí
    )
    
    # 4. Ejecutar upload
    imagen = await upload_imagen(db=db_session, file=upload_file, usuario_id=user.id)
    
    # 5. Aseveraciones
    assert imagen.id is not None
    assert imagen.nombre_original == "chickens.jpg"
    assert imagen.ruta == "https://res.cloudinary.com/pio-ai/test.jpg"
    assert imagen.usuario_id == user.id
    
    # Verificar que se creó el resultado IA pendiente en BD
    res = db_session.query(ResultadoIA).filter(ResultadoIA.imagen_id == imagen.id).first()
    assert res is not None

@patch("app.services.imagenes._verificar_calidad")
@patch("app.services.imagenes.cloudinary.uploader.upload")
@pytest.mark.asyncio
async def test_upload_imagen_duplicate_hash(mock_upload, mock_quality, db_session: Session):
    mock_quality.return_value = None
    mock_upload.return_value = {"secure_url": "https://res.cloudinary.com/pio-ai/test.jpg"}
    
    user = User(email="img_test_dup@test.com", hashed_password="pw", role="usuario")
    db_session.add(user)
    db_session.commit()
    
    file_hash = _compute_hash(b"duplicate_content")
    prev_img = Imagen(
        nombre_original="prev.jpg",
        nombre_almacenado="prev_stored.jpg",
        ruta="http://cloudinary/prev.jpg",
        content_type="image/jpeg",
        tamaño_bytes=100,
        hash_archivo=file_hash,
        usuario_id=user.id
    )
    db_session.add(prev_img)
    db_session.commit()
    
    upload_file = UploadFile(
        file=io.BytesIO(b"duplicate_content"),
        filename="new.jpg",
        size=17,
        headers=Headers({"content-type": "image/jpeg"})
    )
    
    with pytest.raises(HTTPException) as exc_info:
        await upload_imagen(db=db_session, file=upload_file, usuario_id=user.id)
    assert exc_info.value.status_code == status.HTTP_409_CONFLICT

def test_get_imagenes_service(db_session: Session):
    user = User(email="img_list@test.com", hashed_password="pw", role="usuario")
    db_session.add(user)
    db_session.commit()
    
    for i in range(3):
        img = Imagen(
            nombre_original=f"img_{i}.jpg",
            nombre_almacenado=f"img_{i}_stored.jpg",
            ruta=f"http://cloudinary/img_{i}.jpg",
            content_type="image/jpeg",
            tamaño_bytes=100,
            hash_archivo=f"hash_{i}",
            usuario_id=user.id
        )
        db_session.add(img)
    db_session.commit()
    
    imgs, total = get_imagenes(db_session, usuario_id=user.id)
    assert total == 3
    assert len(imgs) == 3

@patch("app.services.imagenes.cloudinary.uploader.destroy")
def test_delete_imagen_service(mock_destroy, db_session: Session):
    mock_destroy.return_value = {"result": "ok"}
    
    user = User(email="img_del@test.com", hashed_password="pw", role="usuario")
    db_session.add(user)
    db_session.commit()
    
    img = Imagen(
        nombre_original="del.jpg",
        nombre_almacenado="del_stored.jpg",
        ruta="http://cloudinary/pio-ai/upload/v12345/del.jpg",
        content_type="image/jpeg",
        tamaño_bytes=100,
        hash_archivo="del_hash",
        usuario_id=user.id
    )
    db_session.add(img)
    db_session.commit()
    
    success = delete_imagen(db_session, img.id)
    assert success is True
    
    deleted = get_imagen_by_id(db_session, img.id)
    assert deleted is None
    mock_destroy.assert_called_once()