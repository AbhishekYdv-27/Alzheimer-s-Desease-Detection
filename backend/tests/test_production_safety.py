import asyncio
import hashlib
from datetime import datetime, timedelta, timezone
from io import BytesIO
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

import pytest
import torch
from fastapi import HTTPException, UploadFile
from fastapi.testclient import TestClient
from PIL import Image

from backend.app.core import uploads
from backend.app.core.config import settings
from backend.app.core import database
from backend.app.core.doctor_provisioning import provision_verified_doctor
from backend.app.core.database import get_db
from backend.app.ml.models import checkpoint_provisioning
from backend.app.ml.models.model_loader import ModelLoader
from backend.app.ml.registry import ModelRegistry
from backend.app import main
from backend.app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "isolated.sqlite3")
    with TestClient(app) as test_client:
        yield test_client


def png_bytes(width=8, height=8):
    image = Image.new("RGB", (width, height), color=(20, 40, 60))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def upload_from(content, filename="mri.png", content_type="image/png"):
    return UploadFile(
        filename=filename,
        file=BytesIO(content),
        headers={"content-type": content_type},
    )


def test_upload_validation_uses_image_bytes_and_cleans_temp_file():
    path = asyncio.run(
        uploads.save_validated_upload(
            upload_from(png_bytes(), filename="scan.exe", content_type="application/octet-stream")
        )
    )
    try:
        with Image.open(path) as image:
            assert image.format == "PNG"
            assert image.size == (8, 8)
    finally:
        Path(path).unlink(missing_ok=True)


def test_upload_validation_rejects_invalid_and_oversized_images(monkeypatch):
    with pytest.raises(HTTPException) as invalid:
        asyncio.run(uploads.save_validated_upload(upload_from(b"not an image")))
    assert invalid.value.status_code == 400

    monkeypatch.setattr(uploads, "MAX_UPLOAD_SIZE_BYTES", 16)
    with pytest.raises(HTTPException) as oversized:
        asyncio.run(uploads.save_validated_upload(upload_from(png_bytes())))
    assert oversized.value.status_code == 413


def test_prediction_and_explain_routes_require_authentication(client):
    for path in ("/api/predict", "/api/explain"):
        response = client.post(
            path,
            files={"file": ("mri.png", png_bytes(), "image/png")},
            data={"model_name": "ResNet50"},
        )
        assert response.status_code == 401


def test_authentication_registration_login_and_invalid_password(client):
    credentials = {
        "name": "Authentication Test",
        "email": f"auth-{uuid4().hex}@example.com",
        "password": "secure-test-password",
    }
    registration = client.post("/api/auth/register", json=credentials)
    assert registration.status_code == 200

    login = client.post(
        "/api/auth/login",
        json={"email": credentials["email"], "password": credentials["password"]},
    )
    assert login.status_code == 200
    assert login.json()["access_token"]

    invalid_login = client.post(
        "/api/auth/login",
        json={"email": credentials["email"], "password": "incorrect-password"},
    )
    assert invalid_login.status_code == 401
    assert invalid_login.json()["detail"] == "Invalid email or password"


def test_authentication_timestamps_are_timezone_aware_utc(client):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "UTC Timestamp Test",
            "email": f"utc-{uuid4().hex}@example.com",
            "password": "secure-test-password",
        },
    )
    assert response.status_code == 200

    for field in ("created_at", "updated_at"):
        value = datetime.fromisoformat(response.json()["user"][field])
        assert value.utcoffset() == timedelta(0)
        assert value.tzinfo == timezone.utc


def test_public_registration_cannot_assign_doctor_role(client):
    credentials = {
        "name": "Unverified Doctor",
        "email": f"unverified-{uuid4().hex}@example.com",
        "password": "secure-test-password",
        "role": "doctor",
    }
    response = client.post("/api/auth/register", json=credentials)
    assert response.status_code == 422
    assert database.get_user_by_email(credentials["email"]) is None


def test_patient_cannot_escalate_role_through_profile_update(client):
    registered = client.post(
        "/api/auth/register",
        json={
            "name": "Patient Role",
            "email": f"role-{uuid4().hex}@example.com",
            "password": "secure-test-password",
        },
    ).json()
    response = client.patch(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {registered['access_token']}"},
        json={"name": "Patient Role", "role": "doctor"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == "patient"


def test_privileged_doctor_provisioning_records_review(client):
    email = f"verified-{uuid4().hex}@example.com"
    doctor = provision_verified_doctor(
        name="Verified Doctor",
        email=email,
        password="temporary-doctor-password",
        provisioned_by="test-operator",
        verification_method="professional register review",
    )

    connection = get_db()
    try:
        audit = connection.execute(
            "SELECT provisioned_by, verification_method FROM doctor_provisioning_audit WHERE doctor_id = ?",
            (doctor["id"],),
        ).fetchone()
        profile = connection.execute(
            "SELECT user_id FROM doctor_profiles WHERE user_id = ?",
            (doctor["id"],),
        ).fetchone()
    finally:
        connection.close()

    assert doctor["role"] == "doctor"
    assert audit["provisioned_by"] == "test-operator"
    assert audit["verification_method"] == "professional register review"
    assert profile is not None


def test_invalid_bearer_token_is_rejected(client):
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )
    assert response.status_code == 401


def test_analysis_and_report_access_is_limited_to_owner(client):
    owner_response = client.post(
        "/api/auth/register",
        json={
            "name": "Record Owner",
            "email": f"owner-{uuid4().hex}@example.com",
            "password": "secure-test-password",
        },
    )
    other_response = client.post(
        "/api/auth/register",
        json={
            "name": "Other User",
            "email": f"other-{uuid4().hex}@example.com",
            "password": "secure-test-password",
        },
    )
    owner = owner_response.json()
    other = other_response.json()
    owner_headers = {"Authorization": f"Bearer {owner['access_token']}"}
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}
    saved = client.post(
        "/api/analysis/records",
        headers=owner_headers,
        json={
            "user_id": owner["user"]["id"],
            "image_name": "isolated-test.png",
            "model_name": "ResNet50",
            "predicted_class": "NonDemented",
            "confidence": 0.5,
        },
    )
    record_id = saved.json()["id"]

    assert client.get(f"/api/analysis/records/{record_id}", headers=owner_headers).status_code == 200
    assert client.get(f"/api/analysis/records/{record_id}", headers=other_headers).status_code == 404
    assert client.get(f"/api/reports/analysis/{record_id}", headers=other_headers).status_code == 404
    assert client.get(
        f"/api/reports/analysis/{record_id}/download",
        headers=other_headers,
    ).status_code == 404


def test_model_checkpoint_provisioning_downloads_and_verifies_digest(tmp_path, monkeypatch):
    payload = b"private-model-artifact"
    digest = hashlib.sha256(payload).hexdigest()
    destination = tmp_path / "models" / "checkpoint.pth"
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "model_checkpoint_path", str(destination))
    monkeypatch.setattr(settings, "model_checkpoint_sha256", digest)
    monkeypatch.setattr(settings, "model_artifact_url", "https://models.example.test/checkpoint")
    monkeypatch.setattr(settings, "model_artifact_token", "test-artifact-token")

    class Response:
        headers = {"Content-Length": str(len(payload))}

        def __init__(self):
            self.stream = BytesIO(payload)

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self, size):
            return self.stream.read(size)

    class Opener:
        def open(self, request, timeout):
            assert request.full_url == "https://models.example.test/checkpoint"
            assert request.get_header("Authorization") == "Bearer test-artifact-token"
            assert timeout == checkpoint_provisioning.DOWNLOAD_TIMEOUT_SECONDS
            return Response()

    monkeypatch.setattr(
        checkpoint_provisioning,
        "build_opener",
        lambda *_: Opener(),
    )
    result = checkpoint_provisioning.provision_model_checkpoint()

    assert result.available
    assert result.code == "MODEL_CHECKPOINT_PROVISIONED"
    assert destination.read_bytes() == payload


def test_model_checkpoint_provisioning_fails_safely_without_integrity_config(tmp_path, monkeypatch):
    destination = tmp_path / "missing.pth"
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "model_checkpoint_path", str(destination))
    monkeypatch.setattr(settings, "model_checkpoint_sha256", None)
    monkeypatch.setattr(settings, "model_artifact_url", None)
    monkeypatch.setattr(settings, "model_artifact_token", None)

    result = checkpoint_provisioning.provision_model_checkpoint()
    assert not result.available
    assert result.code == "MODEL_CHECKSUM_REQUIRED"


def test_model_checkpoint_provisioning_rejects_invalid_checksum(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "model_checkpoint_path", str(tmp_path / "missing.pth"))
    monkeypatch.setattr(settings, "model_checkpoint_sha256", "not-a-sha256")
    monkeypatch.setattr(settings, "model_artifact_url", None)
    monkeypatch.setattr(settings, "model_artifact_token", None)

    result = checkpoint_provisioning.provision_model_checkpoint()
    assert not result.available
    assert result.code == "MODEL_CHECKSUM_INVALID"


def test_model_checkpoint_provisioning_rejects_non_https_artifact_url(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "model_checkpoint_path", str(tmp_path / "model.pth"))
    monkeypatch.setattr(settings, "model_checkpoint_sha256", hashlib.sha256(b"model").hexdigest())
    monkeypatch.setattr(settings, "model_artifact_url", "http://models.example.test/model.pth")
    monkeypatch.setattr(settings, "model_artifact_token", "test-artifact-token")
    monkeypatch.setattr(
        checkpoint_provisioning,
        "build_opener",
        lambda *_: pytest.fail("Insecure artifact URLs must be rejected before network access"),
    )

    result = checkpoint_provisioning.provision_model_checkpoint()
    assert not result.available
    assert result.code == "MODEL_ARTIFACT_PROVISION_FAILED"
    assert not (tmp_path / "model.pth").exists()


def test_model_checkpoint_provisioning_reports_unavailable_artifact(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "model_checkpoint_path", str(tmp_path / "missing.pth"))
    monkeypatch.setattr(settings, "model_checkpoint_sha256", hashlib.sha256(b"model").hexdigest())
    monkeypatch.setattr(settings, "model_artifact_url", "https://models.example.test/model.pth")
    monkeypatch.setattr(settings, "model_artifact_token", "test-artifact-token")

    class Opener:
        def open(self, request, timeout):
            raise checkpoint_provisioning.URLError("artifact host unavailable")

    monkeypatch.setattr(checkpoint_provisioning, "build_opener", lambda *_: Opener())
    result = checkpoint_provisioning.provision_model_checkpoint()

    assert not result.available
    assert result.code == "MODEL_ARTIFACT_PROVISION_FAILED"
    assert not (tmp_path / "missing.pth").exists()


def test_model_checkpoint_digest_mismatch_preserves_existing_file(tmp_path, monkeypatch):
    destination = tmp_path / "model.pth"
    destination.write_bytes(b"previous-valid-file")
    payload = b"untrusted-download"
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "model_checkpoint_path", str(destination))
    monkeypatch.setattr(settings, "model_checkpoint_sha256", hashlib.sha256(b"expected").hexdigest())
    monkeypatch.setattr(settings, "model_artifact_url", "https://models.example.test/model.pth")
    monkeypatch.setattr(settings, "model_artifact_token", "test-artifact-token")

    class Response:
        headers = {"Content-Length": str(len(payload))}

        def __init__(self):
            self.stream = BytesIO(payload)

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self, size):
            return self.stream.read(size)

    class Opener:
        def open(self, request, timeout):
            return Response()

    monkeypatch.setattr(checkpoint_provisioning, "build_opener", lambda *_: Opener())
    result = checkpoint_provisioning.provision_model_checkpoint()

    assert not result.available
    assert result.code == "MODEL_ARTIFACT_PROVISION_FAILED"
    assert destination.read_bytes() == b"previous-valid-file"
    assert list(tmp_path.glob("*.download")) == []


