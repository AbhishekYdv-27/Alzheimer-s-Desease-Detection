#!/usr/bin/env python3

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import torch
import torch.nn as nn
from collections.abc import Mapping
import logging

from backend.app.ml.models import (
    ResNet50Architecture,
    SwinTransformer,
    UNet,
    create_resnet50,
    create_swin_transformer,
    create_unet,
    get_device
)
from backend.app.ml.registry import ModelRegistry, ModelStatus, ALZHEIMER_CLASSES

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
logger = logging.getLogger(__name__)


@dataclass
class ModelLoadResult:
    success: bool = False
    model: Optional[nn.Module] = None
    error_code: str = ""
    error_message: str = ""
    model_name: str = ""
    model_version: str = ""


class ModelLoader:
    def __init__(self, registry: Optional[ModelRegistry] = None):
        self.registry = registry if registry is not None else ModelRegistry()

    def load_model(
        self,
        model_name: str,
        model_version: str = "1.0",
        device: Optional[torch.device] = None
    ) -> ModelLoadResult:
        if device is None:
            device = get_device()

        result = ModelLoadResult(model_name=model_name, model_version=model_version)

        is_valid, error_code, error_msg = self.registry.validate_model_file(model_name, model_version)
        if not is_valid:
            result.error_code = error_code
            result.error_message = error_msg
            return result

        meta = self.registry.get_model(model_name, model_version)

        try:
            model = self._create_model_architecture(meta.architecture, meta.config)

            if not meta.model_path:
                result.error_code = "MODEL_PATH_MISSING"
                result.error_message = f"No model path specified for {model_name}"
                return result

            model_path = self.registry.resolve_model_path(meta)
            checkpoint = torch.load(model_path, map_location=device, weights_only=True)
            if isinstance(checkpoint, Mapping) and "model_state_dict" in checkpoint:
                state_dict = checkpoint["model_state_dict"]
            else:
                state_dict = checkpoint

            if not isinstance(state_dict, Mapping) or not all(
                isinstance(key, str) and isinstance(value, torch.Tensor)
                for key, value in state_dict.items()
            ):
                raise ValueError("Checkpoint does not contain a tensor state dictionary")

            checkpoint_classes = checkpoint.get("class_names") if isinstance(checkpoint, Mapping) else None
            if checkpoint_classes is not None and list(checkpoint_classes) != meta.class_names:
                raise ValueError("Checkpoint class labels do not match the model registry")

            backbone_state_dict = {}
            for key, value in state_dict.items():
                if key.startswith("backbone."):
                    backbone_state_dict[key[len("backbone."):]] = value
                else:
                    backbone_state_dict[key] = value

            model.backbone.load_state_dict(backbone_state_dict, strict=True)

            model = model.to(device)
            model.eval()

            result.success = True
            result.model = model
            return result

        except FileNotFoundError:
            result.error_code = "MODEL_FILE_NOT_FOUND"
            result.error_message = "Configured model checkpoint was not found"
            return result
        except Exception:
            logger.exception("Configured model checkpoint could not be loaded")
            result.error_code = "MODEL_LOAD_FAILED"
            result.error_message = "Configured model checkpoint could not be loaded"
            return result

    def _create_model_architecture(self, architecture: str, config: Dict[str, Any]) -> nn.Module:
        architecture_lower = architecture.lower()

        if "resnet" in architecture_lower:
            return create_resnet50(
                num_classes=config.get("num_classes", 4),
                pretrained=config.get("pretrained", False),
                freeze_backbone=config.get("freeze_backbone", False),
                dropout_rate=config.get("dropout_rate", 0.5)
            )
        elif "swin" in architecture_lower:
            return create_swin_transformer(
                num_classes=config.get("num_classes", 4),
                pretrained=config.get("pretrained", False),
                img_size=config.get("input_size", [224, 224])[0],
                window_size=config.get("window_size", 7),
                embed_dim=config.get("embed_dim", 96),
                depths=tuple(config.get("depths", [2, 2, 6, 2])),
                num_heads=tuple(config.get("num_heads", [3, 6, 12, 24])),
                drop_rate=config.get("drop_rate", 0.0),
                attn_drop_rate=config.get("attn_drop_rate", 0.0),
                drop_path_rate=config.get("drop_path_rate", 0.1)
            )
        elif "unet" in architecture_lower:
            return create_unet(
                in_channels=config.get("in_channels", 3),
                out_channels=config.get("out_channels", 1),
                base_filters=config.get("base_filters", 64),
                depth=config.get("depth", 4),
                use_batch_norm=config.get("use_batch_norm", True),
                dropout_rate=config.get("dropout_rate", 0.0),
                bilinear=config.get("bilinear", True)
            )
        else:
            raise ValueError(f"Unknown architecture: {architecture}")

    def check_model_availability(self, model_name: str, model_version: str = "1.0") -> Tuple[bool, str]:
        meta = self.registry.get_model(model_name, model_version)

        if meta is None:
            return False, "MODEL_NOT_REGISTERED"

        if meta.training_status == ModelStatus.NOT_TRAINED.value:
            return False, "MODEL_NOT_TRAINED"

        if meta.training_status == ModelStatus.NOT_CONFIGURED.value:
            return False, "MODEL_NOT_CONFIGURED"

        if meta.training_status == ModelStatus.FAILED.value:
            return False, "MODEL_TRAINING_FAILED"

        if not meta.model_path:
            return False, "MODEL_PATH_MISSING"

        model_file = self.registry.resolve_model_path(meta)
        if not model_file.exists():
            return False, "MODEL_FILE_NOT_FOUND"
        try:
            from backend.app.ml.registry.model_registry import ModelRegistry

            valid, status, _ = ModelRegistry().validate_model_file(model_name, model_version)
            if not valid:
                return False, status
        except OSError:
            return False, "MODEL_FILE_UNREADABLE"

        return True, "AVAILABLE"


def load_trained_model(
    model_name: str,
    model_version: str = "1.0",
    device: Optional[torch.device] = None
) -> ModelLoadResult:
    loader = ModelLoader()
    return loader.load_model(model_name, model_version, device)


def check_model_ready(model_name: str, model_version: str = "1.0") -> Tuple[bool, str, str]:
    loader = ModelLoader()
    available, status = loader.check_model_availability(model_name, model_version)
    if available:
        return True, "READY", f"{model_name} v{model_version} is ready for inference"
    return False, status, f"{model_name} v{model_version} is not ready: {status}"
