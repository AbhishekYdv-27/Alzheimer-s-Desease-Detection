from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
from pathlib import Path

router = APIRouter(prefix="/api/models", tags=["models"])

_registry = None

def get_registry():
    global _registry
    if _registry is None:
        from backend.app.ml.registry import ModelRegistry
        _registry = ModelRegistry()
    return _registry


class ModelStatusResponse(BaseModel):
    model_name: str
    model_version: str
    status: str
    message: str


class ModelInfo(BaseModel):
    model_name: str
    model_version: str
    architecture: str
    num_classes: int
    class_names: List[str]
    training_status: str
    model_path: Optional[str] = None
    experiment_id: Optional[str] = None
    metrics: Dict[str, Any] = {}


class ReadinessCheck(BaseModel):
    check: str
    passed: bool
    message: str


class ReadinessReport(BaseModel):
    model_name: str
    model_version: str
    ready: bool
    checks: List[ReadinessCheck]


@router.get("/", response_model=List[ModelInfo])
def list_models():
    registry = get_registry()
    models = registry.get_all_models()
    items = []
    for model in models:
        available, status, _ = registry.validate_model_file(
            model.model_name,
            model.model_version,
        )
        items.append(ModelInfo(
            model_name=model.model_name,
            model_version=model.model_version,
            architecture=model.architecture,
            num_classes=model.num_classes,
            class_names=model.class_names,
            training_status=model.training_status if available else status,
            model_path=None,
            experiment_id=model.experiment_id if model.experiment_id else None,
            metrics=model.metrics,
        ))
    return items


@router.get("/status")
def get_all_statuses():
    registry = get_registry()
    models = registry.get_all_models()
    from backend.app.ml.models.model_loader import check_model_ready

    statuses = []
    for model in models:
        ready, status, message = check_model_ready(model.model_name, model.model_version)
        statuses.append({
            "model_name": model.model_name,
            "model_version": model.model_version,
            "status": status,
            "available": ready,
            "message": message,
        })
    return {
        "models": statuses
    }


@router.get("/{model_name}", response_model=ModelInfo)
def get_model_info(model_name: str):
    registry = get_registry()
    meta = registry.get_model(model_name)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
    available, status, _ = registry.validate_model_file(meta.model_name, meta.model_version)
    return ModelInfo(
        model_name=meta.model_name,
        model_version=meta.model_version,
        architecture=meta.architecture,
        num_classes=meta.num_classes,
        class_names=meta.class_names,
        training_status=meta.training_status if available else status,
        model_path=None,
        experiment_id=meta.experiment_id if meta.experiment_id else None,
        metrics=meta.metrics
    )


@router.get("/{model_name}/status", response_model=ModelStatusResponse)
def get_model_status(model_name: str, model_version: str = "1.0"):
    from backend.app.ml.models.model_loader import check_model_ready
    ready, status, message = check_model_ready(model_name, model_version)
    return ModelStatusResponse(
        model_name=model_name,
        model_version=model_version,
        status=status,
        message=message
    )


@router.get("/{model_name}/readiness", response_model=ReadinessReport)
def get_model_readiness(model_name: str, model_version: str = "1.0"):
    from backend.app.ml.inference import create_prediction_readiness_report
    report = create_prediction_readiness_report(model_name, model_version)
    return ReadinessReport(**report)


@router.get("/compare/")
def compare_all_models():
    from backend.app.ml.evaluation import ComparisonResult, compare_models, format_comparison_table
    from backend.app.ml.registry import ModelStatus

    registry = get_registry()
    trained_models = registry.get_trained_models()

    if not trained_models:
        return {
            "status": "NO_TRAINED_MODELS",
            "message": "No trained models available for comparison",
            "comparison": None
        }

    comparisons = [
        ComparisonResult(
            model_name=m.model_name,
            model_version=m.model_version,
            experiment_id=m.experiment_id,
            training_status=m.training_status,
            accuracy=m.metrics.get("accuracy"),
            precision=m.metrics.get("precision"),
            recall=m.metrics.get("recall"),
            macro_f1=m.metrics.get("macro_f1"),
            weighted_f1=m.metrics.get("weighted_f1"),
            dataset_version=m.metrics.get("dataset_version", ""),
            created_date=m.updated_date
        )
        for m in trained_models
    ]

    sorted_comparisons = compare_models(comparisons)

    return {
        "status": "SUCCESS",
        "comparison": [
            {
                "model_name": c.model_name,
                "model_version": c.model_version,
                "training_status": c.training_status,
                "accuracy": c.accuracy,
                "macro_f1": c.macro_f1,
                "weighted_f1": c.weighted_f1
            }
            for c in sorted_comparisons
        ],
        "table": format_comparison_table(sorted_comparisons)
    }
