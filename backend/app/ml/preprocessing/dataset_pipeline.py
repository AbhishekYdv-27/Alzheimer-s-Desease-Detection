#!/usr/bin/env python3

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import csv
import json
import os
from PIL import Image
import torch
from torch.utils.data import Dataset


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


class DatasetSplit(Enum):
    TRAIN = "train"
    VAL = "val"
    TEST = "test"
    ALL = "all"


ALZHEIMER_CLASSES = ["NonDemented", "VeryMildDemented", "MildDemented", "ModerateDemented"]

ALZHEIMER_CLASS_TO_IDX = {cls: idx for idx, cls in enumerate(ALZHEIMER_CLASSES)}

ALZHEIMER_IDX_TO_CLASS = {idx: cls for idx, cls in enumerate(ALZHEIMER_CLASSES)}


class ImageFormat(Enum):
    JPEG = "jpeg"
    JPG = "jpg"
    PNG = "png"
    BMP = "bmp"
    TIFF = "tiff"
    UNKNOWN = "unknown"


SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}


@dataclass
class DatasetConfig:
    data_root: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "raw")
    output_root: Path = field(default_factory=lambda: PROJECT_ROOT / "data")
    metadata_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "metadata")
    splits_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "splits")
    models_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "models")
    image_size: Tuple[int, int] = (224, 224)
    batch_size: int = 32
    num_workers: int = 4
    validation_split: float = 0.15
    test_split: float = 0.15
    random_seed: int = 42
    class_names: List[str] = field(default_factory=lambda: ALZHEIMER_CLASSES.copy())
    supported_formats: List[str] = field(default_factory=lambda: [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"])

    def __post_init__(self):
        self.data_root = Path(self.data_root)
        self.output_root = Path(self.output_root)
        self.metadata_dir = Path(self.metadata_dir)
        self.splits_dir = Path(self.splits_dir)
        self.models_dir = Path(self.models_dir)


@dataclass
class DatasetMetadata:
    total_images: int = 0
    class_distribution: Dict[str, int] = field(default_factory=dict)
    image_formats: Dict[str, int] = field(default_factory=dict)
    image_dimensions: Dict[str, int] = field(default_factory=dict)
    corrupted_images: List[str] = field(default_factory=list)
    missing_labels: List[str] = field(default_factory=list)
    dataset_version: str = "1.0"
    generated_date: str = ""
    data_root: str = ""


@dataclass
class SplitMetadata:
    split_name: str = ""
    num_samples: int = 0
    class_distribution: Dict[str, int] = field(default_factory=dict)
    file_path: str = ""


@dataclass
class ImageRecord:
    image_id: str
    file_path: str
    class_name: str
    class_index: int
    file_size: int
    image_format: str
    width: int
    height: int
    is_valid: bool
    validation_message: str = ""


def get_image_format(file_path: str) -> ImageFormat:
    ext = Path(file_path).suffix.lower()
    format_map = {
        ".jpeg": ImageFormat.JPEG,
        ".jpg": ImageFormat.JPEG,
        ".png": ImageFormat.PNG,
        ".bmp": ImageFormat.BMP,
        ".tiff": ImageFormat.TIFF,
        ".tif": ImageFormat.TIFF,
    }
    return format_map.get(ext, ImageFormat.UNKNOWN)


def validate_image_file(file_path: str) -> Tuple[bool, str, Optional[Dict]]:
    try:
        if not os.path.exists(file_path):
            return False, "File does not exist", None

        if not os.path.isfile(file_path):
            return False, "Path is not a file", None

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return False, "File is empty", None

        ext = Path(file_path).suffix.lower()
        if ext not in SUPPORTED_IMAGE_EXTENSIONS:
            return False, f"Unsupported file format: {ext}", None

        with Image.open(file_path) as img:
            width, height = img.size
            img_format = img.format

            if width < 16 or height < 16:
                return False, f"Image too small: {width}x{height}", None

            img.verify()

        with Image.open(file_path) as img:
            width, height = img.size
            mode = img.mode

        return True, "Valid", {
            "width": width,
            "height": height,
            "format": img_format,
            "mode": mode,
            "file_size": file_size
        }
    except Exception as e:
        return False, f"Validation error: {str(e)}", None


def discover_images(data_root: Path, class_names: List[str]) -> Dict[str, List[str]]:
    discovered = {cls: [] for cls in class_names}

    for class_name in class_names:
        class_dir = data_root / class_name
        if not class_dir.exists():
            continue

        for file_path in class_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
                discovered[class_name].append(str(file_path))

    return discovered


def generate_image_id(file_path: str, index: int) -> str:
    return f"img_{index:06d}_{Path(file_path).stem}"


class DatasetValidator:
    def __init__(self, config: DatasetConfig):
        self.config = config
        self.errors = []
        self.warnings = []

    def validate_structure(self) -> bool:
        valid = True

        if not self.config.data_root.exists():
            self.errors.append(f"Data root does not exist: {self.config.data_root}")
            valid = False

        for class_name in self.config.class_names:
            class_dir = self.config.data_root / class_name
            if not class_dir.exists():
                self.warnings.append(f"Class directory missing: {class_name}")

        return valid

    def validate_images(self, max_images: Optional[int] = None) -> Dict:
        discovered = discover_images(self.config.data_root, self.config.class_names)

        all_images = []
        for class_name, paths in discovered.items():
            for path in paths:
                all_images.append({"path": path, "class_name": class_name})

        if max_images is not None and len(all_images) > max_images:
            import random
            random.seed(self.config.random_seed)
            all_images = random.sample(all_images, max_images)

        results = {
            "total_checked": len(all_images),
            "valid": 0,
            "invalid": 0,
            "corrupted": [],
            "format_distribution": {},
            "dimension_distribution": {}
        }

        for record in all_images:
            is_valid, message, details = validate_image_file(record["path"])

            if is_valid:
                results["valid"] += 1
                if details:
                    fmt = details.get("format", "unknown")
                    results["format_distribution"][fmt] = results["format_distribution"].get(fmt, 0) + 1

                    dim_key = f"{details['width']}x{details['height']}"
                    results["dimension_distribution"][dim_key] = results["dimension_distribution"].get(dim_key, 0) + 1
            else:
                results["invalid"] += 1
                results["corrupted"].append({
                    "path": record["path"],
                    "class_name": record["class_name"],
                    "error": message
                })

        return results


def generate_dataset_metadata(config: DatasetConfig) -> DatasetMetadata:
    discovered = discover_images(config.data_root, config.class_names)

    metadata = DatasetMetadata()
    metadata.data_root = str(config.data_root)

    total = 0
    all_valid_images = []

    for class_name, paths in discovered.items():
        metadata.class_distribution[class_name] = len(paths)
        total += len(paths)

        for path in paths:
            is_valid, message, details = validate_image_file(path)
            record = ImageRecord(
                image_id=generate_image_id(path, len(all_valid_images)),
                file_path=path,
                class_name=class_name,
                class_index=ALZHEIMER_CLASS_TO_IDX.get(class_name, -1),
                file_size=details.get("file_size", 0) if details else 0,
                image_format=details.get("format", "unknown") if details else "unknown",
                width=details.get("width", 0) if details else 0,
                height=details.get("height", 0) if details else 0,
                is_valid=is_valid,
                validation_message=message
            )
            all_valid_images.append(record)

            if not is_valid:
                metadata.corrupted_images.append(path)

    metadata.total_images = total

    return metadata


def save_metadata_csv(records: List[ImageRecord], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "image_id", "file_path", "class_name", "class_index",
            "file_size", "image_format", "width", "height", "is_valid", "validation_message"
        ])

        for record in records:
            writer.writerow([
                record.image_id,
                record.file_path,
                record.class_name,
                record.class_index,
                record.file_size,
                record.image_format,
                record.width,
                record.height,
                record.is_valid,
                record.validation_message
            ])


def save_metadata_json(metadata: DatasetMetadata, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "total_images": metadata.total_images,
            "class_distribution": metadata.class_distribution,
            "image_formats": metadata.image_formats,
            "image_dimensions": metadata.image_dimensions,
            "corrupted_images": metadata.corrupted_images,
            "missing_labels": metadata.missing_labels,
            "dataset_version": metadata.dataset_version,
            "generated_date": metadata.generated_date,
            "data_root": metadata.data_root
        }, f, indent=2)


