from dataclasses import dataclass
import logging
from pathlib import Path
import tempfile
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from backend.app.core.config import settings
from backend.app.ml.models.checkpoint_integrity import (
    checkpoint_sha256_matches,
    normalize_sha256,
)
from backend.app.ml.registry import ModelRegistry

logger = logging.getLogger(__name__)
MAX_CHECKPOINT_BYTES = 1024 * 1024 * 1024
DOWNLOAD_TIMEOUT_SECONDS = 45
DOWNLOAD_CHUNK_BYTES = 8 * 1024 * 1024


@dataclass(frozen=True)
class CheckpointProvisionStatus:
    available: bool
    code: str


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        return None


def _matches_expected_digest(path: Path, expected: str) -> bool:
    try:
        return checkpoint_sha256_matches(path, expected)
    except OSError:
        return False


def _download_checkpoint(url: str, token: str, expected: str, destination: Path) -> bool:
    parsed_url = urlsplit(url)
    if (
        parsed_url.scheme != "https"
        or not parsed_url.hostname
        or parsed_url.username
        or parsed_url.password
        or parsed_url.fragment
    ):
        return False

    request = Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/octet-stream",
            "User-Agent": "alzheimers-model-provisioner/1.0",
        },
    )
    temporary_path: Path | None = None
    digest_bytes = 0
    import hashlib

    digest = hashlib.sha256()
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with build_opener(_NoRedirectHandler).open(
            request,
            timeout=DOWNLOAD_TIMEOUT_SECONDS,
        ) as response:
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_CHECKPOINT_BYTES:
                return False
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=destination.parent,
                prefix=f".{destination.name}.",
                suffix=".download",
                delete=False,
            ) as temp_file:
                temporary_path = Path(temp_file.name)
                while True:
                    chunk = response.read(DOWNLOAD_CHUNK_BYTES)
                    if not chunk:
                        break
                    digest_bytes += len(chunk)
                    if digest_bytes > MAX_CHECKPOINT_BYTES:
                        return False
                    digest.update(chunk)
                    temp_file.write(chunk)

        if digest.hexdigest() != expected:
            return False
        temporary_path.replace(destination)
        temporary_path = None
        return True
    except (HTTPError, URLError, TimeoutError, OSError, ValueError):
        return False
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def provision_model_checkpoint() -> CheckpointProvisionStatus:
    registry = ModelRegistry()
    metadata = registry.get_model("ResNet50", "1.0")
    if metadata is None:
        return CheckpointProvisionStatus(False, "MODEL_NOT_REGISTERED")

    destination = registry.resolve_model_path(metadata)
    artifact_url = (settings.model_artifact_url or "").strip()
    artifact_token = (settings.model_artifact_token or "").strip()
    expected_digest = normalize_sha256(settings.model_checkpoint_sha256)
    production = settings.app_env.strip().lower() in {"production", "prod"}

    if settings.model_checkpoint_sha256 and expected_digest is None:
        return CheckpointProvisionStatus(False, "MODEL_CHECKSUM_INVALID")
    if production and expected_digest is None:
        return CheckpointProvisionStatus(False, "MODEL_CHECKSUM_REQUIRED")
    if bool(artifact_url) != bool(artifact_token):
        return CheckpointProvisionStatus(False, "MODEL_ARTIFACT_CONFIGURATION_INVALID")
    if artifact_url and expected_digest is None:
        return CheckpointProvisionStatus(False, "MODEL_ARTIFACT_CONFIGURATION_INVALID")

    if destination.is_file():
        if expected_digest is None or _matches_expected_digest(destination, expected_digest):
            return CheckpointProvisionStatus(True, "MODEL_CHECKPOINT_AVAILABLE")
        if not artifact_url:
            return CheckpointProvisionStatus(False, "MODEL_CHECKSUM_MISMATCH")

    if not artifact_url:
        return CheckpointProvisionStatus(False, "MODEL_FILE_NOT_FOUND")
    if not _download_checkpoint(artifact_url, artifact_token, expected_digest, destination):
        logger.warning("Model checkpoint provisioning failed; inference will be unavailable")
        return CheckpointProvisionStatus(False, "MODEL_ARTIFACT_PROVISION_FAILED")
    return CheckpointProvisionStatus(True, "MODEL_CHECKPOINT_PROVISIONED")
