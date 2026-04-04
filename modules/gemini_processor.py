"""
DesiCaptions — Gemini Post-Processing Module
Converts raw ASR output into formatted desi-style captions.
Three output modes: Desi Style | Script+English | English Only
"""

import os
import re
import time
from typing import List, Optional
from dataclasses import dataclass

try:
    from google import genai
    from google.genai import types as genai_types
    GEMINI_AVAILABLE = True
    _GENAI_NEW_SDK = True
except ImportError:
    try:
        import google.generativeai as genai  # legacy fallback
        GEMINI_AVAILABLE = True
        _GENAI_NEW_SDK = False
    except ImportError:
        GEMINI_AVAILABLE = False
        _GENAI_NEW_SDK = False
        print("[GeminiProcessor] Gemini SDK not installed. Run: pip install google-genai")


# ---------------------------------------------------------------------------
# Output modes
# ---------------------------------------------------------------------------

MODE_DESI = "desi"          # Romanized code-mixed (WhatsApp style)
MODE_BILINGUAL = "bilingual"  # Native script + English translation
MODE_ENGLISH = "english"    # Clean English translation only

SUPPORTED_MODES = [MODE_DESI, MODE_BILINGUAL, MODE_ENGLISH]

# Language display names for prompts
LANGUAGE_DISPLAY = {
    "hinglish": "Hinglish (Hindi + English)",
    "benglish": "Benglish (Bengali + English)",
    "tanglish": "Tanglish (Tamil + English)",
    "tenglish": "Tenglish (Telugu + English)",
    "odiaenglish": "Odia + English",
    "hindi": "Hindi",
    "bengali": "Bengali",
    "tamil": "Tamil",
    "telugu": "Telugu",
    "odia": "Odia",
    "english": "English",
}

# WhatsApp-style romanization hints per language
ROMANIZATION_HINTS = {
    "hinglish": "Use common WhatsApp-style Hindi romanization: bohot (not bahut), accha (not acha/achha), yaar (not yar), nahi (not nahin), aaj (not aaj), kya (not kia), toh (not to), mein (not main/mein), hain (not hai when plural), bas (enough), kal (yesterday/tomorrow), abhi (now), phir (again/then), bhi (also).",
    "benglish": "Use common WhatsApp-style Bengali romanization: ami (I), tumi (you), bhalo (good), ki (what), keno (why), ebar (now), ei (this), onek (many/lots).",
    "tanglish": "Use common WhatsApp-style Tamil romanization: naan (I), nee (you), enna (what), vera level (another level), da (informal address), pa (informal address), super (great), sollu (say/tell).",
    "tenglish": "Use common WhatsApp-style Telugu romanization: nenu (I), meeru/nuvvu (you), chala (very), baagundi (good), enti (what), ee (this), anni (all), kaadu (not).",
    "odiaenglish": "Use common WhatsApp-style Odia romanization: mo (my), tu/tume (you), bhala (good), kana (what), ae (this), bahut (very), achi (is/are), hela (happened).",
}

# Native script names for bilingual mode
SCRIPT_INSTRUCTION = {
    "hinglish": "Devanagari script (Hindi)",
    "benglish": "Bengali/Bangla script",
    "tanglish": "Tamil script",
    "tenglish": "Telugu script",
    "odiaenglish": "Odia script",
    "hindi": "Devanagari script",
    "bengali": "Bengali script",
    "tamil": "Tamil script",
    "telugu": "Telugu script",
    "odia": "Odia script",
}

MAX_CHARS_PER_LINE = 42
MAX_LINES_PER_BLOCK = 2
GEMINI_MODEL = "gemini-2.0-flash"
RATE_LIMIT_DELAY = 3.5  # Slightly faster but still safe 


@dataclass
class CaptionBlock:
    text: str        # Formatted caption text (1–2 lines)
    block_index: int


