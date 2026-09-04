from backend.tests.test_role_security import auth_header, client, register, users


def test_slot_booking_conflict_and_approval_notifications(client, users):
    accounts, created = users
    patient = register(client, accounts[0], created)
    doctor = register(client, accounts[1], created)
    patient_headers = auth_header(patient["access_token"])
    doctor_headers = auth_header(doctor["access_token"])

    schedule = {
        "date": "2099-04-15",
        "start_time": "09:00",
        "end_time": "10:00",
        "interval_minutes": 30,
    }
    response = client.post("/api/portal/doctor/availability", json=schedule, headers=doctor_headers)
    assert response.status_code == 200
    slots = response.json()
    assert len(slots) == 2

    available = client.get(
        f"/api/portal/doctors/{doctor['user']['id']}/availability?date=2099-04-15"
    )
    assert available.status_code == 200
    assert all(slot["is_available"] == 1 for slot in available.json())

    booking = client.post(
        "/api/portal/appointments",
        json={
            "doctor_id": doctor["user"]["id"],
            "slot_id": slots[0]["id"],
            "appointment_at": slots[0]["slot_at"],
            "reason": "Reliability test",
        },
        headers=patient_headers,
    )
    assert booking.status_code == 200
    appointment_id = booking.json()["id"]

    duplicate = client.post(
        "/api/portal/appointments",
        json={
            "doctor_id": doctor["user"]["id"],
            "slot_id": slots[0]["id"],
            "appointment_at": slots[0]["slot_at"],
        },
        headers=patient_headers,
    )
    assert duplicate.status_code == 409

    unavailable = client.get(
        f"/api/portal/doctors/{doctor['user']['id']}/availability?date=2099-04-15"
    ).json()
    assert next(slot for slot in unavailable if slot["id"] == slots[0]["id"])["is_available"] == 0

    doctor_notifications = client.get("/api/portal/notifications", headers=doctor_headers)
    assert doctor_notifications.status_code == 200
    assert any(item["entity_id"] == appointment_id for item in doctor_notifications.json())

    approved = client.patch(
        f"/api/portal/appointments/{appointment_id}",
        json={"status": "approved"},
        headers=doctor_headers,
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    patient_notifications = client.get("/api/portal/notifications", headers=patient_headers)
    assert patient_notifications.status_code == 200
    assert any(item["notification_type"] == "appointment_update" for item in patient_notifications.json())


def test_rejection_and_notification_read_state(client, users):
    accounts, created = users
    patient = register(client, accounts[0], created)
    doctor = register(client, accounts[1], created)
    patient_headers = auth_header(patient["access_token"])
    doctor_headers = auth_header(doctor["access_token"])

    slots = client.post(
        "/api/portal/doctor/availability",
        json={"date": "2099-04-16", "start_time": "09:00", "end_time": "09:30", "interval_minutes": 30},
        headers=doctor_headers,
    ).json()
    appointment = client.post(
        "/api/portal/appointments",
        json={"doctor_id": doctor["user"]["id"], "slot_id": slots[0]["id"], "appointment_at": slots[0]["slot_at"]},
        headers=patient_headers,
    ).json()
    rejected = client.patch(
        f"/api/portal/appointments/{appointment['id']}",
        json={"status": "rejected"},
        headers=doctor_headers,
    )
    assert rejected.status_code == 200

    notification = client.get("/api/portal/notifications", headers=patient_headers).json()[0]
    marked = client.patch(f"/api/portal/notifications/{notification['id']}/read", headers=patient_headers)
    assert marked.status_code == 200
    persisted = client.get("/api/portal/notifications", headers=patient_headers).json()[0]
    assert persisted["read_at"] is not None
