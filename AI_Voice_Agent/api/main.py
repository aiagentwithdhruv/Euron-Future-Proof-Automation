"""FastAPI app for the AI Voice Agent.

Run locally:
    uvicorn api.main:app --reload --port 8080

Tunnel (free, stable):
    cloudflared tunnel --url http://localhost:8080

Then register the tunnel URL + API_KEY header on your Vapi assistant's tool config.
"""

from __future__ import annotations

import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.config import get_settings
from api.logging_utils import get_logger
from api.routers import health, tools, webhooks


logger = get_logger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="AI Voice Agent",
        version="0.1.0",
        description="Tool endpoints + webhooks for Vapi/Bland/Retell voice assistants.",
    )

    @app.middleware("http")
    async def access_log(request: Request, call_next):
        t0 = time.monotonic()
        try:
            response = await call_next(request)
            duration_ms = int((time.monotonic() - t0) * 1000)
            logger.info(
                "http.request",
                extra={"path": request.url.path, "status": response.status_code, "duration_ms": duration_ms},
            )
            return response
        except Exception as e:  # noqa: BLE001
            duration_ms = int((time.monotonic() - t0) * 1000)
            logger.exception(f"http.error path={request.url.path} duration_ms={duration_ms}: {e}")
            return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    app.include_router(health.router)
    app.include_router(tools.router)
    app.include_router(webhooks.router)

    @app.on_event("startup")
    async def _startup() -> None:
        logger.info(
            "app.startup",
            extra={"path": "/", "status": 0},
        )
        # Soft config summary (no secrets): helps students see what's wired
        logger.info(
            f"config platform={settings.voice_platform} "
            f"business={settings.business_name} "
            f"env={settings.environment}"
        )

    return app


app = create_app()
