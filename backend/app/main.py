from contextlib import asynccontextmanager
import logging
import time
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.models import router as models_router
from backend.app.api.routes.prediction import router as prediction_router
from backend.app.api.routes.index import router as index_router
from backend.app.api.routes.auth import router as auth_router
from backend.app.api.routes.analysis import router as analysis_router
from backend.app.api.routes.reports import router as reports_router
from backend.app.api.routes.portal import router as portal_router
from backend.app.core.database import init_db
from backend.app.ml.registry import ModelRegistry
from backend.app.core.config import settings

logger = logging.getLogger("alzheimers.api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    app.state.model_registry = ModelRegistry()
    logger.info("Application started with database %s", settings.database_url.split("://", 1)[0])
    yield
    logger.info("Application shutdown")


app = FastAPI(
    title="Alzheimer's Disease Detection & AI-Assisted Clinical Decision Support Platform",
    version="0.1.0",
    description="AI-assisted platform for Alzheimer's Disease detection and clinical decision support.",
    lifespan=lifespan,
)


@app.middleware("http")
async def request_logging(request, call_next):
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled error for %s %s", request.method, request.url.path)
        raise
    elapsed_ms = (time.perf_counter() - started) * 1000
    if response.status_code >= 500:
        logger.error("Server error %s %s -> %s (%.1fms)", request.method, request.url.path, response.status_code, elapsed_ms)
    else:
        logger.info("%s %s -> %s (%.1fms)", request.method, request.url.path, response.status_code, elapsed_ms)
    return response

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(index_router, tags=["index"])
app.include_router(health_router, prefix="/api/health", tags=["health"])
app.include_router(auth_router, tags=["auth"])
app.include_router(models_router, tags=["models"])
app.include_router(prediction_router, tags=["prediction"])
app.include_router(analysis_router, tags=["analysis"])
app.include_router(reports_router, tags=["reports"])
app.include_router(portal_router, tags=["patient-doctor-portal"])

results_dir = Path(__file__).resolve().parent.parent / "results"
app.mount("/api/results", StaticFiles(directory=str(results_dir)), name="results")


@app.get("/")
def root():
    return {"message": "Alzheimer's AI Platform API"}


@app.get("/health")
def health():
    return {"status": "healthy", "service": "alzheimers-ai-platform"}