class GeminiPostProcessor:
    """
    Uses Gemini 1.5 Flash to convert raw ASR transcript into
    formatted subtitle blocks in the user's chosen style.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self._last_call_time = 0.0
        self._client = None
        self._model = None

        if GEMINI_AVAILABLE and self.api_key:
            if _GENAI_NEW_SDK:
                self._client = genai.Client(api_key=self.api_key)
            else:
                # Legacy SDK — configure and use model without models/ prefix
                genai.configure(api_key=self.api_key)
                self._model = genai.GenerativeModel(GEMINI_MODEL)
        else:
            if not self.api_key:
                print("[GeminiProcessor] WARNING: GEMINI_API_KEY not set.")
                print("  Get free key at: https://aistudio.google.com")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(
        self,
        raw_text: str,
        language: str,
        mode: str = MODE_DESI,
    ) -> List[CaptionBlock]:
        """
        Convert raw ASR transcript → formatted caption blocks.

        Args:
            raw_text: raw text from Sarvam/Whisper
            language: language key (e.g. "hinglish")
            mode: one of MODE_DESI, MODE_BILINGUAL, MODE_ENGLISH

        Returns:
            List of CaptionBlock objects
        """
        if mode not in SUPPORTED_MODES:
            raise ValueError(f"Invalid mode '{mode}'. Choose from: {SUPPORTED_MODES}")

        if not raw_text.strip():
            return []

        if self._client is None and self._model is None:
            return self._fallback_process(raw_text)

        # Rate limiting for free tier
        self._respect_rate_limit()

        prompt = self._build_prompt(raw_text, language, mode)
        response_text = self._call_gemini(prompt)
        blocks = self._parse_response_to_blocks(response_text, mode)

        return blocks

    def process_chunk_streaming(
        self,
        raw_text: str,
        language: str,
        mode: str = MODE_DESI,
    ) -> str:
        """
        Lighter version for live streaming — returns a single formatted string
        without full block parsing. Faster, fewer tokens.
        """
        if not raw_text.strip() or (self._client is None and self._model is None):
            return raw_text

        self._respect_rate_limit()

        prompt = self._build_streaming_prompt(raw_text, language, mode)
        return self._call_gemini(prompt)

    # ------------------------------------------------------------------
    # Prompt builders
    # ------------------------------------------------------------------

    def _build_prompt(self, raw_text: str, language: str, mode: str) -> str:
        lang_display = LANGUAGE_DISPLAY.get(language, language)

        if mode == MODE_DESI:
            roman_hint = ROMANIZATION_HINTS.get(language, "")
            return f"""You are a subtitle formatter for Indian code-mixed speech.

Language mix: {lang_display}
{roman_hint}

Task: Format the raw ASR transcript into subtitle blocks.
Rules:
1. PRESERVE the code-mixed style EXACTLY — do NOT translate Indian words to English
2. Do NOT translate English words to the Indian language
3. Use WhatsApp-style romanization for Indian words (informal, not academic)
4. Add natural punctuation (commas, periods, question marks)
5. Split into blocks: maximum {MAX_LINES_PER_BLOCK} lines per block, maximum {MAX_CHARS_PER_LINE} characters per line
6. Separate blocks with a blank line
7. Output ONLY the formatted blocks — no explanations, no markdown

Raw transcript:
{raw_text}

Formatted subtitle blocks:"""

        elif mode == MODE_BILINGUAL:
            script = SCRIPT_INSTRUCTION.get(language, "native script")
            return f"""You are a bilingual subtitle formatter for Indian language content.

Language: {lang_display}

Task: Format the raw ASR transcript into bilingual subtitle blocks.
Rules:
1. Line 1: Write the Indian language content in {script}
2. Line 2: Write a natural, informal English translation
3. Keep each line under {MAX_CHARS_PER_LINE} characters
4. Separate blocks with a blank line
5. Output ONLY the formatted blocks — no explanations, no markdown

Raw transcript:
{raw_text}

Formatted bilingual subtitle blocks:"""

        elif mode == MODE_ENGLISH:
            return f"""You are a subtitle translator for Indian language content.

Source language: {lang_display}

Task: Translate and format the raw ASR transcript into English subtitle blocks.
Rules:
1. Translate EVERYTHING to clean, natural English
2. Preserve the informal/casual tone — don't over-formalize
3. Maximum {MAX_LINES_PER_BLOCK} lines per block, maximum {MAX_CHARS_PER_LINE} characters per line
4. Separate blocks with a blank line
5. Output ONLY the formatted blocks — no explanations, no markdown

