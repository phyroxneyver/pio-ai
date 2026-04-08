from sqlalchemy.orm import Session
from app.models.aves import Ave, ProduccionHuevos
from app.schemas.aves import AveCreate, ProduccionCreate


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


def get_aves(db: Session) -> list[Ave]:
    return db.query(Ave).all()


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


def get_producciones(db: Session) -> list[ProduccionHuevos]:
    return db.query(ProduccionHuevos).all()