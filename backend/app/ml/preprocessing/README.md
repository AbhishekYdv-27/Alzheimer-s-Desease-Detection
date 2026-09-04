# ML Folder README

## Overview

This folder contains all machine learning related components for Alzheimer's Disease Detection.

## Subfolders

### preprocessing/

Contains scripts and utilities for preprocessing medical imaging data for Alzheimer's detection, including:

- MRI image normalization
- Skull stripping and brain extraction
- Brain region segmentation
- Feature extraction
- Data augmentation techniques

### models/

Repository for trained AI models and their configurations:

- Model architectures (future: Swin Transformer, ResNet, U-Net)
- Trained model weights (future)
- Model configuration files
- Hyperparameter settings

### evaluation/

Tools for model evaluation and performance assessment:

- Accuracy, sensitivity, specificity metrics
- ROC curve analysis
- Confusion matrix generation
- Cross-validation utilities
- Statistical significance testing

### explainability/

Explainable AI components for model interpretation:

- Grad-CAM visualizations
- SHAP values for feature importance
- Attention maps
- Counterfactual explanations

### training/

Model training pipelines and configurations:

- Training scripts
- Hyperparameter optimization
- Model checkpointing
- Early stopping mechanisms
- Distributed training setup
