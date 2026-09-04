from backend.tests.test_role_security import client


def test_prediction_health_reports_readiness(client):
    response = client.get("/api/predict/health")
    assert response.status_code == 200
    assert response.json()["status"] in {"HEALTHY", "UNHEALTHY"}


def test_prediction_rejects_unsupported_media_type(client):
    response = client.post(
        "/api/predict",
        files={"file": ("notes.txt", b"not an image", "text/plain")},
        data={"model_name": "ResNet50", "model_version": "1.0"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["error_code"] == "INVALID_IMAGE"
    assert "Unsupported image format" in payload["error_message"]
