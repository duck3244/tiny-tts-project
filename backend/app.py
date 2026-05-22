#!/usr/bin/env python3
"""
FastAPI Backend for Tiny TTS
Vue SPA + FastAPI 구조의 백엔드 API (Flask web_tts.py 대체)
"""

import os
import threading
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from tts_engine import MAX_TEXT_LENGTH, TTSEngine

# HF Hub에서 존재가 검증된 모델만 허용 (점검 B1)
ALLOWED_MODELS = {
    "Matthijs/mms-tts-kor": "한국어",
    "facebook/mms-tts-eng": "영어",
    "facebook/mms-tts-spa": "스페인어",
    "facebook/mms-tts-fra": "프랑스어",
}
DEFAULT_MODEL = "Matthijs/mms-tts-kor"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
DIST_DIR = os.path.join(BASE_DIR, "..", "frontend", "dist")
MAX_KEPT_FILES = 20  # outputs/ 에 보관할 최대 wav 개수 (점검 I1)

os.makedirs(OUTPUT_DIR, exist_ok=True)

engine: TTSEngine | None = None
engine_lock = threading.Lock()


def _load_engine(model_name: str) -> None:
    """엔진을 (재)로딩. 모델 전환 시 이전 모델 VRAM 회수 (점검 I2)."""
    global engine
    old = engine
    engine = TTSEngine(model_name=model_name)
    if old is not None:
        del old
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass


def _prune_outputs() -> None:
    """outputs/ 의 오래된 wav 파일을 MAX_KEPT_FILES 개로 정리 (점검 I1)."""
    try:
        wavs = [
            os.path.join(OUTPUT_DIR, f)
            for f in os.listdir(OUTPUT_DIR)
            if f.endswith(".wav")
        ]
        wavs.sort(key=os.path.getmtime, reverse=True)
        for stale in wavs[MAX_KEPT_FILES:]:
            os.remove(stale)
    except OSError:
        pass


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """서버 기동 시 기본 모델 미리 로딩."""
    _load_engine(DEFAULT_MODEL)
    info = engine.get_device_info()
    print(f"디바이스: {info['device']} / 모델: {info['model_name']}")
    yield


app = FastAPI(title="Tiny TTS API", lifespan=lifespan)

# 개발 시 Vite 프록시를 쓰면 불필요하나, 직접 호출도 허용 (단일 사용자 MVP)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_TEXT_LENGTH)
    language: str = DEFAULT_MODEL


@app.get("/api/status")
def status():
    """디바이스·모델 상태 및 지원 언어 목록."""
    if engine is None:
        return {"ready": False}
    info = engine.get_device_info()
    info["ready"] = True
    info["languages"] = ALLOWED_MODELS
    return info


@app.post("/api/generate")
def generate(req: GenerateRequest):
    """텍스트를 음성으로 변환하고 파일명을 반환."""
    if req.language not in ALLOWED_MODELS:
        raise HTTPException(status_code=400, detail="지원하지 않는 언어입니다.")

    with engine_lock:
        if engine is None or engine.model_name != req.language:
            _load_engine(req.language)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"tts_{timestamp}.wav"
        filepath = os.path.join(OUTPUT_DIR, filename)

        try:
            engine.generate(req.text, output_path=filepath)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        _prune_outputs()

    return {"filename": filename}


@app.get("/api/audio/{filename}")
def get_audio(filename: str):
    """생성된 wav 파일 반환."""
    safe = os.path.basename(filename)  # 경로 탐색 방지
    if not safe.endswith(".wav"):
        raise HTTPException(status_code=400, detail="잘못된 파일명입니다.")
    path = os.path.join(OUTPUT_DIR, safe)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    return FileResponse(path, media_type="audio/wav", filename=safe)


# 운영: 빌드된 프론트엔드(dist)가 있으면 정적 서빙 (API 라우트 뒤에 마운트)
if os.path.isdir(DIST_DIR):
    app.mount("/", StaticFiles(directory=DIST_DIR, html=True), name="spa")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
