try:
    from app.main import app
except Exception as e:
    import traceback
    from fastapi import FastAPI
    app = FastAPI()
    
    error_detail = traceback.format_exc()
    
    @app.get("/{path:path}")
    def catch_all(path: str):
        return {"error": str(e), "traceback": error_detail}
