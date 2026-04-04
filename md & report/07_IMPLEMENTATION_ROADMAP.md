# Implementation Roadmap

## DESI-CAPTION — 6-Month Solo Development Plan

---

## Phase Overview

| Phase | Duration | Focus |
|---|---|---|
| Phase 1 | Weeks 1-2 | Setup, API keys, basic transcription |
| Phase 2 | Weeks 3-4 | Audio preprocessing pipeline |
| Phase 3 | Weeks 5-6 | Gemini post-processing |
| Phase 4 | Weeks 7-8 | SRT generation module |
| Phase 5 | Weeks 9-10 | Web UI and WebSocket live captioning |
| Phase 6 | Weeks 11-14 | Benchmarking study |
| Phase 7 | Weeks 15-16 | Testing, bug fixes, documentation |
| Phase 8 | Weeks 17-20 | Report writing, presentation prep |
| Buffer | Weeks 21-24 | Revisions, refinements |

---

## Phase 1: Setup & Proof of Concept (Weeks 1-2)

### Goals
- Set up development environment
- Get API keys for Sarvam AI and Gemini
- Run first successful transcription

### Tasks

**Week 1:**
- [ ] Install Python 3.11, create virtual environment
- [ ] Install dependencies: `pip install openai-whisper fastapi streamlit librosa ffmpeg-python pydub jiwer google-generativeai requests`
- [ ] Create Sarvam AI account at https://www.sarvam.ai → get API key
- [ ] Create Google AI Studio account at https://makersuite.google.com → get Gemini API key
- [ ] Write `hello_world_transcription.py` — send a 5-second Hindi audio clip to Sarvam API and print transcript

**Week 2:**
- [ ] Download and test Whisper locally: `python -c "import whisper; model = whisper.load_model('large-v3')"`
- [ ] Transcribe same Hindi clip with Whisper
- [ ] Compare both outputs side by side
- [ ] Document observations in a simple notes file

### Deliverable
A Python script that takes a .wav file, transcribes it with both Sarvam and Whisper, and prints both results.

---

## Phase 2: Audio Processing Pipeline (Weeks 3-4)

### Goals
- Handle any audio/video format as input
- Preprocess audio for best ASR accuracy

### Tasks

**Week 3:**
- [ ] Install FFmpeg on system
- [ ] Write `audio_processor.py`:
  - `convert_to_wav(input_path)` — converts MP3/MP4/OGG to 16kHz mono WAV
  - `normalize_volume(audio)` — peak normalization
- [ ] Test with MP3, MP4, OGG inputs

**Week 4:**
- [ ] Add noise reduction: `pip install noisereduce`
- [ ] Add Voice Activity Detection:
  - Install `webrtcvad` or use energy-based VAD
  - `is_speech(chunk)` returns True/False
- [ ] Add audio chunking:
  - `chunk_audio(audio, chunk_ms=3000, overlap_ms=500)`
- [ ] Test full preprocessing on a 2-minute Hindi audio file

### Deliverable
`audio_processor.py` module that takes any input file and returns clean 16kHz chunks ready for ASR.

---

## Phase 3: Gemini Post-Processing (Weeks 5-6)

### Goals
- Build and refine the Gemini post-processing layer
- Test on all 4 target languages

### Tasks

**Week 5:**
- [ ] Write `gemini_processor.py`:
  - `process_caption(raw_text, language)` function
  - Test basic prompt for Hindi
  - Iterate on prompt until punctuation is correct

**Week 6:**
- [ ] Extend and test prompt for Odia, Tamil, Telugu
- [ ] Add caption chunking function: splits processed text into 84-char max blocks
- [ ] Build evaluation: show 10 side-by-side comparisons (raw vs processed) to 2-3 friends and collect ratings
- [ ] Document prompt template that works best

### Gemini Prompt (Starting Point — iterate this)
```
You are a post-processor for Indian language speech recognition captions.

Language: {language}
Task: Add punctuation and capitalize properly. Split into lines of max 42 chars each, max 2 lines per block. Do NOT change any words.

Input: {raw_text}
Output (formatted caption blocks only, no explanation):
```

### Deliverable
`gemini_processor.py` with tested, working prompt for all 4 languages.

---

## Phase 4: SRT Generation Module (Weeks 7-8)

### Goals
- Build custom SRT builder with proper timestamp handling

### Tasks

**Week 7:**
- [ ] Write `srt_builder.py` — `SRTBuilder` class:
  - `add_segment(text, start_ms, end_ms)`
  - `format_timestamp(ms)` → "HH:MM:SS,mmm"
  - `export_srt(filepath)`
- [ ] Test with dummy data

**Week 8:**
- [ ] Add quality rules enforcement:
  - Merge segments < 1 second
  - Split segments > 7 seconds
  - Ensure min 84ms gap between segments
