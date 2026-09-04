#!/usr/bin/env python3

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import json

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


class ExperimentStatus:
    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class Experiment:
    experiment_id: str
    model_name: str
    architecture: str
    config: Dict[str, Any]
    dataset_version: str = ""
    training_status: str = ExperimentStatus.PLANNED
    metrics: Dict[str, Any] = field(default_factory=dict)
    created_date: str = ""
    started_date: str = ""
    completed_date: str = ""
    notes: str = ""
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "experiment_id": self.experiment_id,
            "model_name": self.model_name,
            "architecture": self.architecture,
            "config": self.config,
            "dataset_version": self.dataset_version,
            "training_status": self.training_status,
            "metrics": self.metrics,
            "created_date": self.created_date,
            "started_date": self.started_date,
            "completed_date": self.completed_date,
            "notes": self.notes,
            "tags": self.tags
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Experiment":
        return cls(**data)


class ExperimentTracker:
    def __init__(self, storage_path: Optional[Path] = None):
        if storage_path is None:
            storage_path = PROJECT_ROOT / "experiments" / "experiments.json"
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.experiments: Dict[str, Experiment] = {}
        self._load()

    def _load(self) -> None:
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.experiments = {
                        exp_id: Experiment.from_dict(exp_data)
                        for exp_id, exp_data in data.get("experiments", {}).items()
                    }
            except Exception:
                self.experiments = {}

    def _save(self) -> None:
        data = {
            "experiments": {
                exp_id: exp.to_dict()
                for exp_id, exp in self.experiments.items()
            },
            "last_updated": datetime.now().isoformat()
        }
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def create_experiment(
        self,
        experiment_id: str,
        model_name: str,
        architecture: str,
        config: Dict[str, Any],
        dataset_version: str = "",
        notes: str = "",
        tags: Optional[List[str]] = None
    ) -> Experiment:
        experiment = Experiment(
            experiment_id=experiment_id,
            model_name=model_name,
            architecture=architecture,
            config=config,
            dataset_version=dataset_version,
            created_date=datetime.now().isoformat(),
            notes=notes,
            tags=tags or []
        )
        self.experiments[experiment_id] = experiment
        self._save()
        return experiment

    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        return self.experiments.get(experiment_id)

    def get_all_experiments(self) -> List[Experiment]:
        return list(self.experiments.values())

    def update_experiment(
        self,
        experiment_id: str,
        status: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None
    ) -> bool:
        if experiment_id not in self.experiments:
            return False

        exp = self.experiments[experiment_id]

        if status is not None:
            exp.training_status = status
            if status == ExperimentStatus.RUNNING and not exp.started_date:
                exp.started_date = datetime.now().isoformat()
            elif status in [ExperimentStatus.COMPLETED, ExperimentStatus.FAILED]:
                exp.completed_date = datetime.now().isoformat()

        if metrics is not None:
            exp.metrics.update(metrics)

        if notes is not None:
            exp.notes = notes

        self._save()
        return True

    def delete_experiment(self, experiment_id: str) -> bool:
        if experiment_id in self.experiments:
            del self.experiments[experiment_id]
            self._save()
            return True
        return False

    def get_experiments_by_model(self, model_name: str) -> List[Experiment]:
        return [
            exp for exp in self.experiments.values()
            if exp.model_name == model_name
        ]

    def get_experiments_by_status(self, status: str) -> List[Experiment]:
        return [
            exp for exp in self.experiments.values()
            if exp.training_status == status
        ]

    def get_recent_experiments(self, limit: int = 10) -> List[Experiment]:
        sorted_exps = sorted(
            self.experiments.values(),
            key=lambda x: x.created_date,
            reverse=True
        )
        return sorted_exps[:limit]


def create_experiment_id(model_name: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{model_name.lower()}_{timestamp}"
