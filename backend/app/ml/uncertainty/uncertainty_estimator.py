#!/usr/bin/env python3

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


class UncertaintyError(Exception):
    def __init__(self, error_code: str, message: str):
        self.error_code = error_code
        self.message = message
        super().__init__(f"[{error_code}] {message}")


class UncertaintyErrorCode:
    MODEL_NOT_AVAILABLE = "MODEL_NOT_AVAILABLE"
    UNCERTAINTY_NOT_AVAILABLE = "UNCERTAINTY_NOT_AVAILABLE"
    INFERENCE_FAILED = "INFERENCE_FAILED"
    INVALID_INPUT = "INVALID_INPUT"


@dataclass
class UncertaintyResult:
    success: bool
    mean_probabilities: Optional[np.ndarray] = None
    std_probabilities: Optional[np.ndarray] = None
    entropy: Optional[np.ndarray] = None
    uncertainty_score: Optional[float] = None
    num_samples: int = 0
    error_code: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class MCDropoutConfig:
    num_samples: int = 30
    dropout_rate: float = 0.5
    enable_mc_dropout: bool = True


def compute_predictive_entropy(probabilities: np.ndarray) -> np.ndarray:
    epsilon = 1e-10
    entropy = -np.sum(probabilities * np.log(probabilities + epsilon), axis=-1)
    return entropy


def compute_std_deviation(probabilities: np.ndarray) -> np.ndarray:
    return np.std(probabilities, axis=0)


def compute_uncertainty_score(
    mean_probs: np.ndarray,
    std_probs: np.ndarray,
    entropy: np.ndarray
) -> float:
    prob_uncertainty = np.mean(std_probs)
    entropy_uncertainty = np.mean(entropy)

    uncertainty = 0.5 * prob_uncertainty + 0.5 * entropy_uncertainty

    return float(uncertainty)


class MCDropoutUncertainty:
    def __init__(self, model: nn.Module, config: Optional[MCDropoutConfig] = None):
        self.model = model
        self.config = config if config is not None else MCDropoutConfig()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def enable_dropout(self):
        for module in self.model.modules():
            if isinstance(module, nn.Dropout) or isinstance(module, nn.Dropout2d):
                module.train()

    def predict(self, input_tensor: torch.Tensor) -> torch.Tensor:
        input_tensor = input_tensor.to(self.device)

        logits = self.model(input_tensor)
        probabilities = torch.softmax(logits, dim=1)

        return probabilities

    def estimate_uncertainty(
        self,
        input_tensor: torch.Tensor,
        num_samples: Optional[int] = None
    ) -> UncertaintyResult:
        if num_samples is None:
            num_samples = self.config.num_samples

        self.enable_dropout()

        all_probabilities = []

        try:
            for i in range(num_samples):
                with torch.no_grad():
                    probs = self.predict(input_tensor)
                    all_probabilities.append(probs.cpu().numpy())

            all_probabilities = np.array(all_probabilities)

            mean_probs = np.mean(all_probabilities, axis=0)
            std_probs = np.std(all_probabilities, axis=0)
            entropy = compute_predictive_entropy(mean_probs)

            uncertainty_score = compute_uncertainty_score(mean_probs, std_probs, entropy)

            return UncertaintyResult(
                success=True,
                mean_probabilities=mean_probs,
                std_probabilities=std_probs,
                entropy=entropy,
                uncertainty_score=uncertainty_score,
                num_samples=num_samples
            )

        except Exception as e:
            return UncertaintyResult(
                success=False,
                num_samples=0,
                error_code=UncertaintyErrorCode.INFERENCE_FAILED,
                error_message=str(e)
            )


class EnsembleUncertainty:
    def __init__(self, models: List[nn.Module]):
        self.models = models
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def estimate_uncertainty(self, input_tensor: torch.Tensor) -> UncertaintyResult:
        input_tensor = input_tensor.to(self.device)

        all_probabilities = []

        try:
            for model in self.models:
                model.eval()
                with torch.no_grad():
                    logits = model(input_tensor.unsqueeze(0))
                    probabilities = torch.softmax(logits, dim=1)
                    all_probabilities.append(probabilities.cpu().numpy())

            all_probabilities = np.array(all_probabilities)

            mean_probs = np.mean(all_probabilities, axis=0)
            std_probs = np.std(all_probabilities, axis=0)
            entropy = compute_predictive_entropy(mean_probs)

            uncertainty_score = compute_uncertainty_score(mean_probs, std_probs, entropy)

            return UncertaintyResult(
                success=True,
                mean_probabilities=mean_probs,
                std_probabilities=std_probs,
                entropy=entropy,
                uncertainty_score=uncertainty_score,
                num_samples=len(self.models)
            )

        except Exception as e:
            return UncertaintyResult(
                success=False,
                num_samples=0,
                error_code=UncertaintyErrorCode.INFERENCE_FAILED,
                error_message=str(e)
            )


def estimate_prediction_uncertainty(
    model: nn.Module,
    input_tensor: torch.Tensor,
    method: str = "mc_dropout",
    mc_config: Optional[MCDropoutConfig] = None,
    ensemble_models: Optional[List[nn.Module]] = None
) -> UncertaintyResult:
    if method == "mc_dropout":
        estimator = MCDropoutUncertainty(model, mc_config)
        return estimator.estimate_uncertainty(input_tensor)
    elif method == "ensemble" and ensemble_models:
        estimator = EnsembleUncertainty(ensemble_models)
        return estimator.estimate_uncertainty(input_tensor)
    else:
        return UncertaintyResult(
            success=False,
            error_code=UncertaintyErrorCode.INVALID_INPUT,
            error_message=f"Unknown uncertainty method or missing models: {method}"
        )


def get_uncertainty_interpretation(uncertainty_score: float) -> str:
    if uncertainty_score < 0.1:
        return "Very high confidence"
    elif uncertainty_score < 0.3:
        return "High confidence"
    elif uncertainty_score < 0.5:
        return "Moderate confidence"
    elif uncertainty_score < 0.7:
        return "Low confidence"
    else:
        return "Very low confidence - high uncertainty"


def check_uncertainty_available(model_available: bool, model_trained: bool) -> Tuple[bool, str]:
    if not model_available:
        return False, "MODEL_NOT_AVAILABLE"
    if not model_trained:
        return False, "MODEL_NOT_TRAINED"
    return True, "UNCERTAINTY_AVAILABLE"