- [ ] Test with real Sarvam AI timestamp data
- [ ] Open .srt in VLC to visually verify correctness

### Deliverable
`srt_builder.py` generating correct .srt files verifiable in VLC.

---

## Phase 5: Web UI and Live Captioning (Weeks 9-10)

### Goals
- Build Streamlit web application
- Implement real-time WebSocket captioning

### Tasks

**Week 9:**
- [ ] Create `app.py` — Streamlit app with:
  - File upload widget
  - Language selector
  - Transcribe button
  - Transcript display
  - SRT download button
- [ ] Wire up all modules (audio processor → ASR → Gemini → SRT)
- [ ] Test end-to-end file upload flow

**Week 10:**
- [ ] Add WebSocket for live microphone captioning
  - FastAPI backend: `websocket_server.py`
  - Streamlit frontend: custom HTML component with JS MediaRecorder
- [ ] Test live captioning with microphone input
- [ ] Measure actual latency (target: < 2 seconds)

### Deliverable
Working web application accessible at `localhost:8501`

---

## Phase 6: Benchmarking Study (Weeks 11-14)

### Goals
- Run formal WER comparison: Sarvam AI vs Whisper
- Document results for project report

### Tasks

**Week 11:**
- [ ] Download Kathbath dataset from AI4Bharat GitHub
- [ ] Select 50 clips per language (Hindi, Odia, Tamil, Telugu)
- [ ] Organize into folder structure: `benchmark/hindi/`, `benchmark/odia/`, etc.

**Week 12:**
- [ ] Write `benchmark.py` script:
  - Loops over all 200 clips
  - Transcribes with Sarvam AI → saves to `results/sarvam/`
  - Transcribes with Whisper → saves to `results/whisper/`

**Week 13:**
- [ ] Write `evaluate.py` script:
  - Computes WER for each clip
  - Aggregates by language and model
  - Generates results table

**Week 14:**
- [ ] Create charts with `matplotlib`:
  - Bar chart: WER by language, grouped by model
  - Save as PNG for project report
- [ ] Document findings and write analysis

### Deliverable
Results table + charts ready for project report Chapter 8.

---

## Phase 7: Testing & Polish (Weeks 15-16)

### Tasks
- [ ] Test with 10 different audio files (various accents, quality levels)
- [ ] Fix edge cases (very short audio, corrupted files, API timeouts)
- [ ] Add proper error messages to UI
- [ ] Code cleanup and comments
- [ ] Create `requirements.txt` and `README.md`

---

## Phase 8: Report & Presentation (Weeks 17-20)

### Tasks
- [ ] Fill in benchmarking results in `05_PROJECT_REPORT.md`
- [ ] Add screenshots of working application
- [ ] Write 10-slide PowerPoint presentation
- [ ] Practice 10-minute demo walkthrough
- [ ] Prepare answers to all Q&A questions (see `06_TEACHER_QA_PREP.md`)

---

## Development Environment Setup (Do This First)

```bash
# Create project folder
mkdir desi-caption
cd desi-caption

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Install all dependencies
pip install openai-whisper fastapi streamlit uvicorn librosa pydub \
            ffmpeg-python noisereduce webrtcvad jiwer \
            google-generativeai requests python-dotenv matplotlib

# Create .env file for API keys (NEVER commit this to GitHub)
echo "SARVAM_API_KEY=your_key_here" > .env
echo "GEMINI_API_KEY=your_key_here" >> .env
echo ".env" >> .gitignore
```

---

## Project Folder Structure

```
desi-caption/
├── .env                     # API keys (never commit!)
├── .gitignore
├── requirements.txt
├── README.md
├── app.py                   # Main Streamlit app
├── websocket_server.py      # FastAPI WebSocket backend
├── modules/
│   ├── audio_processor.py
│   ├── asr_router.py        # Sarvam + Whisper routing
│   ├── gemini_processor.py
│   └── srt_builder.py
├── benchmark/
│   ├── benchmark.py         # Run benchmarks
│   ├── evaluate.py          # Compute WER
│   └── data/                # Kathbath clips (gitignored)
├── results/
│   ├── sarvam/
│   ├── whisper/
│   └── charts/
└── docs/
    ├── 01_PROJECT_SYNOPSIS.md
    ├── 02_SYSTEM_ARCHITECTURE.md
    ├── 03_PIPELINE_DOCUMENTATION.md
    ├── 04_TECH_STACK_AND_DESIGN.md
    ├── 05_PROJECT_REPORT.md
    ├── 06_TEACHER_QA_PREP.md
    └── 07_IMPLEMENTATION_ROADMAP.md
```

---

*Document: Implementation Roadmap v1.0 — DESI-CAPTION Project*
