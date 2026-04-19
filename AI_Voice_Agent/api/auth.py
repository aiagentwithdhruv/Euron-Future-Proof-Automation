"""Shared-secret auth — Vapi sends our API_KEY in a custom header on every tool call."""

from __future__ import annotations

from fastapi import Header, HTTPException, status

from api.config import get_settings


async def require_api_key(
    x_api_key: str | None = Header(default=None, alias="X-Api-Key"),
    authorization: str | None = Header(default=None),
) -> None:
    settings = get_settings()
    if not settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API_KEY not configured on server",
        )
    presented = x_api_key
    if not presented and authorization:
        if authorization.lower().startswith("bearer "):
            presented = authorization.split(" ", 1)[1].strip()
    if presented != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
