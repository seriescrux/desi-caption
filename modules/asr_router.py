"""
DesiCaptions — ASR Router Module
Handles dual-model ASR: Sarvam AI (primary) + OpenAI Whisper (secondary).
Includes code-mix language detection logic.
"""

import os
import time
import json
import tempfile
from typing import Optional, Tuple
from dataclasses import dataclass

import requests
import numpy as np

# Whisper import — graceful fallback
try:
    import whisper as openai_whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("[ASRRouter] openai-whisper not installed. Run: pip install openai-whisper")


# ---------------------------------------------------------------------------
# Language config
# ---------------------------------------------------------------------------

# Sarvam API language codes (ISO 639-1 + region)
SARVAM_LANG_CODES = {
    "hinglish": "hi-IN",
    "benglish": "bn-IN",
    "tanglish": "ta-IN",
    "tenglish": "te-IN",
    "odiaenglish": "or-IN",
    "hindi": "hi-IN",
    "bengali": "bn-IN",
    "tamil": "ta-IN",
    "telugu": "te-IN",
    "odia": "or-IN",
    "english": "en-IN",
}

# Whisper language codes
WHISPER_LANG_CODES = {
    "hinglish": "hi",
    "benglish": "bn",
    "tanglish": "ta",
    "tenglish": "te",
    "odiaenglish": "or",  # Note: Whisper support for Odia is limited
    "hindi": "hi",
    "bengali": "bn",
    "tamil": "ta",
    "telugu": "te",
    "odia": None,   # Whisper has poor Odia support, skip
    "english": "en",
}

# Common English words used in code-mixed Indian speech (sampling)
ENGLISH_INDICATOR_WORDS = {
    "the", "is", "are", "was", "were", "have", "has", "had", "will", "would",
    "can", "could", "should", "do", "does", "did", "not", "but", "and", "or",
    "so", "that", "this", "what", "how", "why", "when", "where", "who",
    "very", "really", "actually", "basically", "literally", "seriously",
    "like", "just", "even", "only", "also", "too", "again", "well",
    "okay", "ok", "yes", "no", "good", "great", "amazing", "awesome",
    "let", "lets", "get", "got", "going", "think", "know", "want",
    "need", "make", "made", "come", "came", "see", "say", "said",
    "start", "started", "watch", "video", "today", "time", "day",
    "people", "things", "something", "anything", "everything", "nothing",
}


@dataclass
class TranscriptSegment:
    text: str
    start_ms: int
    end_ms: int
    language: str
    model_used: str  # "sarvam" or "whisper"
    confidence: float = 1.0


