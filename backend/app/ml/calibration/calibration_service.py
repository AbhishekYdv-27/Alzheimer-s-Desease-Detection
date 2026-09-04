#!/usr/bin/env python3

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import torch
import torch.nn as nn
from sklearn.calibration import calibration_curve
from sklearn.metrics import auc

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


class CalibrationError(Exception):
    def __init__(self, error_code: str, message: str):
        self.error_code = error_code
        self.message = message
        super().__init__(f"[{error_code}] {message}")


class CalibrationErrorCode:
    MODEL_NOT_AVAILABLE = "MODEL_NOT_AVAILABLE"
    CALIBRATION_FAILED = "CALIBRATION_FAILED"
    INVALID_PREDICTIONS = "INVALID_PREDICTIONS"
    NOT_CALIBRATED = "NOT_CALIBRATED"


@dataclass
class CalibrationResult:
    success: bool
    temperature: Optional[float] = None
    ece: Optional[float] = None
    mce: Optional[float] = None
    calibration_curve: Optional[Dict[str, List[float]]] = None
    is_calibrated: bool = False
    error_code: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class TemperatureScalingResult:
    success: bool
    temperature: float = 1.0
    before_ece: Optional[float] = None
    after_ece: Optional[float] = None
    improvement: Optional[float] = None


class CalibrationMetrics:
    @staticmethod
    def expected_calibration_error(
        confidences: np.ndarray,
        accuracies: np.ndarray,
        n_bins: int = 10
    ) -> float:
        bin_edges = np.linspace(0, 1, n_bins + 1)
        ece = 0.0

        for i in range(n_bins):
            mask = (confidences >= bin_edges[i]) & (confidences < bin_edges[i + 1])
            if i == n_bins - 1:
                mask = (confidences >= bin_edges[i]) & (confidences <= bin_edges[i + 1])

            if np.sum(mask) > 0:
                bin_confidence = np.mean(confidences[mask])
                bin_accuracy = np.mean(accuracies[mask])
                bin_weight = np.sum(mask) / len(confidences)
                ece += bin_weight * np.abs(bin_confidence - bin_accuracy)

        return float(ece)

    @staticmethod
    def maximum_calibration_error(
        confidences: np.ndarray,
        accuracies: np.ndarray,
        n_bins: int = 10
    ) -> float:
        bin_edges = np.linspace(0, 1, n_bins + 1)
        max_error = 0.0

        for i in range(n_bins):
            mask = (confidences >= bin_edges[i]) & (confidences < bin_edges[i + 1])
            if i == n_bins - 1:
                mask = (confidences >= bin_edges[i]) & (confidences <= bin_edges[i + 1])

            if np.sum(mask) > 0:
                bin_confidence = np.mean(confidences[mask])
                bin_accuracy = np.mean(accuracies[mask])
                error = np.abs(bin_confidence - bin_accuracy)
                max_error = max(max_error, error)

        return float(max_error)

    @staticmethod
    def reliability_diagram_data(
        confidences: np.ndarray,
        accuracies: np.ndarray,
        n_bins: int = 10
    ) -> Dict[str, List[float]]:
        bin_edges = np.linspace(0, 1, n_bins + 1)
        mean_confidences = []
        mean_accuracies = []
        counts = []

        for i in range(n_bins):
            mask = (confidences >= bin_edges[i]) & (confidences < bin_edges[i + 1])
            if i == n_bins - 1:
                mask = (confidences >= bin_edges[i]) & (confidences <= bin_edges[i + 1])

            if np.sum(mask) > 0:
                mean_confidences.append(np.mean(confidences[mask]))
                mean_accuracies.append(np.mean(accuracies[mask]))
                counts.append(np.sum(mask))
            else:
                mean_confidences.append((bin_edges[i] + bin_edges[i + 1]) / 2)
                mean_accuracies.append(0.0)
                counts.append(0)

        return {
            "mean_confidence": mean_confidences,
            "mean_accuracy": mean_accuracies,
            "counts": counts,
            "bin_edges": bin_edges.tolist()
        }


class TemperatureScaling:
    def __init__(self):
        self.temperature = 1.0
        self.is_fitted = False

    def fit(self, logits: np.ndarray, labels: np.ndarray) -> TemperatureScalingResult:
        try:
            temperatures = np.linspace(0.5, 5.0, 50)
            best_temp = 1.0
            best_ece = float('inf')

            for temp in temperatures:
                calibrated_probs = self._apply_temperature(logits, temp)
                confidences = np.max(calibrated_probs, axis=1)
                predictions = np.argmax(calibrated_probs, axis=1)
                accuracies = (predictions == labels).astype(float)

                ece = CalibrationMetrics.expected_calibration_error(confidences, accuracies)

                if ece < best_ece:
                    best_ece = ece
                    best_temp = temp

            self.temperature = best_temp
            self.is_fitted = True

            before_ece = CalibrationMetrics.expected_calibration_error(
                np.max(self._apply_temperature(logits, 1.0), axis=1),
                (np.argmax(self._apply_temperature(logits, 1.0), axis=1) == labels).astype(float)
            )

            return TemperatureScalingResult(
                success=True,
                temperature=self.temperature,
                before_ece=before_ece,
                after_ece=best_ece,
                improvement=before_ece - best_ece
            )

        except Exception as e:
            return TemperatureScalingResult(
                success=False,
                temperature=1.0
            )

    def _apply_temperature(self, logits: np.ndarray, temperature: float) -> np.ndarray:
        scaled = logits / temperature
        exp_scaled = np.exp(scaled - np.max(scaled, axis=1, keepdims=True))
        probs = exp_scaled / np.sum(exp_scaled, axis=1, keepdims=True)
        return probs

    def transform(self, logits: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise CalibrationError(
                CalibrationErrorCode.NOT_CALIBRATED,
                "TemperatureScaling must be fitted before transform"
            )
        return self._apply_temperature(logits, self.temperature)


def calibrate_model(
    model: nn.Module,
    dataloader,
    num_classes: int = 4
) -> CalibrationResult:
    model.eval()

    all_logits = []
    all_labels = []

    try:
        with torch.no_grad():
            for inputs, labels in dataloader:
                logits = model(inputs)
                all_logits.append(logits.cpu().numpy())
                all_labels.append(labels.numpy())

        logits = np.concatenate(all_logits, axis=0)
        labels = np.concatenate(all_labels, axis=0)

        calibrator = TemperatureScaling()
        result = calibrator.fit(logits, labels)

        calibrated_probs = calibrator.transform(logits)
        confidences = np.max(calibrated_probs, axis=1)
        predictions = np.argmax(calibrated_probs, axis=1)
        accuracies = (predictions == labels).astype(float)

        ece = CalibrationMetrics.expected_calibration_error(confidences, accuracies)
        mce = CalibrationMetrics.maximum_calibration_error(confidences, accuracies)

        reliability_data = CalibrationMetrics.reliability_diagram_data(confidences, accuracies)

        return CalibrationResult(
            success=True,
            temperature=result.temperature,
            ece=ece,
            mce=mce,
            calibration_curve=reliability_data,
            is_calibrated=True
        )

    except Exception as e:
        return CalibrationResult(
            success=False,
            is_calibrated=False,
            error_code=CalibrationErrorCode.CALIBRATION_FAILED,
            error_message=str(e)
        )


def check_calibration_available(model_available: bool, model_trained: bool) -> Tuple[bool, str]:
    if not model_available:
        return False, "MODEL_NOT_AVAILABLE"
    if not model_trained:
        return False, "MODEL_NOT_TRAINED"
    return True, "CALIBRATION_AVAILABLE"
