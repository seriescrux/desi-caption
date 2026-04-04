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
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("[GeminiProcessor] google-generativeai not installed. Run: pip install google-generativeai")


# ---------------------------------------------------------------------------
# Output modes
# ---------------------------------------------------------------------------

MODE_DESI = "desi"
MODE_BILINGUAL = "bilingual"
MODE_ENGLISH = "english"

SUPPORTED_MODES = [MODE_DESI, MODE_BILINGUAL, MODE_ENGLISH]

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

ROMANIZATION_HINTS = {
    "hinglish": "Use WhatsApp-style Hindi romanization: bohot (not bahut), accha (not acha/achha), yaar (not yar), nahi (not nahin), kya (not kia), toh (not to), mein, hain, bas, abhi, phir, bhi.",
    "benglish": "Use WhatsApp-style Bengali romanization: ami (I), tumi (you), bhalo (good), ki (what), keno (why), ebar (now), ei (this), onek (many).",
    "tanglish": "Use WhatsApp-style Tamil romanization: naan (I), nee (you), enna (what), vera level (another level), da, pa, super, sollu.",
    "tenglish": "Use WhatsApp-style Telugu romanization: nenu (I), meeru/nuvvu (you), chala (very), baagundi (good), enti (what), ee (this), anni (all), kaadu (not).",
    "odiaenglish": "Use WhatsApp-style Odia romanization: mo (my), tu/tume (you), bhala (good), kana (what), ae (this), bahut (very), achi (is/are).",
}

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
RATE_LIMIT_DELAY = 4.1


@dataclass
class CaptionBlock:
    text: str
    block_index: int


# ---------------------------------------------------------------------------
# BOM-safe .env reader — fixes Windows UTF-8 BOM issue with python-dotenv
# ---------------------------------------------------------------------------

def _read_env_file_directly() -> dict:
    """
    Manually read .env file with utf-8-sig encoding to strip Windows BOM.
    This is a fallback for when python-dotenv fails due to BOM encoding.
    """
    env_vars = {}
    # Look for .env in project root (parent of modules/)
    search_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'),
        os.path.join(os.getcwd(), '.env'),
    ]
    for env_path in search_paths:
        env_path = os.path.normpath(env_path)
        if os.path.exists(env_path):
            try:
                with open(env_path, 'r', encoding='utf-8-sig') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, _, val = line.partition('=')
                            env_vars[key.strip()] = val.strip().strip('"').strip("'")
                print(f"[GeminiProcessor] Loaded .env from {env_path}")
                break
            except Exception as e:
                print(f"[GeminiProcessor] Could not read {env_path}: {e}")
    return env_vars


class GeminiPostProcessor:
    """
    Uses Gemini 1.5 Flash to convert raw ASR transcript into
    formatted subtitle blocks in the user's chosen style.
    """

    def __init__(self, api_key: Optional[str] = None):
        # 3-layer key resolution: passed → os.getenv → direct .env file read (BOM-safe)
        env_file = _read_env_file_directly()

        self.api_key = (
            api_key or
            os.getenv("GEMINI_API_KEY", "") or
            env_file.get("GEMINI_API_KEY", "")
        ).strip()

        self._last_call_time = 0.0

        if GEMINI_AVAILABLE and self.api_key:
            self._client = genai.Client(api_key=self.api_key)
            self._model = GEMINI_MODEL
            print(f"[GeminiProcessor] ✓ Gemini ready (key ends: ...{self.api_key[-6:]})")
        else:
            self._client = None
            self._model = None
            print("[GeminiProcessor] WARNING: GEMINI_API_KEY not found — captions will be raw ASR output.")
            print("  Fix: ensure .env has GEMINI_API_KEY=your_key (no quotes, no BOM)")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(
        self,
        raw_text: str,
        language: str,
        mode: str = MODE_DESI,
    ) -> List[CaptionBlock]:
        if mode not in SUPPORTED_MODES:
            raise ValueError(f"Invalid mode '{mode}'. Choose from: {SUPPORTED_MODES}")

        if not raw_text.strip():
            return []

        if not hasattr(self, "_client") or self._client is None:
            return self._fallback_process(raw_text)

        self._respect_rate_limit()

        prompt = self._build_prompt(raw_text, language, mode)
        response_text = self._call_gemini(prompt)

        # If Gemini returns empty, fall back — but don't disable permanently
        if not response_text:
            return self._fallback_process(raw_text)

        return self._parse_response_to_blocks(response_text, mode)

    def process_chunk_streaming(
        self,
        raw_text: str,
        language: str,
        mode: str = MODE_DESI,
    ) -> str:
        if not raw_text.strip() or not hasattr(self, "_client") or self._client is None:
            return raw_text

        self._respect_rate_limit()
        prompt = self._build_streaming_prompt(raw_text, language, mode)
        result = self._call_gemini(prompt)
        return result if result else raw_text

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

