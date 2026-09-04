#!/usr/bin/env python3

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import torch
import torch.nn as nn
from PIL import Image
import numpy as np

from backend.app.ml.models import get_device, ALZHEIMER_CLASSES
from backend.app.ml.registry import ModelRegistry, ModelStatus
from backend.app.ml.models.model_loader import ModelLoader, check_model_ready
from backend.app.ml.preprocessing import (
    DatasetConfig,
    validate_image_file,
    SUPPORTED_IMAGE_EXTENSIONS
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


class PredictionError(Exception):
    def __init__(self, error_code: str, message: str):
        self.error_code = error_code
        self.message = message
        super().__init__(f"[{error_code}] {message}")


class ErrorCode:
    MODEL_NOT_TRAINED = "MODEL_NOT_TRAINED"
    MODEL_NOT_AVAILABLE = "MODEL_NOT_AVAILABLE"
    MODEL_FILE_NOT_FOUND = "MODEL_FILE_NOT_FOUND"
    MODEL_LOAD_FAILED = "MODEL_LOAD_FAILED"
    INVALID_INPUT = "INVALID_INPUT"
    INVALID_IMAGE = "INVALID_IMAGE"
    PREPROCESSING_FAILED = "PREPROCESSING_FAILED"
    PREDICTION_FAILED = "PREDICTION_FAILED"


@dataclass
class PredictionRequest:
    image_path: str
    model_name: str
    model_version: str = "1.0"
    return_probabilities: bool = True
    return_uncertainty: bool = False


@dataclass
class PredictionResponse:
    predicted_class: str
    predicted_class_index: int
    model_name: str
    model_version: str
    class_probabilities: Optional[Dict[str, float]] = None
    confidence: Optional[float] = None
    uncertainty: Optional[Dict[str, float]] = None
    explanation_available: bool = False
    timestamp: str = ""
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    def is_successful(self) -> bool:
        return self.error_code is None


class InferenceService:
    def __init__(self, registry: Optional[ModelRegistry] = None):
        self.registry = registry if registry is not None else ModelRegistry()
        self.model_loader = ModelLoader(self.registry)
        self._cached_model = None
        self._cached_model_name = None
        self._cached_model_version = None

    def validate_input(self, image_path: str) -> Tuple[bool, str]:
        if not image_path:
            return False, "Image path is empty"

        path = Path(image_path)
        if not path.exists():
            return False, f"Image file not found: {image_path}"

        if not path.is_file():
            return False, f"Path is not a file: {image_path}"

        ext = path.suffix.lower()
        if ext not in SUPPORTED_IMAGE_EXTENSIONS:
            return False, f"Unsupported image format: {ext}"

        is_valid, message, _ = validate_image_file(str(path))
        if not is_valid:
            return False, f"Invalid image: {message}"

        return True, "Valid"

    def preprocess_image(
        self,
        image_path: str,
        target_size: Tuple[int, int] = (224, 224)
    ) -> Optional[torch.Tensor]:
        try:
            image = Image.open(image_path).convert("RGB")
            image = image.resize(target_size, Image.BILINEAR)

            image_array = np.array(image).astype(np.float32) / 255.0
            image_tensor = torch.from_numpy(image_array).permute(2, 0, 1)

            mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
            std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
            image_tensor = (image_tensor - mean) / std

            return image_tensor
        except Exception as e:
            return None

    def _get_model(self, model_name: str, model_version: str) -> Optional[nn.Module]:
        if (self._cached_model is not None and
            self._cached_model_name == model_name and
            self._cached_model_version == model_version):
            return self._cached_model

        result = self.model_loader.load_model(model_name, model_version)

        if result.success:
            self._cached_model = result.model
            self._cached_model_name = model_name
            self._cached_model_version = model_version
            return result.model

        return None

    def predict(self, request: PredictionRequest) -> PredictionResponse:
        timestamp = datetime.now().isoformat()

        ready, status, msg = check_model_ready(request.model_name, request.model_version)
        if not ready:
            return PredictionResponse(
                predicted_class="",
                predicted_class_index=-1,
                model_name=request.model_name,
                model_version=request.model_version,
                timestamp=timestamp,
                error_code=status,
                error_message=msg
            )

        input_valid, validation_msg = self.validate_input(request.image_path)
        if not input_valid:
            return PredictionResponse(
                predicted_class="",
                predicted_class_index=-1,
                model_name=request.model_name,
                model_version=request.model_version,
                timestamp=timestamp,
                error_code=ErrorCode.INVALID_IMAGE,
                error_message=validation_msg
            )

        model = self._get_model(request.model_name, request.model_version)
        if model is None:
            return PredictionResponse(
                predicted_class="",
                predicted_class_index=-1,
                model_name=request.model_name,
                model_version=request.model_version,
                timestamp=timestamp,
                error_code=ErrorCode.MODEL_LOAD_FAILED,
                error_message="Failed to load model"
            )

        image_tensor = self.preprocess_image(request.image_path)
        if image_tensor is None:
            return PredictionResponse(
                predicted_class="",
                predicted_class_index=-1,
                model_name=request.model_name,
                model_version=request.model_version,
                timestamp=timestamp,
                error_code=ErrorCode.PREPROCESSING_FAILED,
                error_message="Failed to preprocess image"
            )

        try:
            device = get_device()
            image_tensor = image_tensor.unsqueeze(0).to(device)
            model.eval()

            with torch.no_grad():
                logits = model(image_tensor)

            probabilities = torch.softmax(logits, dim=1).cpu().numpy()[0]
            predicted_idx = int(np.argmax(probabilities))
            confidence = float(probabilities[predicted_idx])

            class_probabilities = {
                cls: float(prob)
                for cls, prob in zip(ALZHEIMER_CLASSES, probabilities)
            }

            return PredictionResponse(
                predicted_class=ALZHEIMER_CLASSES[predicted_idx],
                predicted_class_index=predicted_idx,
                class_probabilities=class_probabilities if request.return_probabilities else None,
                confidence=confidence,
                model_name=request.model_name,
                model_version=request.model_version,
                explanation_available=True,
                timestamp=timestamp
            )

        except Exception as e:
            return PredictionResponse(
                predicted_class="",
                predicted_class_index=-1,
                model_name=request.model_name,
                model_version=request.model_version,
                timestamp=timestamp,
                error_code=ErrorCode.PREDICTION_FAILED,
                error_message=f"Prediction failed: {str(e)}"
            )

    def predict_batch(
        self,
        image_paths: List[str],
        model_name: str,
        model_version: str = "1.0"
    ) -> List[PredictionResponse]:
        return [self.predict(PredictionRequest(
            image_path=path,
            model_name=model_name,
            model_version=model_version
        )) for path in image_paths]

    def clear_cache(self):
        self._cached_model = None
        self._cached_model_name = None
        self._cached_model_version = None


def create_prediction_readiness_report(model_name: str, model_version: str = "1.0") -> Dict[str, Any]:
    checks = []
    all_passed = True

    registry = ModelRegistry()

    meta = registry.get_model(model_name, model_version)
    checks.append({
        "check": "Model registered",
        "passed": meta is not None,
        "message": f"Model {model_name} v{model_version}" + (" found" if meta else " not found")
    })
    if meta is None:
        all_passed = False

    if meta:
        status_ok = meta.training_status == ModelStatus.TRAINED.value
        checks.append({
            "check": "Model status is TRAINED",
            "passed": status_ok,
            "message": f"Status: {meta.training_status}"
        })
        if not status_ok:
            all_passed = False

    if meta and meta.model_path:
        file_exists = Path(meta.model_path).exists()
        checks.append({
            "check": "Model file exists",
            "passed": file_exists,
            "message": f"File: {meta.model_path}"
        })
        if not file_exists:
            all_passed = False
    else:
        checks.append({
            "check": "Model file exists",
            "passed": False,
            "message": "No model path specified"
        })
        all_passed = False

    return {
        "model_name": model_name,
        "model_version": model_version,
        "ready": all_passed,
        "checks": checks
    }
