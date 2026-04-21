import sys
import os

# Asegurar que el directorio de la app sea visible
sys.path.append(os.path.dirname(__file__))

from app.main import app

# Exportar 'app' para que Vercel lo encuentre
# Si Vercel busca 'handler' por defecto en algunos runtimes, lo asignamos:
handler = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