class ASRRouter:
    """
    Routes audio chunks to the best ASR model based on language.
    Combines Sarvam AI (excellent for Indic words) +
    Whisper (excellent for English portions).
    """

    def __init__(
        self,
        sarvam_api_key: Optional[str] = None,
        whisper_model_size: str = "medium",
    ):
        self.sarvam_api_key = sarvam_api_key or os.getenv("SARVAM_API_KEY", "")
        self.whisper_model_size = whisper_model_size
        self._whisper_model = None  # Lazy load

        if not self.sarvam_api_key:
            print("[ASRRouter] WARNING: SARVAM_API_KEY not set. Sarvam calls will fail.")
            print("  Get free key at: https://www.sarvam.ai")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def transcribe(
        self,
        audio_bytes: bytes,
        language: str = "auto",
        prefer_model: str = "sarvam",
    ) -> TranscriptSegment:
        """
        Main transcription entry point.
        
        Args:
            audio_bytes: raw PCM bytes (16kHz, mono, 16-bit)
            language: detected language key (e.g. "hinglish") or "auto"
            prefer_model: "sarvam" or "whisper"
        
        Returns:
            TranscriptSegment with text + estimated timestamps
        """
        # Auto-detect language if needed
        if language == "auto":
            language = self._detect_language_from_audio(audio_bytes)

        # Route to best model
        if prefer_model == "sarvam" and self.sarvam_api_key:
            try:
                result = self._sarvam_transcribe(audio_bytes, language)
                if result and result.text.strip():
                    return result
            except Exception as e:
                print(f"[ASRRouter] Sarvam failed ({e}), falling back to Whisper")

        # Fallback to Whisper
        if WHISPER_AVAILABLE:
            return self._whisper_transcribe(audio_bytes, language)

        raise RuntimeError("No ASR model available. Install whisper or set SARVAM_API_KEY.")

    def transcribe_both(
        self,
        audio_bytes: bytes,
        language: str,
    ) -> Tuple[Optional[TranscriptSegment], Optional[TranscriptSegment]]:
        """
        Run BOTH models for benchmarking comparison.
        Returns (sarvam_result, whisper_result) — either can be None on failure.
        """
        sarvam_result = None
        whisper_result = None

        if self.sarvam_api_key:
            try:
                sarvam_result = self._sarvam_transcribe(audio_bytes, language)
            except Exception as e:
                print(f"[ASRRouter] Sarvam error: {e}")

        if WHISPER_AVAILABLE:
            try:
                whisper_result = self._whisper_transcribe(audio_bytes, language)
            except Exception as e:
                print(f"[ASRRouter] Whisper error: {e}")

        return sarvam_result, whisper_result

    # ------------------------------------------------------------------
    # Language detection
    # ------------------------------------------------------------------

    def detect_code_mix(self, text: str) -> Tuple[float, str]:
        """
        Estimate English ratio in transcribed text.
        Returns (english_ratio, classification)
        """
        words = text.lower().split()
        if not words:
            return 0.0, "unknown"

        english_count = sum(1 for w in words if w.strip(".,!?;:\"'") in ENGLISH_INDICATOR_WORDS)
        english_ratio = english_count / len(words)

        if english_ratio > 0.7:
            return english_ratio, "mostly_english"
        elif english_ratio > 0.2:
            return english_ratio, "code_mixed"
        else:
            return english_ratio, "mostly_indic"

    def _detect_language_from_audio(self, audio_bytes: bytes) -> str:
        """
        Use Whisper's built-in language detection on a short snippet.
        Fallback: return "hinglish" as the most common Indian code-mix.
        """
        if not WHISPER_AVAILABLE:
            return "hinglish"

        model = self._load_whisper()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            _write_pcm_wav(f.name, audio_bytes)
            tmp_path = f.name

        try:
            audio_array = openai_whisper.load_audio(tmp_path)
            audio_array = openai_whisper.pad_or_trim(audio_array)
            mel = openai_whisper.log_mel_spectrogram(audio_array).to(model.device)
            _, probs = model.detect_language(mel)
            detected = max(probs, key=probs.get)
            os.unlink(tmp_path)
        except Exception:
            os.unlink(tmp_path)
            return "hinglish"

        # Map Whisper language codes to our keys
        lang_map = {
            "hi": "hinglish",
            "bn": "benglish",
            "ta": "tanglish",
            "te": "tenglish",
            "or": "odiaenglish",
            "en": "english",
        }
        return lang_map.get(detected, "hinglish")

    # ------------------------------------------------------------------
    # Sarvam AI
    # ------------------------------------------------------------------

    def _sarvam_transcribe(self, audio_bytes: bytes, language: str) -> TranscriptSegment:
        """
        Call Sarvam AI Saaras v2 API.
        Docs: https://docs.sarvam.ai/api-reference/endpoints/speech-to-text
        Uses multipart/form-data with WAV file upload.
        """
        lang_code = SARVAM_LANG_CODES.get(language, "hi-IN")

        # Write PCM bytes to a temp WAV file for upload
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            _write_pcm_wav(tmp.name, audio_bytes)
            tmp_path = tmp.name

        try:
            with open(tmp_path, "rb") as audio_file:
                files = {"file": ("audio.wav", audio_file, "audio/wav")}
                data = {
                    "language_code": lang_code,
                    "model": "saaras:v3",
                    "with_timestamps": "true",
                    "with_disfluencies": "false",
                }
                headers = {"api-subscription-key": self.sarvam_api_key}

                resp = requests.post(
                    "https://api.sarvam.ai/speech-to-text",
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=30,
                )
        finally:
            os.unlink(tmp_path)

        resp.raise_for_status()
        data = resp.json()

        transcript = data.get("transcript", "")
        # Sarvam returns word-level timestamps if available
        words = data.get("words", [])

        if words:
            start_ms = int(words[0].get("start", 0) * 1000)
            end_ms = int(words[-1].get("end", 0) * 1000)
        else:
            start_ms = 0
            end_ms = self._estimate_duration_ms(audio_bytes)

        return TranscriptSegment(
            text=transcript,
            start_ms=start_ms,
            end_ms=end_ms,
            language=language,
            model_used="sarvam",
        )

    # ------------------------------------------------------------------
    # OpenAI Whisper (local)
    # ------------------------------------------------------------------

    def _whisper_transcribe(self, audio_bytes: bytes, language: str) -> TranscriptSegment:
        """Run local Whisper inference."""
        model = self._load_whisper()
        whisper_lang = WHISPER_LANG_CODES.get(language, "hi")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            _write_pcm_wav(f.name, audio_bytes)
            tmp_path = f.name

        try:
            options = {
                "task": "transcribe",
                "language": whisper_lang,
                "word_timestamps": True,
            }
            result = model.transcribe(tmp_path, **options)
        finally:
            os.unlink(tmp_path)

        full_text = result.get("text", "").strip()
        segments = result.get("segments", [])

        if segments:
            start_ms = int(segments[0]["start"] * 1000)
            end_ms = int(segments[-1]["end"] * 1000)
        else:
            start_ms = 0
            end_ms = self._estimate_duration_ms(audio_bytes)

        return TranscriptSegment(
            text=full_text,
            start_ms=start_ms,
            end_ms=end_ms,
            language=language,
            model_used="whisper",
        )

    def _load_whisper(self):
        """Lazy-load Whisper model (only downloads once)."""
        if self._whisper_model is None:
            print(f"[ASRRouter] Loading Whisper {self.whisper_model_size} model...")
            self._whisper_model = openai_whisper.load_model(self.whisper_model_size)
            print("[ASRRouter] Whisper loaded.")
        return self._whisper_model

    def _estimate_duration_ms(self, audio_bytes: bytes) -> int:
        """Estimate duration from raw PCM bytes (16kHz, 16-bit)."""
        n_samples = len(audio_bytes) // 2  # 2 bytes per sample
        return int(n_samples / TARGET_SAMPLE_RATE * 1000)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TARGET_SAMPLE_RATE = 16_000


def _write_pcm_wav(path: str, pcm_bytes: bytes, sample_rate: int = TARGET_SAMPLE_RATE):
    """Write raw PCM bytes as a proper WAV file."""
    import wave
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)   # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
