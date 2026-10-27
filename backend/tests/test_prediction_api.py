from io import BytesIO

from PIL import Image

from backend.tests.test_role_security import auth_header, client, register, users


def test_prediction_health_reports_readiness(client):
    response = client.get("/api/predict/health")
    assert response.status_code == 200
    assert response.json()["status"] in {"HEALTHY", "UNHEALTHY"}


def test_prediction_rejects_unsupported_image_format(client, users):
    accounts, created = users
    patient = register(client, accounts[0], created)
    image = Image.new("RGB", (8, 8), color=(20, 40, 60))
    image_bytes = BytesIO()
    image.save(image_bytes, format="GIF")

    response = client.post(
        "/api/predict",
        headers=auth_header(patient["access_token"]),
        files={"file": ("unsupported.gif", image_bytes.getvalue(), "image/gif")},
        data={"model_name": "ResNet50", "model_version": "1.0"},
    )
    assert response.status_code == 415
    assert response.json()["detail"] == "Supported image formats are JPEG, PNG, BMP, and TIFF"
