"""
DesiCaptions — WebSocket Server (FastAPI)
Handles live microphone captioning via WebSocket.

Run with: uvicorn websocket_server:app --host 0.0.0.0 --port 8000
"""

import os
import json
import asyncio
import tempfile
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from modules.audio_processor import AudioProcessor
from modules.asr_router import ASRRouter
from modules.gemini_processor import GeminiPostProcessor, MODE_DESI, MODE_BILINGUAL, MODE_ENGLISH
from modules.srt_builder import SRTBuilder
from pipeline import DesiCaptionsPipeline, PipelineConfig


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="DesiCaptions API",
    description="AI-powered code-mixed subtitle generator for Indian content creators",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global ASR + post-processor (singleton — Whisper model loads once)
_asr_router: Optional[ASRRouter] = None
_gemini_processor: Optional[GeminiPostProcessor] = None


def get_asr_router() -> ASRRouter:
    global _asr_router
    if _asr_router is None:
        _asr_router = ASRRouter(
            sarvam_api_key=os.getenv("SARVAM_API_KEY", ""),
            whisper_model_size=os.getenv("WHISPER_MODEL", "medium"),
        )
    return _asr_router


def get_gemini_processor() -> GeminiPostProcessor:
    global _gemini_processor
    if _gemini_processor is None:
        _gemini_processor = GeminiPostProcessor(
            api_key=os.getenv("GEMINI_API_KEY", ""),
        )
    return _gemini_processor


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return {"message": "DesiCaptions API is running", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "sarvam_key_set": bool(os.getenv("SARVAM_API_KEY")),
        "gemini_key_set": bool(os.getenv("GEMINI_API_KEY")),
    }


class TranscribeRequest(BaseModel):
    language: str = "auto"
    output_mode: str = MODE_DESI
    prefer_model: str = "sarvam"


@app.post("/transcribe")
async def transcribe_file(
    request: TranscribeRequest,
    # Note: file upload handled by multipart in FastAPI
):
    """
    Full pipeline endpoint for uploaded audio/video files.
    Returns SRT as downloadable file.
    """
    # This endpoint is called from Streamlit via st.file_uploader
    # See app.py for the Streamlit integration
    return JSONResponse({"error": "Use /transcribe-multipart for file upload"})


@app.post("/transcribe-multipart")
async def transcribe_multipart():
    """
    Multipart file upload endpoint.
    Streamlit handles this directly — see app.py.
    """
    return {"status": "use Streamlit app"}


# ---------------------------------------------------------------------------
# WebSocket — live captioning
# ---------------------------------------------------------------------------

@app.websocket("/ws/live")
async def websocket_live_caption(websocket: WebSocket):
    """
    WebSocket endpoint for live microphone captioning.
    
    Protocol:
    - Client connects, sends JSON config: {"language": "hinglish", "mode": "desi"}
    - Client sends binary audio chunks (raw PCM or WebM/OGG from browser)
    - Server replies with JSON: {"text": "...", "is_final": false/true}
    """
    await websocket.accept()
    asr = get_asr_router()
    gemini = get_gemini_processor()
    audio_processor = AudioProcessor(chunk_ms=3000, overlap_ms=500)

    # State
    language = "auto"
    output_mode = MODE_DESI
    session_srt = SRTBuilder()
    chunk_count = 0
    current_ms = 0

    print("[WS] Client connected")

    try:
        # Expect config message first
        config_raw = await websocket.receive_text()
        config = json.loads(config_raw)
        language = config.get("language", "auto")
        output_mode = config.get("mode", MODE_DESI)
        print(f"[WS] Config received: lang={language}, mode={output_mode}")

        await websocket.send_json({
            "type": "ready",
            "message": f"Ready. Language: {language}, Mode: {output_mode}"
        })

        # Main receive loop
        while True:
            data = await websocket.receive_bytes()
            chunk_count += 1

            try:
                # Process the incoming audio bytes
                chunks, duration = audio_processor.process_bytes(data, ".webm")

                for chunk_bytes in chunks:
                    # ASR
                    segment = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: asr.transcribe(
                            audio_bytes=chunk_bytes,
                            language=language,
                            prefer_model="sarvam",
                        )
                    )

                    if not segment or not segment.text.strip():
                        continue

                    # Language auto-detected on first chunk
                    if language == "auto":
                        language = segment.language

                    # Gemini streaming post-process
                    formatted = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: gemini.process_chunk_streaming(
                            raw_text=segment.text,
                            language=language,
                            mode=output_mode,
                        )
                    )

                    # Add to SRT session
                    chunk_ms = 3000
                    session_srt.add_segment(
                        text=formatted or segment.text,
                        start_ms=current_ms,
                        end_ms=current_ms + chunk_ms,
                    )
                    current_ms += chunk_ms

                    # Send to client
                    await websocket.send_json({
                        "type": "caption",
                        "text": formatted or segment.text,
                        "raw": segment.text,
                        "language": language,
                        "chunk": chunk_count,
                        "is_final": False,
                    })

            except Exception as e:
                print(f"[WS] Error processing chunk {chunk_count}: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e),
                    "chunk": chunk_count,
                })

    except WebSocketDisconnect:
        print(f"[WS] Client disconnected after {chunk_count} chunks")

        # Save session SRT
        if session_srt.segment_count() > 0:
            srt_path = f"/tmp/desicaptions_live_{id(websocket)}.srt"
            session_srt.export_srt(srt_path)
            print(f"[WS] Session SRT saved to {srt_path}")

    except Exception as e:
        print(f"[WS] Fatal error: {e}")
        try:
            await websocket.send_json({"type": "fatal_error", "message": str(e)})
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Run directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "websocket_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
