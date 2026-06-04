"""FastAPI entry point for the voice bot backend."""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers.voice import router as voice_router
from services import stt_sarvam as stt_service
from services import tts_router as tts_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("voicebot")

app = FastAPI(title="Voice Bot Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(voice_router)


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("Voice bot backend ready on %s:%s", settings.host, settings.port)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await tts_service.close()
    await stt_service.close()
    logger.info("Voice bot backend shutting down")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/")
async def root() -> dict:
    return {
        "name": "voice-bot-backend",
        "ws": "/ws/voice",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level="info",
    )
