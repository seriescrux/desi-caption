"""
DesiCaptions — Audio Processing Module
Handles all audio ingestion, conversion, chunking, and VAD.
"""

import os
import io
import subprocess
import tempfile
import numpy as np
from pathlib import Path
from typing import List, Tuple

# Optional: noise reduction (graceful fallback if not installed)
try:
    import noisereduce as nr
    NOISE_REDUCE_AVAILABLE = True
except ImportError:
    NOISE_REDUCE_AVAILABLE = False
    print("[AudioProcessor] noisereduce not installed — skipping noise reduction")

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    print("[AudioProcessor] librosa not installed — install for best accuracy")

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("[AudioProcessor] pydub not installed — install for audio chunking")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TARGET_SAMPLE_RATE = 16_000   # Hz — required by both Sarvam and Whisper
TARGET_CHANNELS = 1           # Mono
CHUNK_MS = 3_000              # Default chunk size: 3 seconds
OVERLAP_MS = 500              # Overlap between chunks to avoid word cutoff
VAD_ENERGY_THRESHOLD = 0.01   # Energy threshold for silence detection


class AudioProcessor:
    """
    Converts any audio/video file to 16kHz mono WAV chunks,
    ready for Sarvam AI or Whisper transcription.
    """

    def __init__(self, chunk_ms: int = CHUNK_MS, overlap_ms: int = OVERLAP_MS):
        self.chunk_ms = chunk_ms
        self.overlap_ms = overlap_ms

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_file(self, input_path: str) -> Tuple[List[bytes], float]:
        """
        Full pipeline: convert → normalize → denoise → chunk.

        Returns:
            chunks: list of raw PCM bytes (16kHz, mono, 16-bit)
            duration_seconds: total audio duration
        """
        wav_path = self.convert_to_wav(input_path)
        try:
            audio, sr = self._load_wav(wav_path)
        finally:
            # Clean up converted WAV unless it was the original input
            if wav_path != input_path and os.path.exists(wav_path):
                try:
                    os.unlink(wav_path)
                except Exception:
                    pass

        duration = len(audio) / sr

        audio = self._normalize(audio)
        if NOISE_REDUCE_AVAILABLE:
            audio = self._denoise(audio, sr)

        chunks = self._chunk_audio(audio, sr)
        return chunks, duration

    def process_bytes(self, audio_bytes: bytes, original_ext: str = ".webm") -> Tuple[List[bytes], float]:
        """
        Same pipeline but starting from raw bytes (e.g. from WebSocket mic input).
        """
        with tempfile.NamedTemporaryFile(suffix=original_ext, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        try:
            return self.process_file(tmp_path)
        finally:
            os.unlink(tmp_path)

    # ------------------------------------------------------------------
    # Step 1: Convert to WAV
    # ------------------------------------------------------------------

    def convert_to_wav(self, input_path: str) -> str:
        """
        Use FFmpeg to convert any format (MP4, MP3, OGG, WEBM, MOV, etc.)
        to a 16kHz mono WAV file. Returns path to output WAV.
        Always writes to a temp directory to avoid permission issues.
        """
        input_path = str(input_path)
        # Write to /tmp to avoid read-only or permission issues
        import uuid
        output_path = os.path.join(tempfile.gettempdir(), f"desicaptions_{uuid.uuid4().hex}.wav")

        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-ar", str(TARGET_SAMPLE_RATE),
            "-ac", str(TARGET_CHANNELS),
            "-vn",                  # Drop video stream
            "-acodec", "pcm_s16le", # 16-bit PCM
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"FFmpeg conversion failed:\n{result.stderr}"
            )

        return output_path

    # ------------------------------------------------------------------
    # Step 2: Load
    # ------------------------------------------------------------------

    def _load_wav(self, wav_path: str) -> Tuple[np.ndarray, int]:
        """Load WAV as float32 numpy array."""
        if LIBROSA_AVAILABLE:
            audio, sr = librosa.load(wav_path, sr=TARGET_SAMPLE_RATE, mono=True)
            return audio.astype(np.float32), sr
        else:
            import wave, struct
            with wave.open(wav_path, "rb") as wf:
                n_frames = wf.getnframes()
                raw = wf.readframes(n_frames)
                audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            return audio, TARGET_SAMPLE_RATE

    # ------------------------------------------------------------------
    # Step 3: Normalize volume
    # ------------------------------------------------------------------

    def _normalize(self, audio: np.ndarray) -> np.ndarray:
        """Peak-normalize audio to [-1, 1]."""
        peak = np.max(np.abs(audio))
        if peak > 0:
            audio = audio / peak
        return audio

    # ------------------------------------------------------------------
    # Step 4: Noise reduction (optional)
    # ------------------------------------------------------------------

    def _denoise(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Apply spectral noise reduction using noisereduce library."""
        try:
            reduced = nr.reduce_noise(y=audio, sr=sr, stationary=False)
            return reduced.astype(np.float32)
        except Exception as e:
            print(f"[AudioProcessor] Noise reduction failed ({e}), continuing without")
            return audio

    # ------------------------------------------------------------------
    # Step 5: Chunk audio
    # ------------------------------------------------------------------

    def _chunk_audio(self, audio: np.ndarray, sr: int) -> List[bytes]:
        """
        Split audio into overlapping chunks and convert to PCM bytes.
        Each chunk is self.chunk_ms milliseconds with self.overlap_ms overlap.
        """
        chunk_samples = int(sr * self.chunk_ms / 1000)
        overlap_samples = int(sr * self.overlap_ms / 1000)
        step_samples = chunk_samples - overlap_samples

        chunks = []
        start = 0
        while start < len(audio):
            end = min(start + chunk_samples, len(audio))
            chunk = audio[start:end]

            # Only include chunks with actual speech
            if self._is_speech(chunk):
                pcm_bytes = self._float32_to_pcm16(chunk)
                chunks.append(pcm_bytes)

            start += step_samples

        return chunks

    # ------------------------------------------------------------------
    # VAD — Voice Activity Detection
    # ------------------------------------------------------------------

    def _is_speech(self, chunk: np.ndarray, threshold: float = VAD_ENERGY_THRESHOLD) -> bool:
        """
        Simple energy-based VAD.
        Returns True if the chunk likely contains speech.
        """
        if len(chunk) == 0:
            return False
        rms = np.sqrt(np.mean(chunk ** 2))
        return rms > threshold

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def _float32_to_pcm16(self, audio: np.ndarray) -> bytes:
        """Convert float32 numpy array to 16-bit PCM bytes."""
        clipped = np.clip(audio, -1.0, 1.0)
        pcm = (clipped * 32767).astype(np.int16)
        return pcm.tobytes()

    def get_duration_seconds(self, input_path: str) -> float:
        """Get audio duration using FFprobe."""
        cmd = [
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            input_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        try:
            return float(result.stdout.strip())
        except Exception:
            return 0.0
