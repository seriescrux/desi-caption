# System Architecture

## DesiCaptions — Code-Mixed Indian Speech Subtitle Generator

---

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE LAYER                      │
│      Streamlit Web App — Upload Video / Live Mic Input           │
│      Language Mix Selector | Output Format Selector              │
│      [Desi Style] [Script+English] [English Only]                │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                 Audio/Video Input
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│                    AUDIO PROCESSING LAYER                        │
│   FFmpeg Extract → 16kHz Mono WAV → Noise Reduction → Chunks    │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│               CODE-MIX AUTO DETECTION LAYER                     │
│   Detect dominant language family + English mix percentage       │
│   → Hinglish / Benglish / Tanglish / Tenglish / Odia+Eng        │
└──────────┬───────────────────────────────────────┬───────────────┘
           │                                       │
    Indic-dominant                          English-dominant
           │                                       │
┌──────────▼────────────┐             ┌────────────▼──────────────┐
│   SARVAM AI (Free)    │             │  OPENAI WHISPER (Local)   │
│   Saaras ASR Model    │             │  whisper-large-v3         │
│   REST API call       │             │  Runs on your machine     │
│   Hindi/Bengali/      │             │  Free — no API needed     │
│   Tamil/Telugu/Odia   │             │  English + fallback       │
└──────────┬────────────┘             └────────────┬──────────────┘
           │                                       │
           └──────────────┬────────────────────────┘
                          │
              Raw transcript + word timestamps
                          │
┌─────────────────────────▼────────────────────────────────────────┐
│                 GEMINI POST-PROCESSING LAYER (Free)              │
│                                                                  │
│   ┌─────────────────┐ ┌─────────────────┐ ┌──────────────────┐  │
│   │  MODE 1:        │ │  MODE 2:         │ │  MODE 3:         │  │
│   │  Desi Style     │ │  Script+English  │ │  English Only    │  │
│   │                 │ │                  │ │                  │  │
│   │ Preserve exact  │ │ Line 1: Script   │ │ Clean English    │  │
│   │ code-mixed mix  │ │ Line 2: English  │ │ translation      │  │
│   │ Romanize Indian │ │ translation      │ │                  │  │
│   │ words naturally │ │                  │ │                  │  │
│   └────────┬────────┘ └────────┬─────────┘ └───────┬──────────┘  │
└────────────┼───────────────────┼───────────────────┼─────────────┘
             └───────────────────┼───────────────────┘
                                 │
                    Formatted caption blocks + timestamps
                                 │
              ┌──────────────────┴─────────────────┐
              │                                    │
┌─────────────▼──────────┐          ┌──────────────▼────────────┐
│   LIVE CAPTION ENGINE  │          │   SRT GENERATION MODULE   │
│   WebSocket broadcast  │          │   Custom SRTBuilder class │
│   Real-time display    │          │   .srt file export        │
└────────────────────────┘          └───────────────────────────┘
```

---

## The Code-Mix Auto Detection Layer (Core Innovation)

This is the most technically interesting part of DesiCaptions and the key differentiator from any existing tool.

### What it does

Given an audio chunk, it determines:
1. What is the dominant Indian language? (Hindi / Bengali / Tamil / Telugu / Odia)
2. What percentage is English mixed in?
3. What romanization style is the speaker using? (WhatsApp-style: "accha", "bahut", "yaar")

### How it works (3-step approach)

```
Step 1: Language Family Detection
   → Send first 10 seconds to Sarvam AI with language_code = "auto"
   → Sarvam returns detected language (hi, bn, ta, te, or)
   → This tells us: "this person is a Hindi speaker"

Step 2: Code-Mix Ratio Estimation
   → Also run same chunk through Whisper
   → Compare: how many words did Whisper recognize as English?
   → If > 20% English words detected → code-mixed speech confirmed
   → If < 20% → mostly pure regional language

Step 3: Style Classification
   → Route to correct Gemini prompt for that language pair
   → Hinglish prompt ≠ Tanglish prompt ≠ Benglish prompt
   → Each prompt is tuned for that community's natural style
```

### Why not just use one model for everything?

No single ASR model handles code-mixed Indian speech well today. Sarvam AI is excellent at the Indic words; Whisper is excellent at the English words. By using both and combining their outputs intelligently, DesiCaptions gets better coverage than either alone.

---

## Gemini Post-Processing — 3 Mode Prompts

### Mode 1: Desi Style Prompt

```
You are a subtitle formatter for Indian code-mixed speech (Hinglish/Benglish/Tanglish etc).

