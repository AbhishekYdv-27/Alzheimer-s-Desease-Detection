"""Start the FastAPI backend from the project root with: python run_backend.py"""
import uvicorn
from backend.app.core.config import settings


if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )
