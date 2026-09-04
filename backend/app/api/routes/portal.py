import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.core.auth import get_current_user, require_role
from backend.app.core.database import get_db

router = APIRouter(prefix="/api/portal", tags=["patient-doctor-portal"])


class DoctorProfileInput(BaseModel):
    specialization: str = ""
    qualifications: str = ""
    experience_years: int = Field(default=0, ge=0, le=80)
    clinic_name: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    bio: str = ""
    consultation_info: str = ""
    availability: str = ""
    phone: str = ""


class AppointmentInput(BaseModel):
    doctor_id: str
    appointment_at: str
    slot_id: Optional[str] = None
    reason: str = Field(default="", max_length=1000)


class AvailabilityInput(BaseModel):
    date: str
    start_time: str
    end_time: str
    interval_minutes: int = Field(default=30, ge=15, le=180)


class StatusInput(BaseModel):
    status: str


class NoteInput(BaseModel):
    patient_id: str
    appointment_id: Optional[str] = None
    note_type: str = "clinical_note"
    content: str = Field(min_length=1, max_length=5000)
    follow_up: str = Field(default="", max_length=2000)


def create_notification(conn, user_id: str, notification_type: str, title: str, message: str, entity_id: Optional[str] = None):
    conn.execute("""INSERT INTO notifications
        (id, user_id, notification_type, title, message, entity_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)""", (str(uuid.uuid4()), user_id, notification_type,
        title, message, entity_id, datetime.utcnow().isoformat()))


def profile_dict(row):
    return dict(row) if row else None


@router.get("/doctors")
async def list_doctors(city: str = Query(default=""), specialization: str = Query(default="")):
    conn = get_db()
    query = """SELECT u.id, u.name, u.email, p.* FROM users u JOIN doctor_profiles p ON p.user_id = u.id
               WHERE u.role = 'doctor'"""
    params = []
    if city:
        query += " AND lower(p.city) LIKE lower(?)"
        params.append(f"%{city}%")
    if specialization:
        query += " AND lower(p.specialization) LIKE lower(?)"
        params.append(f"%{specialization}%")
    query += " ORDER BY p.experience_years DESC, u.name"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


