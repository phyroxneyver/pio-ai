from typing import List, Optional
from sqlalchemy.orm import Session
from ..models.aves import Ave, ProduccionHuevos
from ..schemas.aves import AveCreate, AveUpdate, ProduccionCreate, ProduccionUpdate




def create_ave(db: Session, ave: AveCreate) -> Ave:
    db_ave = Ave(
        tipo=ave.tipo,
        cantidad=ave.cantidad,
        raza=ave.raza,
        notas=ave.notas,
    )
    db.add(db_ave)
    db.commit()
    db.refresh(db_ave)
    return db_ave


def get_aves(db: Session) -> List[Ave]:
    return db.query(Ave).all()


def update_ave(db: Session, ave_id: int, datos: AveUpdate) -> Optional[Ave]:
    db_ave = db.query(Ave).filter(Ave.id == ave_id).first()
    if not db_ave:
        return None
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(db_ave, campo, valor)
    db.commit()
    db.refresh(db_ave)
    return db_ave




def create_produccion(db: Session, produccion: ProduccionCreate) -> ProduccionHuevos:
    db_produccion = ProduccionHuevos(
        ave_id=produccion.ave_id,
        cantidad_huevos=produccion.cantidad_huevos,
        notas=produccion.notas,
    )
    db.add(db_produccion)
    db.commit()
    db.refresh(db_produccion)
    return db_produccion


def get_producciones(db: Session) -> List[ProduccionHuevos]:
    return db.query(ProduccionHuevos).all()


def update_produccion(db: Session, produccion_id: int, datos: ProduccionUpdate) -> Optional[ProduccionHuevos]:
    db_prod = db.query(ProduccionHuevos).filter(ProduccionHuevos.id == produccion_id).first()
    if not db_prod:
        return None
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(db_prod, campo, valor)
    db.commit()
    db.refresh(db_prod)
    return db_prod