IMPORTANT: The input may be in Hindi/Devanagari script. Convert ALL Indian language words to romanized WhatsApp style. Keep English words as-is.

Task: Format the raw ASR transcript into subtitle blocks.
Rules:
1. Convert Hindi/Devanagari script to romanized WhatsApp style (e.g. "kya baat hai yaar" not "क्या बात है")
2. Keep English words exactly as they are
3. Preserve the natural code-mixed flow
4. Add natural punctuation
5. Max {MAX_LINES_PER_BLOCK} lines per block, max {MAX_CHARS_PER_LINE} chars per line
6. Separate blocks with a blank line
7. Output ONLY the subtitle blocks — no explanations

Raw transcript:
{raw_text}

Romanized Hinglish subtitle blocks:"""

        elif mode == MODE_BILINGUAL:
            script = SCRIPT_INSTRUCTION.get(language, "native script")
            return f"""You are a bilingual subtitle formatter for Indian language content.

Language: {lang_display}

Rules:
1. Line 1: Write in {script}
2. Line 2: Natural English translation
3. Max {MAX_CHARS_PER_LINE} chars per line
4. Separate blocks with blank line
5. Output ONLY the blocks

Raw transcript:
{raw_text}

Bilingual subtitle blocks:"""

        elif mode == MODE_ENGLISH:
            return f"""You are a subtitle translator for Indian language content.

Source language: {lang_display}

Rules:
1. Translate everything to natural, informal English
2. Max {MAX_LINES_PER_BLOCK} lines per block, max {MAX_CHARS_PER_LINE} chars per line
3. Separate blocks with blank line
4. Output ONLY the blocks

Raw transcript:
{raw_text}

English subtitle blocks:"""

    def _build_streaming_prompt(self, raw_text: str, language: str, mode: str) -> str:
        lang_display = LANGUAGE_DISPLAY.get(language, language)
        if mode == MODE_DESI:
            roman_hint = ROMANIZATION_HINTS.get(language, "")
            return f"""Convert this {lang_display} caption to romanized WhatsApp style. {roman_hint}
If input is in Devanagari/native script, romanize it. Keep English as-is. Max 42 chars/line.
Output only the caption:
{raw_text}"""
        elif mode == MODE_BILINGUAL:
            script = SCRIPT_INSTRUCTION.get(language, "native script")
            return f"""Rewrite as bilingual caption. Line 1: {script}. Line 2: English translation.
Max 42 chars/line. Output only:
{raw_text}"""
        else:
            return f"""Translate this {lang_display} caption to natural English. Max 42 chars/line.
Output only:
{raw_text}"""

    # ------------------------------------------------------------------
    # Gemini API call
    # ------------------------------------------------------------------

    def _call_gemini(self, prompt: str) -> str:
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            print(f"[GeminiProcessor] API error: {e}")
            return ""

    # ------------------------------------------------------------------
    # Parse Gemini output → CaptionBlock list
    # ------------------------------------------------------------------

    def _parse_response_to_blocks(self, response_text: str, mode: str) -> List[CaptionBlock]:
        if not response_text:
            return []
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
                    blocks.append(CaptionBlock(text="\n".join(lines), block_index=block_idx))
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
