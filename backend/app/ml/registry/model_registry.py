#!/usr/bin/env python3

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


class ModelStatus(Enum):
    NOT_CONFIGURED = "NOT_CONFIGURED"
    NOT_TRAINED = "NOT_TRAINED"
    TRAINING = "TRAINING"
    TRAINED = "TRAINED"
    FAILED = "FAILED"
    MODEL_NOT_AVAILABLE = "MODEL_NOT_AVAILABLE"


class ModelArchitecture(Enum):
    RESNET50 = "ResNet50"
    SWIN_TRANSFORMER = "SwinTransformer"
    UNET = "UNet"
    UNKNOWN = "Unknown"


ALZHEIMER_CLASSES = ["NonDemented", "VeryMildDemented", "MildDemented", "ModerateDemented"]


@dataclass
class ModelMetadata:
    model_name: str
    model_version: str
    architecture: str
    num_classes: int
    class_names: List[str] = field(default_factory=lambda: ALZHEIMER_CLASSES.copy())
    model_path: str = ""
    training_status: str = ModelStatus.NOT_TRAINED.value
    experiment_id: str = ""
    created_date: str = ""
    updated_date: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    input_size: tuple = (224, 224)
    input_channels: int = 3

    def to_dict(self) -> dict:
        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "architecture": self.architecture,
            "num_classes": self.num_classes,
            "class_names": self.class_names,
            "model_path": self.model_path,
            "training_status": self.training_status,
            "experiment_id": self.experiment_id,
            "created_date": self.created_date,
            "updated_date": self.updated_date,
            "metrics": self.metrics,
            "notes": self.notes,
            "config": self.config,
            "input_size": list(self.input_size),
            "input_channels": self.input_channels
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ModelMetadata":
        data = data.copy()
        data["input_size"] = tuple(data.get("input_size", [224, 224]))
        return cls(**data)


class ModelRegistry:
    def __init__(self, registry_path: Optional[Path] = None):
        if registry_path is None:
            registry_path = PROJECT_ROOT / "models" / "registry.json"
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.models: Dict[str, ModelMetadata] = {}
        self._load()

    def _load(self) -> None:
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.models = {
                        name: ModelMetadata.from_dict(info)
                        for name, info in data.get("models", {}).items()
                    }
            except Exception:
                self.models = {}

    def _save(self) -> None:
        data = {
            "models": {
                name: meta.to_dict()
                for name, meta in self.models.items()
            },
            "last_updated": datetime.now().isoformat()
        }
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def register_model(self, metadata: ModelMetadata) -> bool:
        try:
            key = f"{metadata.model_name}_{metadata.model_version}"
            self.models[key] = metadata
            self._save()
            return True
        except Exception:
            return False

    def get_model(self, model_name: str, model_version: str = "1.0") -> Optional[ModelMetadata]:
        key = f"{model_name}_{model_version}"
        return self.models.get(key)

    def get_all_models(self) -> List[ModelMetadata]:
        return list(self.models.values())

    def get_models_by_architecture(self, architecture: str) -> List[ModelMetadata]:
        return [
            meta for meta in self.models.values()
            if meta.architecture.lower() == architecture.lower()
        ]

    def get_models_by_status(self, status: ModelStatus) -> List[ModelMetadata]:
        return [
            meta for meta in self.models.values()
            if meta.training_status == status.value
        ]

    def get_trained_models(self) -> List[ModelMetadata]:
        return self.get_models_by_status(ModelStatus.TRAINED)

    def update_model_status(
        self,
        model_name: str,
        model_version: str,
        status: ModelStatus,
        metrics: Optional[Dict] = None,
        model_path: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        key = f"{model_name}_{model_version}"
        if key not in self.models:
            return False

        self.models[key].training_status = status.value
        self.models[key].updated_date = datetime.now().isoformat()

        if metrics is not None:
            self.models[key].metrics.update(metrics)
        if model_path is not None:
            self.models[key].model_path = model_path
        if notes is not None:
            self.models[key].notes = notes

        self._save()
        return True

    def model_exists(self, model_name: str, model_version: str = "1.0") -> bool:
        key = f"{model_name}_{model_version}"
        return key in self.models

    def is_model_trained(self, model_name: str, model_version: str = "1.0") -> bool:
        meta = self.get_model(model_name, model_version)
        if meta is None:
            return False
        return meta.training_status == ModelStatus.TRAINED.value

    def validate_model_file(self, model_name: str, model_version: str = "1.0") -> tuple:
        meta = self.get_model(model_name, model_version)

        if meta is None:
            return False, "MODEL_NOT_REGISTERED", f"Model {model_name} v{model_version} not found in registry"

        if meta.training_status != ModelStatus.TRAINED.value:
            return False, "MODEL_NOT_TRAINED", f"Model {model_name} v{model_version} has status: {meta.training_status}"

        if not meta.model_path:
            return False, "MODEL_PATH_MISSING", f"No model path specified for {model_name} v{model_version}"

        model_file = Path(meta.model_path)
        if not model_file.exists():
            return False, "MODEL_FILE_NOT_FOUND", f"Model file not found: {model_file}"

        return True, "VALID", "Model validation passed"

    def unregister_model(self, model_name: str, model_version: str = "1.0") -> bool:
        key = f"{model_name}_{model_version}"
        if key in self.models:
            del self.models[key]
            self._save()
            return True
        return False


def create_default_registry() -> ModelRegistry:
    registry = ModelRegistry()

    resnet_meta = ModelMetadata(
        model_name="ResNet50",
        model_version="1.0",
        architecture=ModelArchitecture.RESNET50.value,
        num_classes=4,
        class_names=ALZHEIMER_CLASSES.copy(),
        training_status=ModelStatus.NOT_TRAINED.value,
        created_date=datetime.now().isoformat(),
        updated_date=datetime.now().isoformat(),
        config={
            "pretrained": False,
            "freeze_backbone": False,
            "dropout_rate": 0.5,
            "input_size": [224, 224]
        }
    )

    swin_meta = ModelMetadata(
        model_name="SwinTransformer",
        model_version="1.0",
        architecture=ModelArchitecture.SWIN_TRANSFORMER.value,
        num_classes=4,
        class_names=ALZHEIMER_CLASSES.copy(),
        training_status=ModelStatus.NOT_TRAINED.value,
        created_date=datetime.now().isoformat(),
        updated_date=datetime.now().isoformat(),
        config={
            "pretrained": False,
            "embed_dim": 96,
            "depths": [2, 2, 6, 2],
            "num_heads": [3, 6, 12, 24],
            "window_size": 7,
            "input_size": [224, 224]
        }
    )

    unet_meta = ModelMetadata(
        model_name="UNet",
        model_version="1.0",
        architecture=ModelArchitecture.UNET.value,
        num_classes=1,
        training_status=ModelStatus.NOT_TRAINED.value,
        created_date=datetime.now().isoformat(),
        updated_date=datetime.now().isoformat(),
        config={
            "in_channels": 3,
            "out_channels": 1,
            "base_filters": 64,
            "depth": 4,
            "input_size": [224, 224]
        }
    )

    registry.register_model(resnet_meta)
    registry.register_model(swin_meta)
    registry.register_model(unet_meta)

    return registry
