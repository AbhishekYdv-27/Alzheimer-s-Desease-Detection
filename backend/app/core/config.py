from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Alzheimer's AI Platform"
    app_version: str = "0.1.0"
    app_env: str = "development"
    debug: bool = False
    host: str = "127.0.0.1"
    port: int = 8001
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173"
    secret_key: str | None = None
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    alzheimers_db_path: str | None = None
    model_checkpoint_path: str | None = None
    model_checkpoint_sha256: str | None = None
    model_artifact_url: str | None = None
    model_artifact_token: str | None = None
    max_upload_size_bytes: int = 10 * 1024 * 1024
    max_image_pixels: int = 20_000_000

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()