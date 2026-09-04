# ML Models Folder README

## Overview

This folder will store trained models for Alzheimer's Disease detection.

## Purpose

All trained AI models for the Alzheimer's Disease Detection platform will be stored here, including:

- Model architecture files
- Trained model weights
- Model configuration parameters
- Version control for different model iterations

## Future Contents

- **Swin Transformer**: for hierarchical feature extraction from brain MRIs
- **ResNet50**: for baseline classification performance
- **U-Net**: for segmentation-based diagnosis support
- **Hybrid Models**: combinations of above architectures
- **Model Zoo**: collection of pre-trained models for transfer learning

## Storage Guidelines

- Use semantic version naming (v1.0.0, v2.0.0, etc.)
- Include configuration files with each model
- Document training parameters and dataset used
- Include performance benchmarks and evaluation metrics
- Store model cards with usage instructions and limitations

## File Organization

```
models/
├── swin_transformer/
│   ├── v1.0.0/
│   │   ├── model.pt
│   │   ├── config.json
│   │   └── model_card.md
│   └── v2.0.0/
│       ├── model.pt
│       ├── config.json
│       └── model_card.md
├── resnet50/
│   ├── v1.0.0/
│   │   ├── model.pt
│   │   ├── config.json
│   │   └── model_card.md
└── unet/
    ├── v1.0.0/
    │   ├── model.pt
    │   ├── config.json
    │   └── model_card.md
```
