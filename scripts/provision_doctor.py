"""Create a doctor account after a privileged operator verifies credentials."""
from getpass import getpass, getuser
import sqlite3

from backend.app.core.database import init_db
from backend.app.core.doctor_provisioning import provision_verified_doctor


def main() -> int:
    print("Provisioning requires prior manual verification of professional credentials.")
    if input("Have you verified this person's credentials? Type VERIFIED to continue: ").strip() != "VERIFIED":
        print("No account created.")
        return 1

    name = input("Doctor's full name: ").strip()
    email = input("Doctor's email: ").strip()
    verification_method = input(
        "Credential review method (do not enter license numbers or sensitive details): "
    ).strip()
    password = getpass("Temporary password (minimum 12 characters): ")
    confirmation = getpass("Confirm temporary password: ")
    if password != confirmation:
        print("Passwords do not match.")
        return 1

    init_db()
    try:
        doctor = provision_verified_doctor(
            name=name,
            email=email,
            password=password,
            provisioned_by=getuser(),
            verification_method=verification_method,
        )
    except (ValueError, sqlite3.IntegrityError) as exc:
        print(f"Doctor account was not created: {exc}")
        return 1

    print(f"Doctor account provisioned: {doctor['email']} ({doctor['id']})")
    print("Credential review was recorded; communicate the temporary password securely.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