Raw transcript:
{raw_text}

English subtitle blocks:"""

    def _build_streaming_prompt(self, raw_text: str, language: str, mode: str) -> str:
        lang_display = LANGUAGE_DISPLAY.get(language, language)

        if mode == MODE_DESI:
            roman_hint = ROMANIZATION_HINTS.get(language, "")
            return f"""Fix punctuation and format this {lang_display} caption. {roman_hint}
Keep code-mixed style. Max 42 chars/line. Output only the caption:
{raw_text}"""
        elif mode == MODE_BILINGUAL:
            script = SCRIPT_INSTRUCTION.get(language, "native script")
            return f"""Rewrite as bilingual caption. Line 1: {script}. Line 2: English translation.
Max 42 chars/line. Output only the caption:
{raw_text}"""
        else:
            return f"""Translate this {lang_display} caption to natural English. Max 42 chars/line.
Output only the caption:
{raw_text}"""

    # ------------------------------------------------------------------
    # Gemini API call
    # ------------------------------------------------------------------

    def _call_gemini(self, prompt: str) -> str:
        try:
            if _GENAI_NEW_SDK and self._client:
                response = self._client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt,
                )
                return response.text.strip()
            elif self._model:
                response = self._model.generate_content(prompt)
                return response.text.strip()
            return ""
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                # Extract retry delay if present and wait
                import re
                match = re.search(r"retryDelay.*?(\d+)s", err_str)
                wait = int(match.group(1)) if match else 60
                wait = min(wait, 10)  # Cap at 10s max wait
                print(f"[GeminiProcessor] Rate limited — waiting {wait}s then skipping this chunk")
                time.sleep(wait)
                # Disable Gemini for this session to avoid further spam
                self._model = None
                self._client = None
                print("[GeminiProcessor] Gemini disabled for this session — using raw ASR output")
            else:
                print(f"[GeminiProcessor] Gemini API error: {e}")
            return ""

    # ------------------------------------------------------------------
    # Parse Gemini output → CaptionBlock list
    # ------------------------------------------------------------------

    def _parse_response_to_blocks(self, response_text: str, mode: str) -> List[CaptionBlock]:
        """
        Split Gemini's multi-block response into individual CaptionBlocks.
        Gemini separates blocks with blank lines.
        """
        if not response_text:
            return []

        # Split on blank lines
        raw_blocks = re.split(r"\n\s*\n", response_text.strip())
        blocks = []
        for i, block_text in enumerate(raw_blocks):
            clean = block_text.strip()
            if clean:
                blocks.append(CaptionBlock(text=clean, block_index=i + 1))

        return blocks

    # ------------------------------------------------------------------
    # Fallback (no Gemini)
    # ------------------------------------------------------------------

    def _fallback_process(self, raw_text: str) -> List[CaptionBlock]:
        """
        Basic word-wrap into subtitle blocks when Gemini is unavailable.
        No punctuation enhancement — just line breaking.
        """
        words = raw_text.split()
        blocks = []
        block_idx = 1
        current_line = ""
        lines = []

        for word in words:
            if len(current_line) + len(word) + 1 <= MAX_CHARS_PER_LINE:
                current_line = (current_line + " " + word).strip()
            else:
                lines.append(current_line)
                current_line = word

                if len(lines) == MAX_LINES_PER_BLOCK:
                    blocks.append(CaptionBlock(
                        text="\n".join(lines),
                        block_index=block_idx,
                    ))
                    block_idx += 1
                    lines = []

        if current_line:
            lines.append(current_line)
        if lines:
            blocks.append(CaptionBlock(text="\n".join(lines), block_index=block_idx))

        return blocks

    # ------------------------------------------------------------------
    # Rate limiting
    # ------------------------------------------------------------------

    def _respect_rate_limit(self):
        """Enforce ~15 requests/minute for Gemini free tier."""
        elapsed = time.time() - self._last_call_time
        if elapsed < RATE_LIMIT_DELAY:
            time.sleep(RATE_LIMIT_DELAY - elapsed)
        self._last_call_time = time.time()
