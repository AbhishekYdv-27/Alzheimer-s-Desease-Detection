import hashlib
from functools import lru_cache
from pathlib import Path
import re


def normalize_sha256(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", normalized):
        return None
    return normalized


@lru_cache(maxsize=8)
def _cached_sha256_matches(path: str, expected: str, size: int, modified_ns: int) -> bool:
    digest = hashlib.sha256()
    with Path(path).open("rb") as checkpoint:
        for chunk in iter(lambda: checkpoint.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest() == expected


def checkpoint_sha256_matches(path: Path, expected: str) -> bool:
    metadata = path.stat()
    return _cached_sha256_matches(
        str(path.resolve()),
        expected,
        metadata.st_size,
        metadata.st_mtime_ns,
    )
