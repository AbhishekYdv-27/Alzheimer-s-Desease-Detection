#!/usr/bin/env python3

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
import cv2

from backend.app.ml.models import ResNet50Architecture, SwinTransformer, get_device

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


class GradCAMError(Exception):
    def __init__(self, error_code: str, message: str):
        self.error_code = error_code
        self.message = message
        super().__init__(f"[{error_code}] {message}")


class GradCAMErrorCode:
    MODEL_NOT_AVAILABLE = "MODEL_NOT_AVAILABLE"
    LAYER_NOT_FOUND = "LAYER_NOT_FOUND"
    GRADIENT_FAILED = "GRADIENT_FAILED"
    FEATURE_NOT_AVAILABLE = "FEATURE_NOT_AVAILABLE"
    INVALID_TARGET_CLASS = "INVALID_TARGET_CLASS"
    EXPLAINABILITY_NOT_AVAILABLE = "EXPLANATION_NOT_AVAILABLE"


@dataclass
class GradCAMResult:
    success: bool
    heatmap: Optional[np.ndarray] = None
    overlay: Optional[np.ndarray] = None
    target_class: Optional[int] = None
    target_class_name: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class GradCAM:
    def __init__(self, model: nn.Module, target_layer: Optional[nn.Module] = None):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        self.device = get_device()

        if self.target_layer is None:
            self.target_layer = self._find_target_layer()

        self.hooks = []

    def _find_target_layer(self) -> Optional[nn.Module]:
        if isinstance(self.model, ResNet50Architecture):
            return self.model.backbone.layer4
        elif isinstance(self.model, SwinTransformer):
            return self.model.layers[-1] if hasattr(self.model, 'layers') else None
        else:
            for name, module in self.model.named_modules():
                if 'layer4' in name or 'last' in name.lower():
                    return module
            return None

    def _register_hooks(self):
        def forward_hook(module, input, output):
            self.activations = output

        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0]

        if self.target_layer is not None:
            self.hooks.append(
                self.target_layer.register_forward_hook(forward_hook)
            )
            self.hooks.append(
                self.target_layer.register_full_backward_hook(backward_hook)
            )

    def _remove_hooks(self):
        for hook in self.hooks:
            hook.remove()
        self.hooks = []

    def generate_cam(
        self,
        input_tensor: torch.Tensor,
        target_class: Optional[int] = None
    ) -> np.ndarray:
        self._register_hooks()

        try:
            self.model.eval()
            output = self.model(input_tensor)

            if target_class is None:
                target_class = output.argmax(dim=1).item()

            self.model.zero_grad()

            one_hot = torch.zeros_like(output)
            one_hot[0, target_class] = 1.0

            output.backward(gradient=one_hot, retain_graph=True)

            if self.gradients is None or self.activations is None:
                raise GradCAMError(
                    GradCAMErrorCode.GRADIENT_FAILED,
                    "Failed to compute gradients"
                )

            pooled_gradients = torch.mean(self.gradients, dim=[0, 2, 3])

            for i in range(self.activations.shape[1]):
                self.activations[:, i, :, :] *= pooled_gradients[i]

            heatmap = torch.mean(self.activations, dim=1).squeeze()

            heatmap = torch.relu(heatmap)

            if heatmap.max() > 0:
                heatmap = heatmap / heatmap.max()

            heatmap_np = heatmap.cpu().detach().numpy()

            return heatmap_np

        finally:
            self._remove_hooks()

    def generate_overlay(
        self,
        heatmap: np.ndarray,
        original_image: Image.Image,
        alpha: float = 0.4
    ) -> np.ndarray:
        heatmap_resized = cv2.resize(
            heatmap,
            (original_image.width, original_image.height)
        )

        heatmap_uint8 = np.uint8(255 * heatmap_resized)

        heatmap_color = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)

        img_array = np.array(original_image.convert("RGB"))
        heatmap_color = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)

        overlay = cv2.addWeighted(img_array, 1 - alpha, heatmap_color, alpha, 0)

        return overlay

    def explain(
        self,
        image_tensor: torch.Tensor,
        original_image: Image.Image,
        target_class: Optional[int] = None,
        target_class_name: Optional[str] = None,
        generate_overlay: bool = True
    ) -> GradCAMResult:
        if self.target_layer is None:
            return GradCAMResult(
                success=False,
                error_code=GradCAMErrorCode.LAYER_NOT_FOUND,
                error_message="Could not find target layer for GradCAM"
            )

        try:
            image_tensor = image_tensor.to(self.device)
            image_tensor.requires_grad = True

            heatmap = self.generate_cam(image_tensor, target_class)

            overlay = None
            if generate_overlay:
                overlay = self.generate_overlay(heatmap, original_image)

            return GradCAMResult(
                success=True,
                heatmap=heatmap,
                overlay=overlay,
                target_class=target_class,
                target_class_name=target_class_name
            )

        except Exception as e:
            return GradCAMResult(
                success=False,
                error_code=GradCAMErrorCode.GRADIENT_FAILED,
                error_message=str(e)
            )


def create_gradcam_explainer(model: nn.Module, architecture: str) -> Optional[GradCAM]:
    if "resnet" in architecture.lower():
        return GradCAM(model)
    elif "swin" in architecture.lower():
        return GradCAM(model)
    return None


def explain_prediction(
    model: nn.Module,
    image_tensor: torch.Tensor,
    original_image: Image.Image,
    target_class: int,
    architecture: str
) -> GradCAMResult:
    explainer = create_gradcam_explainer(model, architecture)

    if explainer is None:
        return GradCAMResult(
            success=False,
            error_code=GradCAMErrorCode.EXPLAINABILITY_NOT_AVAILABLE,
            error_message=f"GradCAM not supported for architecture: {architecture}"
        )

    from backend.app.ml.models import ALZHEIMER_CLASSES
    class_name = ALZHEIMER_CLASSES[target_class] if 0 <= target_class < len(ALZHEIMER_CLASSES) else None

    return explainer.explain(
        image_tensor=image_tensor,
        original_image=original_image,
        target_class=target_class,
        target_class_name=class_name,
        generate_overlay=True
    )