def test_model_checkpoint_provisioning_rejects_oversized_artifact(tmp_path, monkeypatch):
    payload = b"model-too-large"
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "model_checkpoint_path", str(tmp_path / "model.pth"))
    monkeypatch.setattr(settings, "model_checkpoint_sha256", hashlib.sha256(payload).hexdigest())
    monkeypatch.setattr(settings, "model_artifact_url", "https://models.example.test/model.pth")
    monkeypatch.setattr(settings, "model_artifact_token", "test-artifact-token")
    monkeypatch.setattr(checkpoint_provisioning, "MAX_CHECKPOINT_BYTES", 4)

    class Response:
        headers = {"Content-Length": str(len(payload))}

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    class Opener:
        def open(self, request, timeout):
            return Response()

    monkeypatch.setattr(checkpoint_provisioning, "build_opener", lambda *_: Opener())
    result = checkpoint_provisioning.provision_model_checkpoint()

    assert not result.available
    assert result.code == "MODEL_ARTIFACT_PROVISION_FAILED"
    assert not (tmp_path / "model.pth").exists()


def test_model_loader_rejects_mismatched_checkpoint_labels(tmp_path, monkeypatch):
    checkpoint_path = tmp_path / "mismatched.pth"
    torch.save(
        {
            "model_state_dict": {},
            "class_names": ["Other", "Labels", "Do", "NotMatch"],
        },
        checkpoint_path,
    )
    monkeypatch.setattr(settings, "model_checkpoint_path", str(checkpoint_path))

    result = ModelLoader().load_model("ResNet50", "1.0")
    assert not result.success
    assert result.error_code == "MODEL_LOAD_FAILED"
    assert result.model is None


def test_model_loader_fails_closed_for_corrupted_checkpoint(tmp_path, monkeypatch):
    checkpoint_path = tmp_path / "corrupted.pth"
    checkpoint_path.write_bytes(b"not a PyTorch checkpoint")
    monkeypatch.setattr(settings, "model_checkpoint_path", str(checkpoint_path))
    monkeypatch.setattr(settings, "model_checkpoint_sha256", None)

    result = ModelLoader().load_model("ResNet50", "1.0")
    assert not result.success
    assert result.error_code == "MODEL_LOAD_FAILED"
    assert result.model is None


def test_missing_checkpoint_is_reported_as_unavailable(client, tmp_path, monkeypatch):
    missing_path = tmp_path / "missing.pth"
    monkeypatch.setattr(settings, "model_checkpoint_path", str(missing_path))
    status = client.get("/api/models/status")
    resnet = next(item for item in status.json()["models"] if item["model_name"] == "ResNet50")
    assert status.status_code == 200
    assert resnet["available"] is False
    assert resnet["status"] == "MODEL_FILE_NOT_FOUND"

    patient = client.post(
        "/api/auth/register",
        json={
            "name": "Analysis User",
            "email": f"analysis-{uuid4().hex}@example.com",
            "password": "secure-test-password",
        },
    ).json()
    response = client.post(
        "/api/predict",
        headers={"Authorization": f"Bearer {patient['access_token']}"},
        files={"file": ("scan.png", png_bytes(), "image/png")},
        data={"model_name": "ResNet50"},
    )
    assert response.status_code == 200
    assert response.json()["error_code"] == "MODEL_FILE_NOT_FOUND"


def test_gradcam_assets_require_authentication(client):
    owner_response = client.post(
        "/api/auth/register",
        json={
            "name": "Image Owner",
            "email": f"image-owner-{uuid4().hex}@example.com",
            "password": "secure-test-password",
        },
    )
    other_response = client.post(
        "/api/auth/register",
        json={
            "name": "Other Image User",
            "email": f"image-other-{uuid4().hex}@example.com",
            "password": "secure-test-password",
        },
    )
    owner = owner_response.json()
    other = other_response.json()
    filename = f"{owner['user']['id']}_test_heatmap.png"
    asset_path = Path(main.results_dir) / filename
    asset_path.parent.mkdir(parents=True, exist_ok=True)
    asset_path.write_bytes(png_bytes())
    try:
        assert client.get(f"/api/results/gradcam/{filename}").status_code == 401
        assert client.get(
            f"/api/results/gradcam/{filename}",
            headers={"Authorization": "Bearer invalid-token"},
        ).status_code == 401
        assert client.get(
            f"/api/results/gradcam/{filename}",
            headers={"Authorization": f"Bearer {other['access_token']}"},
        ).status_code == 404
        owner_asset = client.get(
            f"/api/results/gradcam/{filename}",
            headers={"Authorization": f"Bearer {owner['access_token']}"},
        )
        assert owner_asset.status_code == 200
        assert owner_asset.content == png_bytes()
    finally:
        asset_path.unlink(missing_ok=True)


