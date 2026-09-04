#!/usr/bin/env python3

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import torch
import torch.nn as nn
from PIL import Image
import cv2

from backend.app.ml.explainability.gradcam import (
    GradCAM,
    GradCAMResult,
    create_gradcam_explainer,
    explain_prediction,
    GradCAMErrorCode
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


@dataclass
class ExplanationResult:
    success: bool
    explanation_type: str
    explanation_data: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class ExplanationMetadata:
    model_name: str
    model_version: str
    predicted_class: str
    predicted_class_index: int
    confidence: float
    explanation_type: str
    generated_timestamp: str
    visualization_label: str = "AI MODEL VISUALIZATION"


class ExplanationService:
    def __init__(self):
        self.output_dir = PROJECT_ROOT / "reports" / "explanations"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_gradcam_explanation(
        self,
        model: nn.Module,
        image_tensor: torch.Tensor,
        original_image: Image.Image,
        target_class: int,
        architecture: str,
        save_visualization: bool = True
    ) -> ExplanationResult:
        result = explain_prediction(model, image_tensor, original_image, target_class, architecture)

        if not result.success:
            return ExplanationResult(
                success=False,
                explanation_type="GradCAM",
                error_code=result.error_code,
                error_message=result.error_message
            )

        explanation_data = {
            "heatmap": result.heatmap,
            "target_class": result.target_class,
            "target_class_name": result.target_class_name
        }

        file_path = None
        if save_visualization and result.overlay is not None:
            file_path = self._save_overlay(result.overlay)

        return ExplanationResult(
            success=True,
            explanation_type="GradCAM",
            explanation_data=explanation_data,
            file_path=file_path
        )

    def _save_overlay(self, overlay: np.ndarray) -> str:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gradcam_overlay_{timestamp}.png"
        filepath = self.output_dir / filename

        overlay_rgb = cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(filepath), overlay_rgb)

        return str(filepath)

    def create_explanation_response(
        self,
        explanation_result: ExplanationResult,
        metadata: ExplanationMetadata
    ) -> Dict[str, Any]:
        response = {
            "success": explanation_result.success,
            "explanation_type": explanation_result.explanation_type,
            "metadata": {
                "model_name": metadata.model_name,
                "model_version": metadata.model_version,
                "predicted_class": metadata.predicted_class,
                "confidence": metadata.confidence,
                "generated_timestamp": metadata.generated_timestamp,
                "visualization_label": metadata.visualization_label
            }
        }

        if explanation_result.success:
            response["data"] = explanation_result.explanation_data
            response["visualization_path"] = explanation_result.file_path
        else:
            response["error"] = {
                "code": explanation_result.error_code,
                "message": explanation_result.error_message
            }

        return response


def get_explanation_availability(
    model_available: bool,
    architecture: str
) -> Tuple[bool, str]:
    if not model_available:
        return False, "No trained model available for explanation"

    if "resnet" in architecture.lower() or "swin" in architecture.lower():
        return True, "GradCAM explanation available"

    return False, f"Explanation not supported for architecture: {architecture}"
