from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import tempfile
from pathlib import Path
import numpy as np
import torch
from backend.app.ml.models import get_device
from backend.app.ml.models.model_loader import ModelLoader

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent

router = APIRouter(prefix="/api", tags=["prediction"])


class PredictionResponseModel(BaseModel):
    predicted_class: str
    predicted_class_index: int
    class_probabilities: Optional[Dict[str, float]] = None
    confidence: Optional[float] = None
    uncertainty: Optional[Dict[str, float]] = None
    model_name: str
    model_version: str
    explanation_available: bool
    timestamp: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class BatchPredictionRequest(BaseModel):
    model_name: str
    model_version: str = "1.0"


@router.post("/predict", response_model=PredictionResponseModel)
async def predict(
    file: UploadFile = File(...),
    model_name: str = Form(...),
    model_version: str = Form("1.0")
):
    from backend.app.ml.models.model_loader import check_model_ready
    ready, status, message = check_model_ready(model_name, model_version)
    if not ready:
        return PredictionResponseModel(
            predicted_class="",
            predicted_class_index=-1,
            model_name=model_name,
            model_version=model_version,
            explanation_available=False,
            timestamp="",
            error_code=status,
            error_message=message
        )

    allowed_types = {"image/jpeg", "image/png", "image/bmp", "image/tiff"}
    if file.content_type not in allowed_types:
        return PredictionResponseModel(
            predicted_class="",
            predicted_class_index=-1,
            model_name=model_name,
            model_version=model_version,
            explanation_available=False,
            timestamp="",
            error_code="INVALID_IMAGE",
            error_message=f"Unsupported image format: {file.content_type}"
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        from backend.app.ml.inference import InferenceService, PredictionRequest
        service = InferenceService()
        request = PredictionRequest(
            image_path=tmp_path,
            model_name=model_name,
            model_version=model_version,
            return_probabilities=True,
            return_uncertainty=False
        )
        result = service.predict(request)

        return PredictionResponseModel(
            predicted_class=result.predicted_class,
            predicted_class_index=result.predicted_class_index,
            class_probabilities=result.class_probabilities,
            confidence=result.confidence,
            model_name=result.model_name,
            model_version=result.model_version,
            explanation_available=result.explanation_available,
            timestamp=result.timestamp,
            error_code=result.error_code,
            error_message=result.error_message
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@router.post("/explain")
async def explain(
    file: UploadFile = File(...),
    model_name: str = Form(...),
    model_version: str = Form("1.0"),
    target_class: Optional[int] = Form(None)
):
    from backend.app.ml.models.model_loader import check_model_ready, ModelLoader
    from backend.app.ml.explainability import GradCAM, GradCAMResult
    from PIL import Image
    import cv2
    from datetime import datetime
    import os

    ready, status, message = check_model_ready(model_name, model_version)
    if not ready:
        return {
            "success": False,
            "predicted_class": "",
            "predicted_class_index": -1,
            "confidence": 0.0,
            "model_name": model_name,
            "model_version": model_version,
            "heatmap_url": None,
            "overlay_url": None,
            "explanation_available": False,
            "error_code": status,
            "error_message": message
        }

    allowed_types = {"image/jpeg", "image/png", "image/bmp", "image/tiff"}
    if file.content_type not in allowed_types:
        return {
            "success": False,
            "predicted_class": "",
            "predicted_class_index": -1,
            "confidence": 0.0,
            "model_name": model_name,
            "model_version": model_version,
            "heatmap_url": None,
            "overlay_url": None,
            "explanation_available": False,
            "error_code": "INVALID_IMAGE",
            "error_message": f"Unsupported image format: {file.content_type}"
        }

    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    results_dir = Path(PROJECT_ROOT) / "backend" / "results" / "gradcam"
    results_dir.mkdir(parents=True, exist_ok=True)

    try:
        loader = ModelLoader()
        model_result = loader.load_model(model_name, model_version)

        if not model_result.success:
            return {
                "success": False,
                "predicted_class": "",
                "predicted_class_index": -1,
                "confidence": 0.0,
                "model_name": model_name,
                "model_version": model_version,
                "heatmap_url": None,
                "overlay_url": None,
                "explanation_available": False,
                "error_code": model_result.error_code or "MODEL_LOAD_FAILED",
                "error_message": model_result.error_message or "Failed to load model"
            }

        model = model_result.model

        image = Image.open(tmp_path).convert("RGB")
        original_image_array = np.array(image)

        target_size = (224, 224)
        image_resized = image.resize(target_size, Image.BILINEAR)

        image_array = np.array(image_resized).astype(np.float32) / 255.0
        image_tensor = torch.from_numpy(image_array).permute(2, 0, 1)
        mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
        image_tensor = (image_tensor - mean) / std
        image_tensor = image_tensor.unsqueeze(0)

        device = get_device()
        image_tensor = image_tensor.to(device)
        model.eval()

        with torch.no_grad():
            logits = model(image_tensor)
            probabilities = torch.softmax(logits, dim=1).cpu().numpy()[0]

        predicted_idx = int(np.argmax(probabilities))
        confidence = float(probabilities[predicted_idx])

        if target_class is None:
            target_class = predicted_idx

        gradcam = GradCAM(model)
        image_tensor_grad = image_tensor.clone()
        image_tensor_grad.requires_grad = True

        heatmap = gradcam.generate_cam(image_tensor_grad, target_class=target_class)

        heatmap_resized = cv2.resize(
            heatmap,
            (original_image_array.shape[1], original_image_array.shape[0])
        )
        heatmap_uint8 = np.uint8(255 * heatmap_resized)
        heatmap_color = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
        heatmap_color = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

        heatmap_filename = f"heatmap_{timestamp_str}.png"
        heatmap_filepath = results_dir / heatmap_filename
        heatmap_bgr = cv2.cvtColor(heatmap_color, cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(heatmap_filepath), heatmap_bgr)

        overlay = cv2.addWeighted(original_image_array, 0.6, heatmap_color, 0.4, 0)

        overlay_filename = f"overlay_{timestamp_str}.png"
        overlay_filepath = results_dir / overlay_filename
        overlay_bgr = cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(overlay_filepath), overlay_bgr)

        heatmap_url = f"/api/results/gradcam/{heatmap_filename}"
        overlay_url = f"/api/results/gradcam/{overlay_filename}"

        from backend.app.ml.models import ALZHEIMER_CLASSES
        predicted_class_name = ALZHEIMER_CLASSES[predicted_idx] if 0 <= predicted_idx < len(ALZHEIMER_CLASSES) else f"Class_{predicted_idx}"

        return {
            "success": True,
            "predicted_class": predicted_class_name,
            "predicted_class_index": predicted_idx,
            "confidence": confidence,
            "model_name": model_name,
            "model_version": model_version,
            "heatmap_url": heatmap_url,
            "overlay_url": overlay_url,
            "explanation_available": True,
            "error_code": None,
            "error_message": None
        }

    except Exception as e:
        return {
            "success": False,
            "predicted_class": "",
            "predicted_class_index": -1,
            "confidence": 0.0,
            "model_name": model_name,
            "model_version": model_version,
            "heatmap_url": None,
            "overlay_url": None,
            "explanation_available": False,
            "error_code": "EXPLANATION_FAILED",
            "error_message": f"Explanation generation failed: {str(e)}"
        }
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@router.get("/predict/health")
def prediction_health():
    return {
        "status": "HEALTHY",
        "service": "prediction",
        "note": "Prediction endpoint ready. Model availability must be checked separately."
    }
