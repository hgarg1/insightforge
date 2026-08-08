"""FastAPI application factory and local desktop server."""

from __future__ import annotations

import threading

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from insightforge.api.routes import auth, dashboard, datasets
from insightforge.core.config import settings
from insightforge.core.db import initialize_database


def create_app() -> FastAPI:
    initialize_database()
    app = FastAPI(
        title="InsightForge API",
        version="0.1.0",
        description="Secure Excel analytics and customizable dashboard API.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(auth.router, prefix="/api")
    app.include_router(datasets.router, prefix="/api")
    app.include_router(dashboard.router, prefix="/api")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "insightforge-api"}

    @app.exception_handler(ValueError)
    async def value_error_handler(_, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    return app


app = create_app()


def run(host: str = "127.0.0.1", port: int = 8765) -> None:
    uvicorn.run(app, host=host, port=port, log_level="info")


def start_local_api(host: str = "127.0.0.1", port: int = 8765) -> threading.Thread:
    """Start the local API in a daemon thread for the desktop app."""

    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, name="insightforge-api", daemon=True)
    thread.start()
    return thread


if __name__ == "__main__":
    run()