Language mix detected: {language_mix}  (e.g. "Hinglish")
Raw ASR transcript: {raw_text}

Your job:
1. Keep the exact code-mixed style — do NOT translate Indian words to English
2. Do NOT translate English words to the Indian language
3. Romanize Indian words the WhatsApp way (accha not acha, yaar not yar, bohot not bahut etc)
4. Add punctuation naturally
5. Format into subtitle blocks: max 2 lines, max 42 chars per line

Output ONLY the formatted subtitle blocks, nothing else.
Example style: "aaj ka din bohot accha tha, it was amazing yaar"
```

### Mode 2: Script + English Prompt

```
You are a bilingual subtitle formatter for Indian language content.

Language: {language}  (e.g. "Hindi")
Raw transcript: {raw_text}

Your job:
1. Line 1: Write the Indian language words in their NATIVE SCRIPT (Devanagari/Bengali/Tamil/Telugu/Odia)
2. Line 2: Write a natural English translation
3. Format into blocks: max 42 chars per line

Output ONLY formatted blocks, nothing else.
Example:
आज का दिन बहुत अच्छा था
Today was a really good day
```

### Mode 3: English Only Prompt

```
You are a subtitle translator for Indian language content.

Source language mix: {language_mix}
Raw transcript: {raw_text}

Your job:
1. Translate everything to clean, natural English
2. Preserve the casual/informal tone — don't make it too formal
3. Format into blocks: max 2 lines, 42 chars each

Output ONLY formatted subtitle blocks.
```

---

## SRT Output Examples Per Mode

### Input Speech (Hinglish):
*"Aaj ka video mein hum dekhenge how to make the perfect chai at home, toh let's get started yaar"*

---

**Mode 1 — Desi Style SRT:**
```
1
00:00:01,000 --> 00:00:05,200
aaj ka video mein hum dekhenge
how to make the perfect chai

2
00:00:05,400 --> 00:00:07,800
at home, toh let's get
started yaar
```

**Mode 2 — Script + English SRT:**
```
1
00:00:01,000 --> 00:00:05,200
आज के वीडियो में हम देखेंगे
how to make the perfect chai

2
00:00:05,400 --> 00:00:07,800
घर पर, तो चलिए शुरू करते हैं
Let's get started, friends
```

**Mode 3 — English Only SRT:**
```
1
00:00:01,000 --> 00:00:05,200
In today's video, we'll see
how to make the perfect chai

2
00:00:05,400 --> 00:00:07,800
at home. Let's get
started, folks!
```

---

## Free Tier Architecture — How to Stay at ₹0

| Component | Free Strategy |
|---|---|
| **Sarvam AI** | Free tier: ~1000 API calls/month. For a 10-min video at 3-sec chunks = 200 calls. 5 full videos/month free. |
| **Whisper** | Runs 100% locally on your laptop. No API. No cost ever. Use `whisper-large-v3` or `whisper-medium` if RAM is limited. |
| **Gemini 1.5 Flash** | Free tier: 1500 requests/day, 1M tokens/day. More than enough for a student project. |
| **Hosting** | Streamlit Community Cloud — free forever for public apps. |
| **Storage** | No database needed. SRT files generated on-the-fly and downloaded. |

### Sarvam AI Free Tier — How to Get It
1. Go to https://www.sarvam.ai
2. Sign up for developer account
3. Free API key issued immediately
4. No credit card required for free tier
5. Rate limit: check current limits on their dashboard (they update this)

### Whisper Local Setup (Free)
```bash
pip install openai-whisper
# First run downloads the model (~1.5GB for large-v3, ~460MB for medium)
# After that — completely offline, zero cost
python -c "import whisper; model = whisper.load_model('medium'); print('ready')"
```

Use `whisper-medium` if your laptop has less than 8GB RAM. Accuracy is slightly lower but still good.

---

## Technology Stack

| Layer | Tool | Cost |
|---|---|---|
| ASR Primary | Sarvam AI Saaras | Free |
| ASR Secondary | Whisper medium/large-v3 | Free (local) |
| LLM Post-Processor | Gemini 1.5 Flash | Free |
| Backend | FastAPI + Python | Free |
| Real-time | WebSockets (FastAPI) | Free |
| Frontend | Streamlit | Free |
| Hosting | Streamlit Community Cloud | Free |
| Audio processing | FFmpeg + librosa + pydub | Free |
| SRT generation | Custom Python module | Free |
| Benchmarking | jiwer Python library | Free |

---

*Document: System Architecture v2.0 — DesiCaptions*
