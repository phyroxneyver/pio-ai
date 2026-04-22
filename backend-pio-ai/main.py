import sys
import os

sys.path.append(os.path.dirname(__file__))

app = None
handler = None

try:
    from app.main import app
    handler = app
except Exception as e:
    import traceback
    err_trace = traceback.format_exc()
    from fastapi import FastAPI
    app = FastAPI()
    handler = app
    
    @app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
    def catch_all(path_name: str):
        return {"error": "Import Error", "traceback": err_trace}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
