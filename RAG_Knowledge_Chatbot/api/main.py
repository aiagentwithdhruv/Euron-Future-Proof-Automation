"""
FastAPI entrypoint. Thin HTTP layer — all logic lives in tools/.
Endpoints:
  POST /ask          body: {query, k?}         → answer or escalation
  POST /feedback     body: {query_id, verdict, note?}
  POST /reingest     body: {path, type?}       → kicks off ingest pipeline

Auth: simple header `x-api-key` matched against env API_KEY (if set).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

_HERE = Path(__file__).resolve()
_PROJECT_ROOT = _HERE.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from tools._shared import config  # noqa: E402
from tools._shared.logger import get_logger  # noqa: E402
from tools._shared.supabase_client import insert  # noqa: E402
from tools.ask import ask  # noqa: E402
from channels.whatsapp_webhook import router as whatsapp_router  # noqa: E402

logger = get_logger(__name__)

app = FastAPI(title="RAG Knowledge Chatbot", version="0.1.0")
app.include_router(whatsapp_router)

_origins = (config.get("CORS_ORIGINS") or "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins if o.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def verify_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = config.get("API_KEY")
    if expected and x_api_key != expected:
        raise HTTPException(status_code=401, detail="invalid api key")


class AskRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    k: int | None = Field(default=None, ge=1, le=20)
    channel: Literal["web", "whatsapp", "cli", "api"] = "api"


class FeedbackRequest(BaseModel):
    query: str = Field(..., min_length=1)
    answer: str | None = None
    citations: list[dict] | None = None
    confidence: float | None = None
    verdict: Literal["up", "down", "escalated"]
    note: str | None = None
    channel: str = "api"


class ReingestRequest(BaseModel):
    path: str = Field(default="./knowledge")
    type: Literal["md", "txt", "pdf", "all"] = "md"


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ask", dependencies=[Depends(verify_key)])
def ask_endpoint(req: AskRequest) -> dict:
    try:
        return ask(req.query, k=req.k, channel=req.channel)
    except EnvironmentError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/feedback", dependencies=[Depends(verify_key)])
def feedback_endpoint(req: FeedbackRequest) -> dict:
    try:
        row = insert(
            "feedback_events",
            {
                "query": req.query,
                "answer": req.answer,
                "citations": req.citations or [],
                "confidence": req.confidence,
                "verdict": req.verdict,
                "user_note": req.note,
                "channel": req.channel,
            },
        )
        return {"status": "ok", "id": row.get("id")}
    except Exception as e:
        logger.error(f"feedback failed: {e}")
        raise HTTPException(status_code=500, detail="feedback store failed")


@app.post("/reingest", dependencies=[Depends(verify_key)])
def reingest_endpoint(req: ReingestRequest) -> dict:
    """Run the 3-stage ingestion pipeline synchronously (single tenant, small KB)."""
    try:
        steps = [
            [sys.executable, "tools/ingestion/load_docs.py", "--path", req.path, "--type", req.type],
            [sys.executable, "tools/ingestion/chunk_docs.py"],
            [sys.executable, "tools/ingestion/embed_chunks.py"],
        ]
        logs = []
        for cmd in steps:
            proc = subprocess.run(
                cmd,
                cwd=_PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=600,
            )
            logs.append({"cmd": " ".join(cmd[1:]), "rc": proc.returncode, "stdout_tail": proc.stdout[-400:]})
            if proc.returncode != 0:
                raise HTTPException(
                    status_code=500,
                    detail={"stage": cmd[1], "stderr": proc.stderr[-400:]},
                )
        return {"status": "ok", "steps": logs}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"reingest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
