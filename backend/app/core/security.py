import secrets


def generate_secret_key() -> str:
    return secrets.token_urlsafe(32)


def verify_api_key(provided_key: str, expected_key: str) -> bool:
    return secrets.compare_digest(provided_key, expected_key)