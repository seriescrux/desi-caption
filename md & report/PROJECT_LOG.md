# DesiCaptions — Project Development Log

**Project:** DesiCaptions: AI-Powered Code-Mixed Subtitle Generator for Indian Content Creators
**Stack:** Sarvam AI + OpenAI Whisper + Google Gemini 1.5 Flash + FastAPI + Streamlit
**Total Budget:** ₹0

---

## Session Log

### Session 1 — [Date: Current]

**Status:** ✅ BACKEND + FRONTEND COMPLETE

#### Completed This Session
- [x] Backend modules — ALL DONE
- [x] Frontend Streamlit app — DONE (`app.py`)

#### Next Steps
- [ ] Add your API keys to `.env` (copy from `.env.example`)
- [ ] Run: `pip install -r requirements.txt`
- [ ] Run: `streamlit run app.py`
- [ ] Run benchmarking study (Phase 6) — needs Kathbath dataset
- [ ] Fill in WER numbers in `05_PROJECT_REPORT.md`

---

## Build Order (Backend First)

### ✅ BACKEND COMPLETE
- [x] `modules/audio_processor.py` — FFmpeg + chunking + VAD + noise reduction
- [x] `modules/asr_router.py` — Sarvam AI + Whisper routing + language detection
- [x] `modules/gemini_processor.py` — 3-mode Gemini post-processing + rate limiting
- [x] `modules/srt_builder.py` — SRT generation, timestamps, quality rules
- [x] `pipeline.py` — Main orchestrator tying all modules together
- [x] `websocket_server.py` — FastAPI WebSocket backend for live mic
- [x] `benchmark/benchmark.py` — WER benchmarking script (Sarvam vs Whisper)
- [x] `benchmark/evaluate.py` — WER evaluation + matplotlib charts
- [x] `requirements.txt` — all dependencies
- [x] `.env.example` — API key template

### ✅ FRONTEND COMPLETE
- [x] `app.py` — Streamlit frontend (3 tabs: File Upload · Live Mic · How It Works)

---

## Architecture Decisions Log

| Decision | Rationale |
|----------|-----------|
| Dual ASR (Sarvam + Whisper) | Sarvam better for Indic words, Whisper for English portions |
| Gemini post-processor | Semantic punctuation handles Indian lang better than rule-based |
| 3-sec audio chunks | Empirically balances latency vs accuracy |
| No database | Privacy + zero storage cost, stateless design |
| Streamlit frontend | Python-only, free hosting on Community Cloud |

---

## API Keys Needed

| Service | Where to get | Status |
|---------|-------------|--------|
| Sarvam AI | https://www.sarvam.ai (free, no CC) | ⏳ Pending |
| Google Gemini | https://makersuite.google.com (free) | ⏳ Pending |

---

## Notes & Issues

- (Log issues here as you build)

---

*Log started: Session 1*
