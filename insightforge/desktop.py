"""Packaged Windows desktop entry point.

The Flet runner calls ``main(page)`` directly, so the local API is started here
and the UI receives an explicit loopback endpoint. This keeps the packaged app
self-contained while preserving the browser deployment boundary.
"""

from __future__ import annotations

import os
import socket
import threading

import flet as ft

from insightforge.api.server import start_local_api
from insightforge.runtime_log import log_runtime
from insightforge.ui.app import InsightForgeApp
from insightforge.ui.client import ApiClient

_startup_lock = threading.Lock()
_api_port: int | None = None
_AUTH_MODES = {"login", "signup", "reset-request", "reset-confirm"}


def _initial_auth_mode() -> str:
    requested = os.getenv("INSIGHTFORGE_INITIAL_AUTH_MODE", "login").strip().lower()
    return requested if requested in _AUTH_MODES else "login"


def _available_port(preferred: int = 8765) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as candidate:
        candidate.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            candidate.bind(("127.0.0.1", preferred))
        except OSError:
            candidate.bind(("127.0.0.1", 0))
        return int(candidate.getsockname()[1])


def _ensure_local_api() -> int:
    global _api_port
    with _startup_lock:
        if _api_port is None:
            _api_port = _available_port()
            start_local_api(port=_api_port)
    return _api_port


def main(page: ft.Page) -> None:
    log_runtime("Flet page callback started")
    try:
        port = _ensure_local_api()
        log_runtime(f"Local API started on 127.0.0.1:{port}")
        InsightForgeApp(
            page,
            client=ApiClient(base_url=f"http://127.0.0.1:{port}"),
            initial_auth_mode=_initial_auth_mode(),
        )
        log_runtime("Initial UI mounted")
    except BaseException as error:
        log_runtime("Initial UI mount failed", error)
        raise


def run_app() -> None:
    """Connect the packaged Python application to the native Flet shell."""

    ft.run(main, assets_dir="assets")
    log_runtime("Flet runner stopped")
