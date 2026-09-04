#!/usr/bin/env python3

from typing import Optional, Tuple, List
import torch
import torch.nn as nn
from torchvision import models
from torchvision.models import ResNet50_Weights


MODEL_NAME = "ResNet50"
NUM_CLASSES = 4
ALZHEIMER_CLASSES = ["NonDemented", "VeryMildDemented", "MildDemented", "ModerateDemented"]


class ResNet50Architecture(nn.Module):
    def __init__(
        self,
        num_classes: int = NUM_CLASSES,
        pretrained: bool = False,
        freeze_backbone: bool = False,
        dropout_rate: float = 0.5
    ):
        super().__init__()

        self.model_name = MODEL_NAME
        self.num_classes = num_classes
        self.pretrained = pretrained

        if pretrained:
            weights = ResNet50_Weights.IMAGENET1K_V1
            self.backbone = models.resnet50(weights=weights)
        else:
            self.backbone = models.resnet50(weights=None)

        if freeze_backbone:
            for param in self.backbone.parameters():
                param.requires_grad = False

            for param in self.backbone.layer4.parameters():
                param.requires_grad = True

        in_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Sequential(
            nn.Dropout(p=dropout_rate),
            nn.Linear(in_features, num_classes)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)

    def get_feature_extractor(self) -> nn.Module:
        features = nn.Sequential(
            self.backbone.conv1,
            self.backbone.bn1,
            self.backbone.relu,
            self.backbone.maxpool,
            self.backbone.layer1,
            self.backbone.layer2,
            self.backbone.layer3,
            self.backbone.layer4,
        )
        return features

    def get_avgpool_output(self, x: torch.Tensor) -> torch.Tensor:
        x = self.backbone.conv1(x)
        x = self.backbone.bn1(x)
        x = self.backbone.relu(x)
        x = self.backbone.maxpool(x)

        x = self.backbone.layer1(x)
        x = self.backbone.layer2(x)
        x = self.backbone.layer3(x)
        x = self.backbone.layer4(x)

        x = self.backbone.avgpool(x)
        x = torch.flatten(x, 1)
        return x

    def get_layer4_features(self, x: torch.Tensor) -> torch.Tensor:
        x = self.backbone.conv1(x)
        x = self.backbone.bn1(x)
        x = self.backbone.relu(x)
        x = self.backbone.maxpool(x)

        x = self.backbone.layer1(x)
        x = self.backbone.layer2(x)
        x = self.backbone.layer3(x)
        x = self.backbone.layer4(x)
        return x


class ResNet50Config:
    def __init__(
        self,
        num_classes: int = NUM_CLASSES,
        pretrained: bool = False,
        freeze_backbone: bool = False,
        dropout_rate: float = 0.5,
        input_size: Tuple[int, int] = (224, 224),
        input_channels: int = 3,
        batch_norm_momentum: float = 0.1,
        activation: str = "relu"
    ):
        self.num_classes = num_classes
        self.pretrained = pretrained
        self.freeze_backbone = freeze_backbone
        self.dropout_rate = dropout_rate
        self.input_size = input_size
        self.input_channels = input_channels
        self.batch_norm_momentum = batch_norm_momentum
        self.activation = activation
        self.model_name = MODEL_NAME

    def to_dict(self) -> dict:
        return {
            "model_name": self.model_name,
            "num_classes": self.num_classes,
            "pretrained": self.pretrained,
            "freeze_backbone": self.freeze_backbone,
            "dropout_rate": self.dropout_rate,
            "input_size": self.input_size,
            "input_channels": self.input_channels,
            "batch_norm_momentum": self.batch_norm_momentum,
            "activation": self.activation
        }

    @classmethod
    def from_dict(cls, config_dict: dict) -> "ResNet50Config":
        return cls(**{k: v for k, v in config_dict.items() if k != "model_name"})


def create_resnet50(
    num_classes: int = NUM_CLASSES,
    pretrained: bool = False,
    freeze_backbone: bool = False,
    dropout_rate: float = 0.5
) -> ResNet50Architecture:
    return ResNet50Architecture(
        num_classes=num_classes,
        pretrained=pretrained,
        freeze_backbone=freeze_backbone,
        dropout_rate=dropout_rate
    )


def get_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters())


def count_trainable_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def test_resnet50_forward() -> bool:
    device = get_device()

    model = create_resnet50(num_classes=NUM_CLASSES, pretrained=False)
    model = model.to(device)
    model.eval()

    test_input = torch.randn(2, 3, 224, 224).to(device)

    try:
        with torch.no_grad():
            output = model(test_input)

        assert output.shape == (2, NUM_CLASSES), f"Expected shape (2, {NUM_CLASSES}), got {output.shape}"

        probabilities = torch.softmax(output, dim=1)
        assert probabilities.shape == (2, NUM_CLASSES)
        assert torch.allclose(probabilities.sum(dim=1), torch.ones(2).to(device), atol=1e-5)

        return True
    except Exception as e:
        print(f"ResNet50 forward pass test failed: {e}")
        return False


if __name__ == "__main__":
    print(f"Testing {MODEL_NAME} implementation...")

    model = create_resnet50(num_classes=NUM_CLASSES, pretrained=False)

    total_params = count_parameters(model)
    trainable_params = count_trainable_parameters(model)

    print(f"Model: {MODEL_NAME}")
    print(f"Number of classes: {NUM_CLASSES}")
    print(f"Classes: {ALZHEIMER_CLASSES}")
    print(f"Total parameters: {total_params:,}")
    print(f"Trainable parameters: {trainable_params:,}")

    if test_resnet50_forward():
        print("Forward pass test: PASSED")
    else:
        print("Forward pass test: FAILED")
