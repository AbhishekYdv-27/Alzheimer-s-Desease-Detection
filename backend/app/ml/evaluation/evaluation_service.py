#!/usr/bin/env python3

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
    roc_curve,
    auc
)
from sklearn.preprocessing import label_binarize

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


class EvaluationError(Exception):
    def __init__(self, error_code: str, message: str):
        self.error_code = error_code
        self.message = message
        super().__init__(f"[{error_code}] {message}")


class EvaluationErrorCode:
    INVALID_PREDICTIONS = "INVALID_PREDICTIONS"
    INVALID_LABELS = "INVALID_LABELS"
    DIMENSION_MISMATCH = "DIMENSION_MISMATCH"
    EVALUATION_FAILED = "EVALUATION_FAILED"


ALZHEIMER_CLASSES = ["NonDemented", "VeryMildDemented", "MildDemented", "ModerateDemented"]


@dataclass
class EvaluationMetrics:
    accuracy: float
    precision_macro: float
    recall_macro: float
    f1_macro: float
    precision_weighted: float
    recall_weighted: float
    f1_weighted: float
    per_class_precision: Dict[str, float]
    per_class_recall: Dict[str, float]
    per_class_f1: Dict[str, float]
    confusion_matrix: np.ndarray
    classification_report: str
    per_class_roc_curve: Optional[Dict[str, Tuple[np.ndarray, np.ndarray, float]]] = None
    ece: Optional[float] = None
    mce: Optional[float] = None


@dataclass
class EvaluationResult:
    success: bool
    metrics: Optional[EvaluationMetrics] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class ComparisonResult:
    model_name: str
    model_version: str
    experiment_id: str
    training_status: str
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    macro_f1: Optional[float] = None
    weighted_f1: Optional[float] = None
    dataset_version: str = ""
    created_date: str = ""