def test_model_status_reports_checkpoint_availability(client):
    response = client.get("/api/models/status")
    assert response.status_code == 200
    registry = ModelRegistry()
    expected = {
        model.model_name: registry.validate_model_file(model.model_name, model.model_version)[0]
        for model in registry.get_all_models()
    }
    assert {
        model["model_name"]: model["available"]
        for model in response.json()["models"]
    } == expected


def test_model_registry_does_not_publish_unverified_accuracy_claims(client):
    response = client.get("/api/models/")
    assert response.status_code == 200
    resnet = next(model for model in response.json() if model["model_name"] == "ResNet50")
    assert resnet["training_status"] == "UNVERIFIED"
    assert resnet["metrics"] == {}
    assert resnet["experiment_id"] is None


def test_unverified_checkpoint_can_be_available_without_claiming_validation(tmp_path, monkeypatch):
    checkpoint_path = tmp_path / "checkpoint.pth"
    checkpoint_path.write_bytes(b"checkpoint")
    monkeypatch.setattr(settings, "model_checkpoint_path", str(checkpoint_path))
    registry = ModelRegistry()
    registry.get_model("ResNet50", "1.0").training_status = "UNVERIFIED"

    available, status, _ = registry.validate_model_file("ResNet50", "1.0")
    assert available
    assert status == "VALID"


def test_database_connections_enforce_foreign_keys():
    connection = get_db()
    try:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    finally:
        connection.close()


def test_production_database_does_not_create_demo_credentials(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "production.sqlite3")
    monkeypatch.setattr(database, "APP_ENV", "production")
    database.init_db()
    connection = database.get_db()
    try:
        assert connection.execute(
            "SELECT 1 FROM users WHERE email = ?",
            ("demo@neuroscan.ai",),
        ).fetchone() is None
    finally:
        connection.close()


def test_model_registry_resolves_relative_checkpoint_path():
    metadata = ModelRegistry().get_model("ResNet50", "1.0")
    assert metadata is not None
    assert ModelRegistry().resolve_model_path(metadata) == (
        Path(__file__).resolve().parents[2] / "backend" / "models" / "resnet50_best.pth"
    )


def test_production_rejects_missing_jwt_secret(tmp_path):
    environment = os.environ.copy()
    environment.pop("SECRET_KEY", None)
    environment["APP_ENV"] = "production"
    environment["ALZHEIMERS_DB_PATH"] = str(tmp_path / "production.sqlite3")
    environment["CORS_ORIGINS"] = "https://demo.example"
    root = Path(__file__).resolve().parents[2]
    environment["PYTHONPATH"] = str(root)

    result = subprocess.run(
        [sys.executable, "-c", "import backend.app.core.auth"],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "Production requires a SECRET_KEY" in result.stderr


def test_production_rejects_example_jwt_secret(tmp_path):
    environment = os.environ.copy()
    environment["APP_ENV"] = "production"
    environment["SECRET_KEY"] = "replace-with-a-long-random-secret"
    environment["ALZHEIMERS_DB_PATH"] = str(tmp_path / "production.sqlite3")
    environment["CORS_ORIGINS"] = "https://demo.example"
    root = Path(__file__).resolve().parents[2]
    environment["PYTHONPATH"] = str(root)

    result = subprocess.run(
        [sys.executable, "-c", "import backend.app.core.auth"],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "Production requires a SECRET_KEY" in result.stderr


def test_cors_preflight_allows_local_frontend(client):
    response = client.options(
        "/api/auth/login",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
    assert "authorization" in response.headers["access-control-allow-headers"].lower()


def test_openapi_operation_ids_are_unique():
    operations = [
        operation
        for path in app.openapi()["paths"].values()
        for operation in path.values()
        if isinstance(operation, dict) and "operationId" in operation
    ]
    operation_ids = [operation["operationId"] for operation in operations]
    assert len(operation_ids) == len(set(operation_ids))
