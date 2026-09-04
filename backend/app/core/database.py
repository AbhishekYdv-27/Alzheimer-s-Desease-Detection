import sqlite3
from pathlib import Path
from typing import Optional
from datetime import datetime
import uuid

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "app.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    user_columns = {row["name"] for row in cursor.execute("PRAGMA table_info(users)").fetchall()}
    if "role" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'patient'")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctor_profiles (
            user_id TEXT PRIMARY KEY,
            specialization TEXT NOT NULL DEFAULT '',
            qualifications TEXT NOT NULL DEFAULT '',
            experience_years INTEGER NOT NULL DEFAULT 0,
            clinic_name TEXT NOT NULL DEFAULT '',
            address TEXT NOT NULL DEFAULT '',
            city TEXT NOT NULL DEFAULT '',
            state TEXT NOT NULL DEFAULT '',
            bio TEXT NOT NULL DEFAULT '',
            consultation_info TEXT NOT NULL DEFAULT '',
            availability TEXT NOT NULL DEFAULT '',
            phone TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            doctor_id TEXT NOT NULL,
            appointment_at TEXT NOT NULL,
            reason TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES users (id),
            FOREIGN KEY (doctor_id) REFERENCES users (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS availability_slots (
            id TEXT PRIMARY KEY,
            doctor_id TEXT NOT NULL,
            slot_at TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL DEFAULT 30,
            created_at TEXT NOT NULL,
            UNIQUE (doctor_id, slot_at),
            FOREIGN KEY (doctor_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    appointment_columns = {row["name"] for row in cursor.execute("PRAGMA table_info(appointments)").fetchall()}
    if "slot_id" not in appointment_columns:
        cursor.execute("ALTER TABLE appointments ADD COLUMN slot_id TEXT")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            notification_type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            entity_id TEXT,
            read_at TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctor_notes (
            id TEXT PRIMARY KEY,
            doctor_id TEXT NOT NULL,
            patient_id TEXT NOT NULL,
            appointment_id TEXT,
            note_type TEXT NOT NULL DEFAULT 'clinical_note',
            content TEXT NOT NULL,
            follow_up TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY (doctor_id) REFERENCES users (id),
            FOREIGN KEY (patient_id) REFERENCES users (id),
            FOREIGN KEY (appointment_id) REFERENCES appointments (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_records (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            image_name TEXT NOT NULL,
            model_name TEXT NOT NULL,
            predicted_class TEXT,
            confidence REAL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    analysis_columns = {
        "model_version": "TEXT NOT NULL DEFAULT '1.0'",
        "class_probabilities": "TEXT",
        "explanation_available": "INTEGER NOT NULL DEFAULT 0",
    }
    existing_columns = {
        row["name"] for row in cursor.execute("PRAGMA table_info(analysis_records)").fetchall()
    }
    for column_name, column_definition in analysis_columns.items():
        if column_name not in existing_columns:
            cursor.execute(
                f"ALTER TABLE analysis_records ADD COLUMN {column_name} {column_definition}"
            )

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            analysis_id TEXT,
            report_type TEXT NOT NULL,
            file_path TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (analysis_id) REFERENCES analysis_records (id)
        )
    """)

    conn.commit()
    conn.close()

    create_demo_user()


def create_demo_user():
    from backend.app.core.auth import create_password_hash

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email = ?", ("demo@neuroscan.ai",))
    if cursor.fetchone() is None:
        user_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        cursor.execute(
            "INSERT INTO users (id, name, email, password_hash, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, "Demo User", "demo@neuroscan.ai", create_password_hash("demo123"), now, now)
        )
        conn.commit()

    conn.close()


def get_user_by_email(email: str) -> Optional[dict]:
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()

    conn.close()

    if row:
        return dict(row)
    return None


def get_user_by_id(user_id: str) -> Optional[dict]:
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()

    conn.close()

    if row:
        return dict(row)
    return None


def update_user_name(user_id: str, name: str) -> Optional[dict]:
    conn = get_db()
    now = datetime.utcnow().isoformat()
    conn.execute(
        "UPDATE users SET name = ?, updated_at = ? WHERE id = ?",
        (name, now, user_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_user_password(user_id: str, password_hash: str) -> Optional[dict]:
    conn = get_db()
    now = datetime.utcnow().isoformat()
    conn.execute(
        "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
        (password_hash, now, user_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_user(name: str, email: str, password_hash: str, role: str = "patient") -> dict:
    conn = get_db()
    cursor = conn.cursor()

    user_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    cursor.execute(
        "INSERT INTO users (id, name, email, password_hash, created_at, updated_at, role) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, name, email, password_hash, now, now, role)
    )

    conn.commit()
    conn.close()

    return {
        "id": user_id,
        "name": name,
        "email": email,
        "created_at": now,
        "updated_at": now
        ,"role": role
    }


def create_analysis_record(
    user_id: str,
    image_name: str,
    model_name: str,
    predicted_class: Optional[str] = None,
    confidence: Optional[float] = None,
    status: str = "pending",
    model_version: str = "1.0",
    class_probabilities: Optional[str] = None,
    explanation_available: bool = False,
) -> dict:
    conn = get_db()
    cursor = conn.cursor()

    record_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    cursor.execute(
        """INSERT INTO analysis_records
              (id, user_id, image_name, model_name, predicted_class, confidence, status, created_at,
                model_version, class_probabilities, explanation_available)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
          (record_id, user_id, image_name, model_name, predicted_class, confidence, status, now,
            model_version, class_probabilities, int(explanation_available))
    )

    conn.commit()
    conn.close()

    return {
        "id": record_id,
        "user_id": user_id,
        "image_name": image_name,
        "model_name": model_name,
        "predicted_class": predicted_class,
        "confidence": confidence,
        "status": status,
        "created_at": now
    }


def get_analysis_records(user_id: str) -> list:
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM analysis_records WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    )
    rows = cursor.fetchall()

    conn.close()

    return [dict(row) for row in rows]
