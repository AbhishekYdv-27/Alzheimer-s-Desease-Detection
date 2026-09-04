"""Validate a local four-class MRI dataset before running model evaluation.

This script reports coverage only. It never creates synthetic clinical samples
or treats a missing class as validated.
"""
from pathlib import Path

CLASSES = ("NonDemented", "VeryMildDemented", "MildDemented", "ModerateDemented")
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def main() -> int:
    root = Path(__file__).resolve().parents[1] / "data" / "raw"
    missing = []
    print(f"Dataset root: {root}")
    for class_name in CLASSES:
        class_dir = root / class_name
        samples = [path for path in class_dir.rglob("*") if path.suffix.lower() in IMAGE_SUFFIXES] if class_dir.exists() else []
        print(f"{class_name}: {len(samples)} image(s)")
        if not samples:
            missing.append(class_name)
    if missing:
        print("Validation blocked; missing samples for: " + ", ".join(missing))
        return 2
    print("All four classes have local image samples. Run the model evaluation workflow next.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
