from fastapi import APIRouter
from app.core.database import DATABASE_URL

router = APIRouter()

@router.get("/debug-db")
def debug_db():
    return {"db_url_prefix": DATABASE_URL[:15] if DATABASE_URL else None}
