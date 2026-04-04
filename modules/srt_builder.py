"""
DesiCaptions — SRT Builder Module
Generates industry-standard .srt subtitle files from caption blocks + timestamps.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class SRTSegment:
    index: int
    start_ms: int
    end_ms: int
    text: str       # 1–2 lines of caption text

    def to_srt_block(self) -> str:
        """Render as a standard SRT block."""
        start = _ms_to_srt_timestamp(self.start_ms)
        end = _ms_to_srt_timestamp(self.end_ms)
        return f"{self.index}\n{start} --> {end}\n{self.text}\n"


# ---------------------------------------------------------------------------
# SRT quality constants (broadcast-standard)
# ---------------------------------------------------------------------------

MIN_SEGMENT_DURATION_MS = 1_000     # Don't show a caption for < 1 second
MAX_SEGMENT_DURATION_MS = 7_000     # Caption blocks longer than 7s should be split
MIN_GAP_BETWEEN_SEGMENTS_MS = 84    # BBC/Netflix standard minimum gap
MAX_CHARS_PER_LINE = 42             # Broadcast standard
MAX_LINES_PER_SEGMENT = 2


class SRTBuilder:
    """
    Accumulates transcript segments and exports a valid .srt file.

    Usage:
        builder = SRTBuilder()
        builder.add_segment("aaj ka din bohot accha tha,\nit was amazing yaar", 1000, 4500)
        builder.add_segment("let's get started yaar", 5000, 7200)
        builder.export_srt("output.srt")
    """

    def __init__(self):
        self._segments: List[SRTSegment] = []
        self._counter = 1

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_segment(self, text: str, start_ms: int, end_ms: int) -> None:
        """
        Add a single caption segment.
        Applies quality rules automatically.
        """
        if not text.strip():
            return

        # Enforce minimum duration
        duration = end_ms - start_ms
        if duration < MIN_SEGMENT_DURATION_MS:
            end_ms = start_ms + MIN_SEGMENT_DURATION_MS

        # Enforce maximum duration — split if too long
        if end_ms - start_ms > MAX_SEGMENT_DURATION_MS:
            self._add_long_segment(text, start_ms, end_ms)
            return

        # Ensure gap from previous segment
        if self._segments:
            prev = self._segments[-1]
            if start_ms - prev.end_ms < MIN_GAP_BETWEEN_SEGMENTS_MS:
                start_ms = prev.end_ms + MIN_GAP_BETWEEN_SEGMENTS_MS

        # Enforce line limits
        text = self._enforce_line_limits(text)

        seg = SRTSegment(
            index=self._counter,
            start_ms=start_ms,
            end_ms=end_ms,
            text=text,
        )
        self._segments.append(seg)
        self._counter += 1

    def add_segments_from_chunks(
        self,
        caption_blocks: List[str],
        chunk_start_ms: int,
        chunk_duration_ms: int,
    ) -> None:
        """
        Given a list of caption block texts for a single audio chunk,
        distribute timestamps evenly across the blocks.
        """
        if not caption_blocks:
            return

        n = len(caption_blocks)
        block_duration = chunk_duration_ms // n

        for i, text in enumerate(caption_blocks):
            start = chunk_start_ms + i * block_duration
            end = start + block_duration
            self.add_segment(text, start, end)

    def export_srt(self, filepath: str) -> str:
        """Write the .srt file to disk. Returns the filepath."""
        content = self.to_string()
        Path(filepath).write_text(content, encoding="utf-8")
        return filepath

    def to_string(self) -> str:
        """Return the full SRT content as a string."""
        if not self._segments:
            return ""
        blocks = [seg.to_srt_block() for seg in self._segments]
        return "\n".join(blocks)

    def reset(self) -> None:
        """Clear all segments (for reuse across sessions)."""
        self._segments = []
        self._counter = 1

    def segment_count(self) -> int:
        return len(self._segments)

    # ------------------------------------------------------------------
    # Quality enforcement
    # ------------------------------------------------------------------

    def _enforce_line_limits(self, text: str) -> str:
        """
        Ensure caption text has max 2 lines, each <= 42 chars.
        Wraps intelligently at word boundaries.
        """
        lines = text.strip().splitlines()
        result_lines = []

        for line in lines:
            if len(line) <= MAX_CHARS_PER_LINE:
                result_lines.append(line)
            else:
                # Word-wrap the long line
                wrapped = _word_wrap(line, MAX_CHARS_PER_LINE)
                result_lines.extend(wrapped)

        # Cap at 2 lines
        if len(result_lines) > MAX_LINES_PER_SEGMENT:
            result_lines = result_lines[:MAX_LINES_PER_SEGMENT]

        return "\n".join(result_lines)

    def _add_long_segment(self, text: str, start_ms: int, end_ms: int) -> None:
        """Split a long segment into multiple shorter ones."""
        words = text.split()
        mid = len(words) // 2
        mid_ms = start_ms + (end_ms - start_ms) // 2

        part1 = " ".join(words[:mid])
        part2 = " ".join(words[mid:])

        self.add_segment(part1, start_ms, mid_ms)
        self.add_segment(part2, mid_ms, end_ms)

    # ------------------------------------------------------------------
    # Merge/finalize (call after all segments added)
    # ------------------------------------------------------------------

    def merge_short_segments(self, min_ms: int = MIN_SEGMENT_DURATION_MS) -> None:
        """
        Merge consecutive segments that are too short to display comfortably.
        Call once after all add_segment() calls are done.
        """
        if len(self._segments) < 2:
            return

        merged = [self._segments[0]]
        for seg in self._segments[1:]:
            prev = merged[-1]
            combined_text = prev.text + " " + seg.text

            # Merge if previous is too short and combined fits in 2 lines
            if (prev.end_ms - prev.start_ms < min_ms and
                    len(combined_text.splitlines()) <= MAX_LINES_PER_SEGMENT):
                merged[-1] = SRTSegment(
                    index=prev.index,
                    start_ms=prev.start_ms,
                    end_ms=seg.end_ms,
                    text=self._enforce_line_limits(combined_text),
                )
            else:
                merged.append(seg)

        # Re-index
        for i, seg in enumerate(merged, 1):
            seg.index = i
        self._segments = merged
        self._counter = len(merged) + 1


# ---------------------------------------------------------------------------
# Timestamp formatting
# ---------------------------------------------------------------------------

def _ms_to_srt_timestamp(ms: int) -> str:
    """Convert milliseconds to SRT timestamp: HH:MM:SS,mmm"""
    ms = max(0, ms)
    hours = ms // 3_600_000
    ms %= 3_600_000
    minutes = ms // 60_000
    ms %= 60_000
    seconds = ms // 1_000
    millis = ms % 1_000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def _word_wrap(text: str, max_chars: int) -> List[str]:
    """Wrap text at word boundaries to max_chars per line."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= max_chars:
            current += " " + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# ---------------------------------------------------------------------------
# Utility: parse existing SRT
# ---------------------------------------------------------------------------

def parse_srt(srt_content: str) -> List[SRTSegment]:
    """Parse an existing SRT string back into SRTSegment objects."""
    segments = []
    blocks = re.split(r"\n\s*\n", srt_content.strip())

    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) < 3:
            continue
        try:
            index = int(lines[0].strip())
            ts_line = lines[1].strip()
            start_str, end_str = ts_line.split(" --> ")
            start_ms = _srt_timestamp_to_ms(start_str)
            end_ms = _srt_timestamp_to_ms(end_str)
            text = "\n".join(lines[2:])
            segments.append(SRTSegment(index=index, start_ms=start_ms, end_ms=end_ms, text=text))
        except Exception:
            continue

    return segments


def _srt_timestamp_to_ms(ts: str) -> int:
    """Parse HH:MM:SS,mmm → milliseconds."""
    ts = ts.strip()
    h, m, rest = ts.split(":")
    s, ms = rest.split(",")
    return int(h) * 3_600_000 + int(m) * 60_000 + int(s) * 1_000 + int(ms)