@router.get("/doctors/{doctor_id}")
async def get_doctor(doctor_id: str):
    conn = get_db()
    row = conn.execute("""SELECT u.id, u.name, u.email, p.* FROM users u
                          JOIN doctor_profiles p ON p.user_id = u.id
                          WHERE u.id = ? AND u.role = 'doctor'""", (doctor_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    return dict(row)


@router.get("/doctors/{doctor_id}/availability")
async def doctor_availability(doctor_id: str, date: str = Query(default="")):
    conn = get_db()
    query = """SELECT s.id, s.slot_at, s.duration_minutes,
                      CASE WHEN a.id IS NULL THEN 1 ELSE 0 END AS is_available
               FROM availability_slots s LEFT JOIN appointments a
                 ON a.slot_id = s.id AND a.status IN ('pending', 'approved')
               WHERE s.doctor_id = ? AND s.slot_at >= ?"""
    params = [doctor_id, datetime.utcnow().isoformat()]
    if date:
        query += " AND substr(s.slot_at, 1, 10) = ?"
        params.append(date)
    query += " ORDER BY s.slot_at"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


@router.post("/doctor/availability")
async def create_availability(data: AvailabilityInput, doctor: dict = Depends(require_role("doctor"))):
    try:
        start = datetime.fromisoformat(f"{data.date}T{data.start_time}")
        end = datetime.fromisoformat(f"{data.date}T{data.end_time}")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Use valid date and time values") from exc
    if end <= start:
        raise HTTPException(status_code=422, detail="End time must be after start time")
    conn = get_db()
    created = []
    current = start
    while current + timedelta(minutes=data.interval_minutes) <= end:
        slot_at = current.isoformat(timespec="minutes")
        slot_id = str(uuid.uuid4())
        cursor = conn.execute("""INSERT OR IGNORE INTO availability_slots
            (id, doctor_id, slot_at, duration_minutes, created_at) VALUES (?, ?, ?, ?, ?)""",
            (slot_id, doctor["id"], slot_at, data.interval_minutes, datetime.utcnow().isoformat()))
        if cursor.rowcount:
            created.append({"id": slot_id, "slot_at": slot_at, "duration_minutes": data.interval_minutes})
        current += timedelta(minutes=data.interval_minutes)
    conn.commit()
    conn.close()
    return created


@router.get("/doctor/profile")
async def get_doctor_profile(doctor: dict = Depends(require_role("doctor"))):
    conn = get_db()
    row = conn.execute("SELECT * FROM doctor_profiles WHERE user_id = ?", (doctor["id"],)).fetchone()
    conn.close()
    return profile_dict(row) or {"user_id": doctor["id"]}


@router.put("/doctor/profile")
async def save_doctor_profile(data: DoctorProfileInput, doctor: dict = Depends(require_role("doctor"))):
    conn = get_db()
    values = tuple(data.dict().values())
    conn.execute("""INSERT INTO doctor_profiles
        (user_id, specialization, qualifications, experience_years, clinic_name, address, city, state, bio, consultation_info, availability, phone)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET specialization=excluded.specialization, qualifications=excluded.qualifications,
        experience_years=excluded.experience_years, clinic_name=excluded.clinic_name, address=excluded.address,
        city=excluded.city, state=excluded.state, bio=excluded.bio, consultation_info=excluded.consultation_info,
        availability=excluded.availability, phone=excluded.phone""", (doctor["id"], *values))
    conn.commit()
    row = conn.execute("SELECT * FROM doctor_profiles WHERE user_id = ?", (doctor["id"],)).fetchone()
    conn.close()
    return dict(row)


@router.post("/appointments")
async def create_appointment(data: AppointmentInput, patient: dict = Depends(require_role("patient"))):
    conn = get_db()
    doctor = conn.execute("SELECT id FROM users WHERE id = ? AND role = 'doctor'", (data.doctor_id,)).fetchone()
    if not doctor:
        conn.close()
        raise HTTPException(status_code=404, detail="Doctor not found")
    if data.slot_id:
        slot = conn.execute("""SELECT id, slot_at FROM availability_slots
                              WHERE id = ? AND doctor_id = ?""", (data.slot_id, data.doctor_id)).fetchone()
        if not slot:
            conn.close()
            raise HTTPException(status_code=404, detail="Availability slot not found")
        data.appointment_at = slot["slot_at"]
    conflict = conn.execute("""SELECT id FROM appointments WHERE doctor_id = ? AND appointment_at = ?
                              AND status IN ('pending', 'approved')""", (data.doctor_id, data.appointment_at)).fetchone()
    if conflict:
        conn.close()
        raise HTTPException(status_code=409, detail="That appointment time is already requested")
    appointment_id = str(uuid.uuid4())
    conn.execute("""INSERT INTO appointments (id, patient_id, doctor_id, appointment_at, slot_id, reason, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)""", (appointment_id, patient["id"], data.doctor_id, data.appointment_at, data.slot_id, data.reason, datetime.utcnow().isoformat()))
    create_notification(conn, data.doctor_id, "appointment_request", "New appointment request",
                        f"{patient['name']} requested an appointment for {data.appointment_at}.", appointment_id)
    conn.commit()
    row = conn.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,)).fetchone()
    conn.close()
    return dict(row)