def create_stratified_split(
    image_records: List[ImageRecord],
    val_split: float,
    test_split: float,
    random_seed: int
) -> Tuple[List[ImageRecord], List[ImageRecord], List[ImageRecord]]:
    from collections import defaultdict

    by_class = defaultdict(list)
    for record in image_records:
        if record.is_valid:
            by_class[record.class_name].append(record)

    train_records = []
    val_records = []
    test_records = []

    import random
    random.seed(random_seed)

    for class_name, records in by_class.items():
        random.shuffle(records)

        n = len(records)
        n_val = int(n * val_split)
        n_test = int(n * test_split)

        test_records.extend(records[:n_test])
        val_records.extend(records[n_test:n_test + n_val])
        train_records.extend(records[n_test + n_val:])

    return train_records, val_records, test_records


def detect_leakage(
    all_records: List[ImageRecord],
    split_records: Dict[str, List[ImageRecord]]
) -> Dict:
    leakage_report = {
        "leakage_detected": False,
        "issues": [],
        "by_class": {}
    }

    all_paths = set(r.file_path for r in all_records)

    for class_name in ALZHEIMER_CLASSES:
        class_records = [r for r in all_records if r.class_name == class_name]
        split_paths = {
            split_name: set(r.file_path for r in records if r.class_name == class_name)
            for split_name, records in split_records.items()
        }

        duplicates = []
        for i, split_a in enumerate(["train", "val", "test"]):
            for split_b in list(["train", "val", "test"])[i+1:]:
                common = split_paths[split_a] & split_paths[split_b]
                if common:
                    duplicates.append({
                        "between": f"{split_a}-{split_b}",
                        "count": len(common),
                        "examples": list(common)[:5]
                    })

        if duplicates:
            leakage_report["leakage_detected"] = True
            leakage_report["by_class"][class_name] = duplicates

    return leakage_report


class AlzheimerMRIDataset(Dataset):
    def __init__(
        self,
        image_records: List[ImageRecord],
        transform=None,
        target_size: Tuple[int, int] = (224, 224)
    ):
        self.image_records = [r for r in image_records if r.is_valid]
        self.transform = transform
        self.target_size = target_size

    def __len__(self) -> int:
        return len(self.image_records)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        record = self.image_records[idx]

        try:
            image = Image.open(record.file_path).convert("RGB")
            image = image.resize(self.target_size, Image.BILINEAR)

            if self.transform:
                image = self.transform(image)
            else:
                image = torch.from_numpy(
                    torch.ByteTensor(torch.ByteStorage.from_buffer(image.tobytes()))
                ).view(image.size[1], image.size[0], 3).permute(2, 0, 1).float() / 255.0

            return image, record.class_index
        except Exception:
            dummy_image = torch.zeros(3, self.target_size[0], self.target_size[1])
            return dummy_image, record.class_index


def get_class_distribution(records: List[ImageRecord]) -> Dict[str, int]:
    dist = {cls: 0 for cls in ALZHEIMER_CLASSES}
    for record in records:
        if record.class_name in dist:
            dist[record.class_name] += 1
    return dist
