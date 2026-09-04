#!/usr/bin/env python3

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple, List, Union


MODEL_NAME = "UNet"
ALZHEIMER_CLASSES = ["NonDemented", "VeryMildDemented", "MildDemented", "ModerateDemented"]


class UNetConfig:
    def __init__(
        self,
        in_channels: int = 3,
        out_channels: int = 1,
        base_filters: int = 64,
        depth: int = 4,
        use_batch_norm: bool = True,
        dropout_rate: float = 0.0,
        attention: bool = False,
        resize_input: bool = True,
        input_size: Tuple[int, int] = (224, 224)
    ):
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.base_filters = base_filters
        self.depth = depth
        self.use_batch_norm = use_batch_norm
        self.dropout_rate = dropout_rate
        self.attention = attention
        self.resize_input = resize_input
        self.input_size = input_size
        self.model_name = MODEL_NAME

    def to_dict(self) -> dict:
        return {
            "model_name": self.model_name,
            "in_channels": self.in_channels,
            "out_channels": self.out_channels,
            "base_filters": self.base_filters,
            "depth": self.depth,
            "use_batch_norm": self.use_batch_norm,
            "dropout_rate": self.dropout_rate,
            "attention": self.attention,
            "resize_input": self.resize_input,
            "input_size": self.input_size
        }


class DoubleConv(nn.Module):
    def __init__(self, in_channels, out_channels, mid_channels=None, use_bn=True, dropout=0.0):
        super().__init__()
        if not mid_channels:
            mid_channels = out_channels

        self.double_conv = nn.Sequential(
            nn.Conv2d(in_channels, mid_channels, kernel_size=3, padding=1, bias=not use_bn),
            nn.BatchNorm2d(mid_channels) if use_bn else nn.Identity(),
            nn.ReLU(inplace=True),
            nn.Dropout2d(dropout) if dropout > 0 else nn.Identity(),
            nn.Conv2d(mid_channels, out_channels, kernel_size=3, padding=1, bias=not use_bn),
            nn.BatchNorm2d(out_channels) if use_bn else nn.Identity(),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        return self.double_conv(x)


class Down(nn.Module):
    def __init__(self, in_channels, out_channels, use_bn=True, dropout=0.0):
        super().__init__()
        self.maxpool_conv = nn.Sequential(
            nn.MaxPool2d(2),
            DoubleConv(in_channels, out_channels, use_bn=use_bn, dropout=dropout)
        )

    def forward(self, x):
        return self.maxpool_conv(x)


class Up(nn.Module):
    def __init__(self, in_channels, out_channels, use_bn=True, dropout=0.0, bilinear=True):
        super().__init__()

        if bilinear:
            self.up = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)
            self.conv = DoubleConv(in_channels, out_channels, in_channels // 2, use_bn=use_bn, dropout=dropout)
        else:
            self.up = nn.ConvTranspose2d(in_channels, in_channels // 2, kernel_size=2, stride=2)
            self.conv = DoubleConv(in_channels, out_channels, use_bn=use_bn, dropout=dropout)

    def forward(self, x1, x2):
        x1 = self.up(x1)

        diffY = x2.size()[2] - x1.size()[2]
        diffX = x2.size()[3] - x1.size()[3]

        x1 = F.pad(x1, [diffX // 2, diffX - diffX // 2,
                        diffY // 2, diffY - diffY // 2])

        x = torch.cat([x2, x1], dim=1)
        return self.conv(x)


class OutConv(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size=1)

    def forward(self, x):
        return self.conv(x)


class UNet(nn.Module):
    def __init__(
        self,
        in_channels: int = 3,
        out_channels: int = 1,
        base_filters: int = 64,
        depth: int = 4,
        use_batch_norm: bool = True,
        dropout_rate: float = 0.0,
        bilinear: bool = True,
        return_features: bool = False
    ):
        super().__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.base_filters = base_filters
        self.depth = depth
        self.bilinear = bilinear
        self.return_features = return_features

        self.inc = DoubleConv(in_channels, base_filters, use_bn=use_batch_norm, dropout=dropout_rate)

        self.downs = nn.ModuleList()
        self.ups = nn.ModuleList()

        factor = 2 if bilinear else 1

        for i in range(depth - 1):
            in_f = base_filters * (2 ** i)
            out_f = base_filters * (2 ** (i + 1))
            self.downs.append(Down(in_f, out_f, use_bn=use_batch_norm, dropout=dropout_rate))

        for i in range(depth - 2, -1, -1):
            in_f = base_filters * (2 ** (i + 1))
            out_f = base_filters * (2 ** i) // factor
            self.ups.append(Up(in_f, out_f, use_bn=use_batch_norm, dropout=dropout_rate, bilinear=bilinear))

        self.outc = OutConv(base_filters, out_channels)

    def forward(self, x):
        features = []

        x = self.inc(x)
        features.append(x)

        for down in self.downs:
            x = down(x)
            features.append(x)

        features = features[:-1][::-1] + [features[-1]]

        for i, up in enumerate(self.ups):
            x = up(x, features[i])

        logits = self.outc(x)

        if self.return_features:
            return logits, features
        return logits

    def get_encoder_features(self, x):
        features = []

        x = self.inc(x)
        features.append(x)

        for down in self.downs:
            x = down(x)
            features.append(x)

        return features


class UNetSegmentationOutput:
    def __init__(
        self,
        logits: torch.Tensor,
        predicted_mask: Optional[torch.Tensor] = None,
        probabilities: Optional[torch.Tensor] = None,
        features: Optional[List[torch.Tensor]] = None
    ):
        self.logits = logits
        self.predicted_mask = predicted_mask
        self.probabilities = probabilities
        self.features = features

    def get_mask(self) -> torch.Tensor:
        if self.predicted_mask is not None:
            return self.predicted_mask
        if self.logits.shape[1] > 1:
            return torch.argmax(self.logits, dim=1)
        return torch.sigmoid(self.logits) > 0.5


def create_unet(
    in_channels: int = 3,
    out_channels: int = 1,
    base_filters: int = 64,
    depth: int = 4,
    use_batch_norm: bool = True,
    dropout_rate: float = 0.0,
    bilinear: bool = True
) -> UNet:
    return UNet(
        in_channels=in_channels,
        out_channels=out_channels,
        base_filters=base_filters,
        depth=depth,
        use_batch_norm=use_batch_norm,
        dropout_rate=dropout_rate,
        bilinear=bilinear
    )


def test_unet_forward() -> bool:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = create_unet(in_channels=3, out_channels=1, base_filters=32, depth=4)
    model = model.to(device)
    model.eval()

    test_input = torch.randn(2, 3, 224, 224).to(device)

    try:
        with torch.no_grad():
            output = model(test_input)

        expected_shape = (2, 1, 224, 224)
        assert output.shape == expected_shape, f"Expected shape {expected_shape}, got {output.shape}"

        return True
    except Exception as e:
        print(f"U-Net forward pass test failed: {e}")
        return False


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters())


def count_trainable_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


if __name__ == "__main__":
    print(f"Testing {MODEL_NAME} implementation...")

    model = create_unet(in_channels=3, out_channels=1, base_filters=32, depth=4)

    total_params = count_parameters(model)
    trainable_params = count_trainable_parameters(model)

    print(f"Model: {MODEL_NAME}")
    print(f"Total parameters: {total_params:,}")
    print(f"Trainable parameters: {trainable_params:,}")

    if test_unet_forward():
        print("Forward pass test: PASSED")
    else:
        print("Forward pass test: FAILED")