def appointment_rows(where: str, params: tuple):
    conn = get_db()
    rows = conn.execute(f"""SELECT a.*, p.name AS patient_name, d.name AS doctor_name
                           FROM appointments a JOIN users p ON p.id = a.patient_id JOIN users d ON d.id = a.doctor_id
                           WHERE {where} ORDER BY a.appointment_at""", params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


@router.get("/appointments/me")
async def patient_appointments(patient: dict = Depends(require_role("patient"))):
    return appointment_rows("a.patient_id = ?", (patient["id"],))


@router.get("/doctor/appointments")
async def doctor_appointments(doctor: dict = Depends(require_role("doctor"))):
    return appointment_rows("a.doctor_id = ?", (doctor["id"],))


@router.patch("/appointments/{appointment_id}")
async def update_appointment(appointment_id: str, data: StatusInput, doctor: dict = Depends(require_role("doctor"))):
    if data.status not in {"approved", "rejected", "cancelled", "completed"}:
        raise HTTPException(status_code=422, detail="Invalid appointment status")
    conn = get_db()
    cursor = conn.execute("UPDATE appointments SET status = ? WHERE id = ? AND doctor_id = ?", (data.status, appointment_id, doctor["id"]))
    conn.commit()
    row = conn.execute("SELECT * FROM appointments WHERE id = ? AND doctor_id = ?", (appointment_id, doctor["id"])).fetchone()
    if cursor.rowcount == 0 or not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Appointment not found")
    create_notification(conn, row["patient_id"], "appointment_update", f"Appointment {data.status}",
                        f"Your appointment for {row['appointment_at']} was {data.status}.", appointment_id)
    conn.commit()
    conn.close()
    return dict(row)


@router.get("/doctor/patients")
async def doctor_patients(doctor: dict = Depends(require_role("doctor"))):
    conn = get_db()
    rows = conn.execute("""SELECT DISTINCT u.id, u.name, u.email FROM users u JOIN appointments a ON a.patient_id = u.id
                          WHERE a.doctor_id = ? AND a.status IN ('pending', 'approved', 'completed') ORDER BY u.name""", (doctor["id"],)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


@router.post("/doctor/notes")
async def create_note(data: NoteInput, doctor: dict = Depends(require_role("doctor"))):
    conn = get_db()
    relation = conn.execute("""SELECT id FROM appointments WHERE doctor_id = ? AND patient_id = ?
                              AND status IN ('approved', 'completed')""", (doctor["id"], data.patient_id)).fetchone()
    if not relation:
        conn.close()
        raise HTTPException(status_code=403, detail="A completed or approved appointment is required")
    note_id = str(uuid.uuid4())
    conn.execute("""INSERT INTO doctor_notes (id, doctor_id, patient_id, appointment_id, note_type, content, follow_up, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", (note_id, doctor["id"], data.patient_id, data.appointment_id, data.note_type, data.content, data.follow_up, datetime.utcnow().isoformat()))
    create_notification(conn, data.patient_id, "doctor_note", "New doctor note",
                        f"Dr. {doctor['name']} added a note to your care record.", note_id)
    conn.commit()
    row = conn.execute("SELECT * FROM doctor_notes WHERE id = ?", (note_id,)).fetchone()
    conn.close()
    return dict(row)


@router.get("/notifications")
async def notifications(user: dict = Depends(get_current_user)):
    conn = get_db()
    rows = conn.execute("SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC", (user["id"],)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


@router.patch("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.execute("UPDATE notifications SET read_at = ? WHERE id = ? AND user_id = ?",
                          (datetime.utcnow().isoformat(), notification_id, user["id"]))
    conn.commit()
    conn.close()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "read"}


@router.get("/progress")
async def patient_progress(patient: dict = Depends(require_role("patient"))):
    conn = get_db()
    analyses = [dict(row) for row in conn.execute("SELECT * FROM analysis_records WHERE user_id = ? ORDER BY created_at", (patient["id"],)).fetchall()]
    notes = [dict(row) for row in conn.execute("""SELECT n.*, u.name AS doctor_name FROM doctor_notes n JOIN users u ON u.id = n.doctor_id
                                                  WHERE n.patient_id = ? ORDER BY n.created_at DESC""", (patient["id"],)).fetchall()]
    conn.close()
    return {"analyses": analyses, "notes": notes}