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
    return [
        ModelInfo(
            model_name=m.model_name,
            model_version=m.model_version,
            architecture=m.architecture,
            num_classes=m.num_classes,
            class_names=m.class_names,
            training_status=m.training_status,
            model_path=m.model_path if m.model_path else None,
            experiment_id=m.experiment_id if m.experiment_id else None,
            metrics=m.metrics
        )
        for m in models
    ]


@router.get("/status")
def get_all_statuses():
    registry = get_registry()
    models = registry.get_all_models()
    return {
        "models": [
            {
                "model_name": m.model_name,
                "model_version": m.model_version,
                "status": m.training_status,
                "available": m.training_status == "TRAINED"
            }
            for m in models
        ]
    }


@router.get("/{model_name}", response_model=ModelInfo)
def get_model_info(model_name: str):
    registry = get_registry()
    meta = registry.get_model(model_name)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
    return ModelInfo(
        model_name=meta.model_name,
        model_version=meta.model_version,
        architecture=meta.architecture,
        num_classes=meta.num_classes,
        class_names=meta.class_names,
        training_status=meta.training_status,
        model_path=meta.model_path if meta.model_path else None,
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
