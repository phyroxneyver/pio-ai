import pytest
from sqlalchemy.orm import Session

from app.services.aves import (
    create_ave,
    get_aves,
    update_ave,
    create_produccion,
    get_producciones,
    update_produccion
)
from app.schemas.aves import (
    AveCreate,
    AveUpdate,
    ProduccionCreate,
    ProduccionUpdate
)
from app.models.aves import Ave, ProduccionHuevos

def test_ave_crud(db_session: Session):
    # 1. Crear Ave
    ave_in = AveCreate(tipo="gallina", cantidad=100, raza="Leghorn", notas="Lote A")
    ave = create_ave(db_session, ave_in)
    
    assert ave.id is not None
    assert ave.tipo == "gallina"
    assert ave.cantidad == 100
    assert ave.raza == "Leghorn"
    assert ave.notas == "Lote A"
    
    # 2. Listar Aves
    aves = get_aves(db_session)
    assert len(aves) == 1
    assert aves[0].id == ave.id
    
    # 3. Actualizar Ave
    datos_update = AveUpdate(cantidad=120, notas="Lote A - Actualizado")
    ave_updated = update_ave(db_session, ave.id, datos_update)
    
    assert ave_updated is not None
    assert ave_updated.cantidad == 120
    assert ave_updated.notas == "Lote A - Actualizado"
    assert ave_updated.tipo == "gallina"  # Se mantiene igual

def test_ave_update_not_found(db_session: Session):
    datos_update = AveUpdate(cantidad=50)
    result = update_ave(db_session, 999, datos_update)
    assert result is None

def test_produccion_crud(db_session: Session):
    # Crear ave primero
    ave_in = AveCreate(tipo="gallina", cantidad=50)
    ave = create_ave(db_session, ave_in)
    
    # 1. Crear Producción
    prod_in = ProduccionCreate(ave_id=ave.id, cantidad_huevos=35, notas="Mañana")
    prod = create_produccion(db_session, prod_in)
    
    assert prod.id is not None
    assert prod.ave_id == ave.id
    assert prod.cantidad_huevos == 35
    assert prod.notas == "Mañana"
    
    # 2. Listar Producción
    prods = get_producciones(db_session)
    assert len(prods) == 1
    assert prods[0].id == prod.id
    
    # 3. Actualizar Producción
    datos_update = ProduccionUpdate(cantidad_huevos=40, notas="Corregido tarde")
    prod_updated = update_produccion(db_session, prod.id, datos_update)
    
    assert prod_updated is not None
    assert prod_updated.cantidad_huevos == 40
    assert prod_updated.notas == "Corregido tarde"

def test_produccion_update_not_found(db_session: Session):
    datos_update = ProduccionUpdate(cantidad_huevos=10)
    result = update_produccion(db_session, 999, datos_update)
    assert result is None