class EvaluationService:
    def __init__(self, class_names: List[str] = None):
        self.class_names = class_names or ALZHEIMER_CLASSES
        self.num_classes = len(self.class_names)

    def validate_inputs(
        self,
        predictions: np.ndarray,
        labels: np.ndarray
    ) -> Tuple[bool, str]:
        if len(predictions) == 0:
            return False, "Empty predictions array"
        if len(labels) == 0:
            return False, "Empty labels array"
        if len(predictions) != len(labels):
            return False, f"Length mismatch: {len(predictions)} predictions vs {len(labels)} labels"
        return True, "Valid"

    def compute_per_class_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]:
        precision = precision_score(y_true, y_pred, average=None, zero_division=0)
        recall = recall_score(y_true, y_pred, average=None, zero_division=0)
        f1 = f1_score(y_true, y_pred, average=None, zero_division=0)

        per_class_precision = {cls: float(precision[i]) for i, cls in enumerate(self.class_names)}
        per_class_recall = {cls: float(recall[i]) for i, cls in enumerate(self.class_names)}
        per_class_f1 = {cls: float(f1[i]) for i, cls in enumerate(self.class_names)}

        return per_class_precision, per_class_recall, per_class_f1

    def compute_roc_curves(
        self,
        y_true: np.ndarray,
        y_probabilities: np.ndarray
    ) -> Optional[Dict[str, Tuple[np.ndarray, np.ndarray, float]]]:
        if y_probabilities.shape[1] != self.num_classes:
            return None

        try:
            y_true_bin = label_binarize(y_true, classes=range(self.num_classes))

            roc_curves = {}
            for i, cls in enumerate(self.class_names):
                fpr, tpr, _ = roc_curve(y_true_bin[:, i], y_probabilities[:, i])
                roc_auc = auc(fpr, tpr)
                roc_curves[cls] = (fpr, tpr, roc_auc)

            return roc_curves
        except Exception:
            return None

    def evaluate(
        self,
        predictions: np.ndarray,
        labels: np.ndarray,
        probabilities: Optional[np.ndarray] = None
    ) -> EvaluationResult:
        valid, msg = self.validate_inputs(predictions, labels)
        if not valid:
            return EvaluationResult(
                success=False,
                error_code=EvaluationErrorCode.INVALID_PREDICTIONS,
                error_message=msg
            )

        try:
            accuracy = float(accuracy_score(labels, predictions))

            precision_macro = float(precision_score(labels, predictions, average='macro', zero_division=0))
            recall_macro = float(recall_score(labels, predictions, average='macro', zero_division=0))
            f1_macro = float(f1_score(labels, predictions, average='macro', zero_division=0))

            precision_weighted = float(precision_score(labels, predictions, average='weighted', zero_division=0))
            recall_weighted = float(recall_score(labels, predictions, average='weighted', zero_division=0))
            f1_weighted = float(f1_score(labels, predictions, average='weighted', zero_division=0))

            per_class_precision, per_class_recall, per_class_f1 = self.compute_per_class_metrics(
                labels, predictions
            )

            conf_matrix = confusion_matrix(labels, predictions)

            report = classification_report(
                labels, predictions,
                target_names=self.class_names,
                zero_division=0
            )

            roc_curves = None
            if probabilities is not None:
                roc_curves = self.compute_roc_curves(labels, probabilities)

            metrics = EvaluationMetrics(
                accuracy=accuracy,
                precision_macro=precision_macro,
                recall_macro=recall_macro,
                f1_macro=f1_macro,
                precision_weighted=precision_weighted,
                recall_weighted=recall_weighted,
                f1_weighted=f1_weighted,
                per_class_precision=per_class_precision,
                per_class_recall=per_class_recall,
                per_class_f1=per_class_f1,
                confusion_matrix=conf_matrix,
                classification_report=report,
                per_class_roc_curve=roc_curves
            )

            return EvaluationResult(success=True, metrics=metrics)

        except Exception as e:
            return EvaluationResult(
                success=False,
                error_code=EvaluationErrorCode.EVALUATION_FAILED,
                error_message=str(e)
            )

    def evaluate_from_torch(
        self,
        model: nn.Module,
        dataloader,
        device: Optional[torch.device] = None
    ) -> EvaluationResult:
        if device is None:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        model.eval()

        all_predictions = []
        all_labels = []
        all_probabilities = []

        try:
            with torch.no_grad():
                for inputs, labels in dataloader:
                    inputs = inputs.to(device)
                    logits = model(inputs)
                    probs = torch.softmax(logits, dim=1)

                    all_predictions.extend(logits.argmax(dim=1).cpu().numpy())
                    all_labels.extend(labels.numpy())
                    all_probabilities.extend(probs.cpu().numpy())

            predictions = np.array(all_predictions)
            labels = np.array(all_labels)
            probabilities = np.array(all_probabilities)

            return self.evaluate(predictions, labels, probabilities)

        except Exception as e:
            return EvaluationResult(
                success=False,
                error_code=EvaluationErrorCode.EVALUATION_FAILED,
                error_message=str(e)
            )


def compare_models(
    model_results: List[ComparisonResult]
) -> List[ComparisonResult]:
    return sorted(
        model_results,
        key=lambda x: (x.macro_f1 or 0, x.accuracy or 0),
        reverse=True
    )


def format_comparison_table(comparisons: List[ComparisonResult]) -> str:
    if not comparisons:
        return "No models available for comparison"

    header = f"{'Model':<20} {'Version':<10} {'Status':<15} {'Accuracy':<10} {'Macro F1':<10} {'Weighted F1':<12}"
    separator = "-" * len(header)

    lines = [header, separator]

    for result in comparisons:
        acc = f"{result.accuracy:.4f}" if result.accuracy else "N/A"
        f1 = f"{result.macro_f1:.4f}" if result.macro_f1 else "N/A"
        wf1 = f"{result.weighted_f1:.4f}" if result.weighted_f1 else "N/A"

        lines.append(
            f"{result.model_name:<20} {result.model_version:<10} "
            f"{result.training_status:<15} {acc:<10} {f1:<10} {wf1:<12}"
        )

    return "\n".join(lines)
