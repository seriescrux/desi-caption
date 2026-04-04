# DesiCaptions 🎬
## AI-Powered Code-Mixed Subtitle Generator for Indian Content Creators

> Final Year Major Project — B.Tech Computer Science & IT
> Total Cost: ₹0 | Stack: Sarvam AI + Whisper + Gemini

---

## What is DesiCaptions?

Indian content creators speak in **Hinglish, Tanglish, Benglish** — not pure Hindi, not pure English. Existing auto-caption tools destroy this natural style by forcing it into one language.

**DesiCaptions preserves it.**

Upload your video → get subtitles that sound exactly like you.

```
You said:  "aaj ka video mein hum dekhenge how to make chai, let's get started yaar"

Google:    "Today's video we will see how to make tea let's get started"  ❌
YouTube:   "आज का वीडियो में हम देखेंगे हाउ टू मेक चाय"               ❌
DesiCaptions: "aaj ka video mein hum dekhenge how to make chai,
               let's get started yaar"                                    ✅
```

---

## Three Output Modes

| Mode | Style | Example |
|---|---|---|
| 🎯 Desi Style | Romanized code-mixed (default) | "aaj ka din bohot accha tha, it was amazing yaar" |
| 🔤 Script + English | Native script + English translation | "आज का दिन बहुत अच्छा था / Today was a really good day" |
| 🌍 English Only | Clean English translation | "Today was a really great day, it was truly amazing" |

---

## Supported Language Mixes (Auto-Detected)

- 🟠 **Hinglish** — Hindi + English (600M+ speakers)
- 🟢 **Benglish** — Bengali + English (100M+ speakers)
- 🔵 **Tanglish** — Tamil + English (80M+ speakers)
- 🟣 **Tenglish** — Telugu + English (96M+ speakers)
- 🔴 **Odia+English** — Odia + English (50M+ speakers)

No language selection needed — auto-detects from your audio.

---

## Project Documents Index

| # | Document | What's Inside |
|---|---|---|
| 01 | [Project Synopsis](01_PROJECT_SYNOPSIS.md) | 1-page summary to show teacher |
| 02 | [System Architecture](02_SYSTEM_ARCHITECTURE.md) | Full architecture + free tier strategy |
| 03 | [Pipeline Documentation](03_PIPELINE_DOCUMENTATION.md) | All 5 processing pipelines in detail |
| 04 | [Tech Stack & Design](04_TECH_STACK_AND_DESIGN.md) | Why each tool, all free |
| 05 | [Project Report](05_PROJECT_REPORT.md) | Full formal report template |
| 06 | [Teacher Q&A Prep](06_TEACHER_QA_PREP.md) | 10 questions + exact answers |
| 07 | [Implementation Roadmap](07_IMPLEMENTATION_ROADMAP.md) | Week-by-week build plan |

---

## 100% Free Tech Stack

```
Audio → Sarvam AI (free) + Whisper (local) → Gemini (free) → SRT
```

| Tool | Purpose | Cost |
|---|---|---|
| Sarvam AI Saaras | Indian language ASR | Free tier |
| OpenAI Whisper | English ASR + fallback | Free (local) |
| Google Gemini 1.5 Flash | Desi style formatting | Free tier |
| FastAPI | Backend + WebSockets | Free |
| Streamlit | Web UI + hosting | Free |

---

## What Makes This a Strong Final Year Project

1. **Novel problem** — No tool generates code-mixed SRT subtitles today
2. **Indian-first** — Built for 500M+ Indian content creators
3. **Research component** — WER benchmarking on code-mixed audio (Kathbath dataset, AI4Bharat IIT Madras)
4. **Three output modes** — Shows design thinking for different user needs
5. **100% free** — Demonstrates resourcefulness and real-world constraint solving
6. **Social impact** — Accessibility for deaf/HoH Indians + empowers creators

---

*DesiCaptions — Final Year Major Project — 2024-25*
