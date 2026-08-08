"""Minimal packaged-startup diagnostics written to Flet's user data directory."""

from __future__ import annotations

import os
import traceback
from datetime import UTC, datetime
from pathlib import Path


def _runtime_log_path() -> Path | None:
    storage = os.getenv("FLET_APP_STORAGE_DATA", "").strip()
    if storage:
        return Path(storage) / "runtime.log"

    console = os.getenv("FLET_APP_CONSOLE", "").strip()
    if console:
        return Path(console).with_name("runtime.log")

    return None


def reset_runtime_log() -> None:
    path = _runtime_log_path()
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


def log_runtime(message: str, error: BaseException | None = None) -> None:
    path = _runtime_log_path()
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).isoformat(timespec="milliseconds")
    detail = f"{timestamp}  {message}\n"
    if error is not None:
        detail += "".join(traceback.format_exception(error))
    with path.open("a", encoding="utf-8") as log:
        log.write(detail)
