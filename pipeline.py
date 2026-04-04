"""
DesiCaptions — Main Pipeline Orchestrator
Ties together: AudioProcessor → ASRRouter → GeminiPostProcessor → SRTBuilder
"""

import os
import time
import tempfile
from typing import Optional, Callable
from dataclasses import dataclass

from modules.audio_processor import AudioProcessor
from modules.asr_router import ASRRouter, TranscriptSegment
from modules.gemini_processor import GeminiPostProcessor, MODE_DESI, MODE_BILINGUAL, MODE_ENGLISH
from modules.srt_builder import SRTBuilder


@dataclass
class PipelineConfig:
    sarvam_api_key: str = ""
    gemini_api_key: str = ""
    whisper_model: str = "medium"   # tiny | base | medium | large-v3
    output_mode: str = MODE_DESI    # desi | bilingual | english
    language: str = "auto"          # auto | hinglish | benglish | tanglish | tenglish | odiaenglish
    prefer_model: str = "sarvam"    # sarvam | whisper
    chunk_ms: int = 3_000
    overlap_ms: int = 500


class DesiCaptionsPipeline:
    """
    End-to-end pipeline: video/audio file → .srt file
    """

    def __init__(self, config: PipelineConfig):
        self.config = config

        self.audio_processor = AudioProcessor(
            chunk_ms=config.chunk_ms,
            overlap_ms=config.overlap_ms,
        )
        self.asr_router = ASRRouter(
            sarvam_api_key=config.sarvam_api_key,
            whisper_model_size=config.whisper_model,
        )
        self.gemini_processor = GeminiPostProcessor(
            api_key=config.gemini_api_key,
        )
        self.srt_builder = SRTBuilder()

    def process_file(
        self,
        input_path: str,
        output_srt_path: Optional[str] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> str:
        """
        Full pipeline: file → SRT.

        Args:
            input_path: path to video or audio file
            output_srt_path: where to write the .srt (auto-named if None)
            progress_callback: fn(progress_0_to_1, status_message)

        Returns:
            Path to generated .srt file
        """
        self.srt_builder.reset()
        start_time = time.time()

        def _progress(pct: float, msg: str):
            if progress_callback:
                progress_callback(pct, msg)
            else:
                print(f"  [{int(pct*100):3d}%] {msg}")

        # Step 1: Audio processing
        _progress(0.0, "Processing audio...")
        chunks, total_duration = self.audio_processor.process_file(input_path)
        _progress(0.1, f"Audio ready: {total_duration:.1f}s → {len(chunks)} chunks")

        if not chunks:
            raise ValueError("No speech detected in audio file.")

        # Step 2: Detect language (from first chunk)
        lang = self.config.language
        if lang == "auto":
            _progress(0.12, "Detecting language...")
            lang = self.asr_router._detect_language_from_audio(chunks[0])
            _progress(0.15, f"Detected: {lang}")

        # Step 3: ASR + Post-process each chunk
        chunk_duration_ms = self.config.chunk_ms
        current_time_ms = 0

        for i, chunk in enumerate(chunks):
            chunk_pct = 0.15 + (i / len(chunks)) * 0.70
            _progress(chunk_pct, f"Transcribing chunk {i+1}/{len(chunks)}...")

            # ASR
            try:
                segment: TranscriptSegment = self.asr_router.transcribe(
                    audio_bytes=chunk,
                    language=lang,
                    prefer_model=self.config.prefer_model,
                )
                raw_text = segment.text.strip()
            except Exception as e:
                print(f"[Pipeline] ASR failed on chunk {i+1}: {e}")
                current_time_ms += chunk_duration_ms
                continue

            if not raw_text:
                current_time_ms += chunk_duration_ms
                continue

            # Gemini post-processing
            try:
                caption_blocks = self.gemini_processor.process(
                    raw_text=raw_text,
                    language=lang,
                    mode=self.config.output_mode,
                )
            except Exception as e:
                print(f"[Pipeline] Gemini failed on chunk {i+1}: {e}")
                # Fallback: use raw text
                from modules.gemini_processor import CaptionBlock
                caption_blocks = [CaptionBlock(text=raw_text, block_index=1)]

            # Add to SRT builder
            block_texts = [b.text for b in caption_blocks]
            self.srt_builder.add_segments_from_chunks(
                caption_blocks=block_texts,
                chunk_start_ms=current_time_ms,
                chunk_duration_ms=chunk_duration_ms,
            )

            current_time_ms += chunk_duration_ms

        # Step 4: Finalize SRT
        _progress(0.85, "Finalizing subtitles...")
        self.srt_builder.merge_short_segments()

        # Step 5: Export
        _progress(0.95, "Exporting SRT...")
        if output_srt_path is None:
            base = os.path.splitext(input_path)[0]
            output_srt_path = f"{base}_{self.config.output_mode}.srt"

        self.srt_builder.export_srt(output_srt_path)
        elapsed = time.time() - start_time

        _progress(1.0, f"Done! {self.srt_builder.segment_count()} captions in {elapsed:.1f}s")
        return output_srt_path

    def get_srt_preview(self, n: int = 10) -> str:
        """Return the first n segments as a string preview."""
        segs = self.srt_builder._segments[:n]
        if not segs:
            return "(no captions yet)"
        from modules.srt_builder import SRTSegment
        return "\n".join(seg.to_srt_block() for seg in segs)
