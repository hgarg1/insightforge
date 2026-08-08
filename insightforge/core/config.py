"""Environment-backed application configuration."""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path


def _env(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


def _default_storage_dir() -> Path:
    """Use Flet's writable per-user data directory in packaged builds."""

    packaged_data = os.getenv("FLET_APP_STORAGE_DATA", "").strip()
    return Path(packaged_data) if packaged_data else Path("./data")


def _default_database_url() -> str:
    database_path = (_default_storage_dir() / "insightforge.db").resolve()
    return f"sqlite:///{database_path.as_posix()}"


def _default_secret_key() -> str:
    configured = os.getenv("INSIGHTFORGE_SECRET_KEY", "").strip()
    if configured:
        return configured

    # A packaged desktop install needs a unique, persistent signing key. Keeping
    # it in Flet's per-user data directory survives upgrades without writing to
    # the read-only application installation directory.
    packaged_data = os.getenv("FLET_APP_STORAGE_DATA", "").strip()
    if not packaged_data:
        return "development-only-change-this-secret-key"

    storage_dir = Path(packaged_data)
    storage_dir.mkdir(parents=True, exist_ok=True)
    key_path = storage_dir / ".secret-key"
    if key_path.exists():
        saved = key_path.read_text(encoding="utf-8").strip()
        if saved:
            return saved

    generated = secrets.token_urlsafe(48)
    try:
        key_path.write_text(generated, encoding="utf-8")
    except OSError:
        # Another startup may have won the race to create the key.
        saved = key_path.read_text(encoding="utf-8").strip()
        if saved:
            return saved
        raise
    return generated


@dataclass(slots=True)
class Settings:
    environment: str = field(default_factory=lambda: _env("INSIGHTFORGE_ENV", "development"))
    database_url: str = field(
        default_factory=lambda: _env("INSIGHTFORGE_DATABASE_URL", _default_database_url())
    )
    storage_dir: Path = field(
        default_factory=lambda: Path(
            _env("INSIGHTFORGE_STORAGE_DIR", str(_default_storage_dir()))
        )
    )
    api_url: str = field(
        default_factory=lambda: _env("INSIGHTFORGE_API_URL", "http://127.0.0.1:8765")
    )
    secret_key: str = field(default_factory=_default_secret_key)
    access_token_minutes: int = field(
        default_factory=lambda: int(_env("INSIGHTFORGE_ACCESS_TOKEN_MINUTES", "30"))
    )
    refresh_token_days: int = field(
        default_factory=lambda: int(_env("INSIGHTFORGE_REFRESH_TOKEN_DAYS", "30"))
    )
    reset_token_minutes: int = field(
        default_factory=lambda: int(_env("INSIGHTFORGE_RESET_TOKEN_MINUTES", "30"))
    )
    cors_origins: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            item.strip()
            for item in _env(
                "INSIGHTFORGE_CORS_ORIGINS", "http://localhost:8550,http://127.0.0.1:8550"
            ).split(",")
            if item.strip()
        )
    )

    @property
    def upload_dir(self) -> Path:
        return self.storage_dir / "uploads"

    @property
    def export_dir(self) -> Path:
        return self.storage_dir / "exports"

    def ensure_directories(self) -> None:
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.export_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
