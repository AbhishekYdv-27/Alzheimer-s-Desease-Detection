import uuid

import pytest
from fastapi.testclient import TestClient

from backend.app.core.database import get_db
from backend.app.core.auth import create_access_token
from backend.app.core.doctor_provisioning import provision_verified_doctor
from backend.app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def users():
    suffix = uuid.uuid4().hex
    accounts = [
        {"name": "Pytest Patient", "email": f"patient-{suffix}@example.com", "password": "patient123", "role": "patient"},
        {"name": "Pytest Doctor", "email": f"doctor-{suffix}@example.com", "password": "test-doctor-password-123", "role": "doctor"},
    ]
    created = []
    yield accounts, created
    conn = get_db()
    ids = [user_id for user_id in created]
    if ids:
        marks = ",".join("?" for _ in ids)
        conn.execute(f"DELETE FROM notifications WHERE user_id IN ({marks})", ids)
        conn.execute(f"DELETE FROM availability_slots WHERE doctor_id IN ({marks})", ids)
        conn.execute(f"DELETE FROM doctor_notes WHERE doctor_id IN ({marks}) OR patient_id IN ({marks})", ids + ids)
        conn.execute(f"DELETE FROM appointments WHERE doctor_id IN ({marks}) OR patient_id IN ({marks})", ids + ids)
        conn.execute(f"DELETE FROM doctor_profiles WHERE user_id IN ({marks})", ids)
        conn.execute(f"DELETE FROM analysis_records WHERE user_id IN ({marks})", ids)
        conn.execute(f"DELETE FROM users WHERE id IN ({marks})", ids)
        conn.commit()
    conn.close()


def register(client, account, created):
    if account["role"] == "doctor":
        user = provision_verified_doctor(
            name=account["name"],
            email=account["email"],
            password=account["password"],
            provisioned_by="pytest",
            verification_method="test fixture",
        )
        data = {"user": user, "access_token": create_access_token({"sub": user["id"]})}
    else:
        response = client.post(
            "/api/auth/register",
            json={key: account[key] for key in ("name", "email", "password")},
        )
        assert response.status_code == 200
        data = response.json()
    assert data["user"]["role"] == account["role"]
    created.append(data["user"]["id"])
    return data


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_roles_auth_and_analysis_ownership(client, users):
    accounts, created = users
    patient = register(client, accounts[0], created)
    doctor = register(client, accounts[1], created)

    assert client.get("/api/auth/me").status_code == 401
    patient_headers = auth_header(patient["access_token"])
    doctor_headers = auth_header(doctor["access_token"])
    assert client.get("/api/auth/me", headers=patient_headers).json()["role"] == "patient"
    assert client.get("/api/portal/doctor/profile", headers=patient_headers).status_code == 403
    assert client.get("/api/portal/progress", headers=doctor_headers).status_code == 403

    record = {
        "user_id": patient["user"]["id"],
        "image_name": "pytest.jpg",
        "model_name": "ResNet50",
        "predicted_class": "NonDemented",
        "confidence": 0.95,
    }
    assert client.post("/api/analysis/records", json=record, headers=patient_headers).status_code == 200
    assert client.get(f"/api/analysis/records?user_id={patient['user']['id']}", headers=patient_headers).status_code == 200
    assert client.get(f"/api/analysis/records?user_id={patient['user']['id']}", headers=doctor_headers).status_code == 403