from contextlib import asynccontextmanager
import logging
import time
from urllib.parse import urlsplit
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from backend.app.core.auth import get_current_user

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
from backend.app.ml.models.checkpoint_provisioning import provision_model_checkpoint

logger = logging.getLogger("alzheimers.api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    app.state.model_registry = ModelRegistry()
    checkpoint_status = provision_model_checkpoint()
    if checkpoint_status.available:
        logger.info("Model checkpoint status: %s", checkpoint_status.code)
    else:
        logger.warning(
            "Model checkpoint unavailable (%s); inference endpoints will report unavailable",
            checkpoint_status.code,
        )
    logger.info("Application started with SQLite persistence configured")
    yield
    logger.info("Application shutdown")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-assisted platform for Alzheimer's Disease detection and clinical decision support.",
    debug=settings.debug,
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

cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
if settings.app_env.strip().lower() in {"production", "prod"}:
    if not cors_origins or any(
        origin == "*"
        or urlsplit(origin).scheme != "https"
        or not urlsplit(origin).netloc
        or urlsplit(origin).path not in {"", "/"}
        for origin in cors_origins
    ):
        raise RuntimeError("Production CORS_ORIGINS must contain explicit HTTPS origins only")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(index_router, tags=["index"])
app.include_router(health_router, prefix="/api/health", tags=["health"])
app.include_router(auth_router, tags=["auth"])
app.include_router(models_router, tags=["models"])
app.include_router(prediction_router, tags=["prediction"])
app.include_router(analysis_router, tags=["analysis"])
app.include_router(reports_router, tags=["reports"])
app.include_router(portal_router, tags=["patient-doctor-portal"])

results_dir = Path(__file__).resolve().parent.parent / "results" / "gradcam"


@app.get("/api/results/gradcam/{filename}", include_in_schema=False)
def get_gradcam_result(filename: str, user: dict = Depends(get_current_user)):
    if Path(filename).name != filename or not filename.startswith(f"{user['id']}_"):
        raise HTTPException(status_code=404, detail="Result not found")
    result_path = (results_dir / filename).resolve()
    if result_path.parent != results_dir.resolve() or not result_path.is_file():
        raise HTTPException(status_code=404, detail="Result not found")
    return FileResponse(
        result_path,
        media_type="image/png",
        headers={"Cache-Control": "private, no-store"},
    )
