from datetime import datetime, timezone
import uuid

from backend.app.core.auth import create_password_hash
from backend.app.core.database import get_db


def provision_verified_doctor(
    *,
    name: str,
    email: str,
    password: str,
    provisioned_by: str,
    verification_method: str,
) -> dict:
    if len(password) < 12:
        raise ValueError("Provisioned doctor passwords must contain at least 12 characters")
    if not provisioned_by.strip() or not verification_method.strip():
        raise ValueError("Provisioning operator and credential review method are required")

    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn = get_db()
    try:
        conn.execute("BEGIN")
        conn.execute(
            """INSERT INTO users
               (id, name, email, password_hash, created_at, updated_at, role)
               VALUES (?, ?, ?, ?, ?, ?, 'doctor')""",
            (user_id, name.strip(), email.strip(), create_password_hash(password), now, now),
        )
        conn.execute(
            "INSERT INTO doctor_profiles (user_id) VALUES (?)",
            (user_id,),
        )
        conn.execute(
            """INSERT INTO doctor_provisioning_audit
               (id, doctor_id, provisioned_by, verification_method, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (str(uuid.uuid4()), user_id, provisioned_by.strip(), verification_method.strip(), now),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return {
        "id": user_id,
        "name": name.strip(),
        "email": email.strip(),
        "created_at": now,
        "updated_at": now,
        "role": "doctor",
    }
