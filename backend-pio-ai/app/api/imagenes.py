@router.post("/{imagen_id}/analizar")
def analizar_imagen(imagen_id: int, db: Session = Depends(get_db), 
                    current_user: User = Depends(get_current_active_user)):
    from ..services.ia_service import analizar_imagen_con_ia
    resultado = analizar_imagen_con_ia(db=db, imagen_id=imagen_id)
    return resultado

