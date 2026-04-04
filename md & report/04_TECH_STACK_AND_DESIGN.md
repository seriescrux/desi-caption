# Technology Stack & Design Decisions

## DesiCaptions — Why We Chose What We Chose (All Free)

---

## The Free Stack Explained

### 1. Sarvam AI — Primary ASR (Free Tier)

**What:** Indian AI startup's speech recognition model "Saaras" — built specifically for Indian languages.

**Why Sarvam over Google/Azure:**
| Tool | Indian Language WER | Code-Mix Support | Cost |
|---|---|---|---|
| Google Speech API | ~30%+ | Poor | Paid |
| Azure Speech | ~35%+ | Very poor | Paid |
| OpenAI Whisper | ~20-25% | Mediocre | Free but local |
| **Sarvam Saaras** | **~8-12%** | **Good** | **Free tier** |

**Free tier details:**
- Sign up at sarvam.ai → free API key immediately
- No credit card required
- Enough calls per month for student development and demo
- If you hit limits: fallback to Whisper (which is always free)

**Critical feature for DesiCaptions:** Sarvam returns word-level timestamps → essential for accurate SRT generation.

---

### 2. OpenAI Whisper — Secondary ASR (100% Free, Local)

**What:** Open-source ASR model by OpenAI. Runs on your laptop. No internet needed after download.

**Why keep Whisper alongside Sarvam:**
- Handles English portions of code-mixed speech better than Sarvam
- Always available even when Sarvam API is down or rate-limited
- Enables benchmarking comparison (Sarvam vs Whisper vs combined)
- Zero cost, zero API calls — runs on CPU

**Which Whisper model to use:**

| Model | Size | RAM needed | Speed | Accuracy |
|---|---|---|---|---|
| tiny | 75MB | 1GB | Very fast | Low |
| base | 145MB | 1GB | Fast | OK |
| medium | 462MB | 5GB | Medium | Good |
| large-v3 | 1.5GB | 10GB | Slow | Best |

**Recommendation for this project:** Use `medium` on a standard laptop. Use `large-v3` if you have 8GB+ RAM and patience.

```bash
# Install once — model downloads automatically on first use
pip install openai-whisper
```

---

### 3. Google Gemini 1.5 Flash — Post-Processor (Free Tier)

**What:** Google's fast LLM. Used for converting raw ASR output into formatted desi-style captions.

**Free tier limits (as of 2024):**
- 1500 requests per day
- 1 million tokens per day
- Rate limit: 15 requests per minute

**Why this is enough for a student project:**
- A 10-minute video = ~200 Gemini calls
- 1500 requests/day = 7+ full videos per day
- Project demo = maybe 20-30 videos total — well within limits

**Why Gemini over GPT-4 for this project:**
- GPT-4 API requires payment after trial
- Gemini free tier is far more generous
- Gemini performs better on Indic language tasks
- Google AI Studio gives API key instantly — no waitlist

**Get API key:** https://makersuite.google.com → "Get API Key" → free immediately

---

### 4. FastAPI — Backend Framework (Free, Open Source)

**Why FastAPI over Flask:**
- Native async — critical for handling Sarvam API calls + Whisper simultaneously
- WebSocket support built-in (needed for live captioning)
- Auto-generates Swagger docs (looks professional in demo)
- Faster than Flask for concurrent requests

---

### 5. Streamlit — Frontend (Free, Open Source + Free Hosting)

**Why Streamlit for solo developer:**
- Python only — same language as all other code
- 0 CSS/JS knowledge needed
- Built-in: file upload, progress bars, buttons, charts
- Streamlit Community Cloud = free hosting, deploy in 5 minutes
- `st.components.v1.html()` allows embedding custom WebSocket JS for live mode

**Free deployment:**
```bash
# Push to GitHub → go to share.streamlit.io → connect repo → deploy
# Your app lives at: https://yourname-desicaptions.streamlit.app
# For free. Forever.
```

---

## Key Design Decisions

### Decision 1: Preserve Code-Mix as Output (Not "Fix" It)

**Every other tool's approach:** Detect code-mix → separate into two languages → output clean single-language transcript.

**DesiCaptions approach:** Detect code-mix → preserve it → output romanized mixed style.

**Why this is right:**
An Indian content creator who says "aaj ka din bohot accha tha" does NOT want their subtitles to say "today was a very good day." Their audience expects to read it the way it was said. Code-mixing is not an error. It is the language.

This design decision is the core innovation and should be emphasized in every presentation.

---

### Decision 2: Romanization = WhatsApp Style, Not Academic Style

Academic romanization of Hindi: "bahuta acchā thā"
WhatsApp/Indian internet style: "bohot accha tha"

DesiCaptions uses WhatsApp style because:
- That's what Indian audiences read naturally
- That's how Indian content creators write their own captions manually
- It makes the subtitles feel authentic, not machine-generated

The Gemini prompt is specifically engineered to produce WhatsApp-style romanization, not academic transliteration.

---

### Decision 3: Three Output Modes

Why three modes instead of one:

| User Type | Preferred Mode | Reason |
|---|---|---|
| Content creator, Indian audience | Desi Style | Their viewers read Hinglish naturally |
| Creator wanting wider reach | Script + English | Both communities can read |
| Creator targeting global/international | English Only | Non-Indian viewers |
| Accessibility (deaf/HoH, Indian) | Desi Style | Matches their mental model of the speech |
| Educational content | Script + English | Students learn script + English together |

Having all three modes in one tool = DesiCaptions serves every Indian creator's use case.

---

### Decision 4: Auto-Detection, Not Manual Language Selection

**Considered:** Ask user "What language are you speaking?"
**Chosen:** Auto-detect from audio

**Why auto-detect:**
- A content creator shouldn't need to categorize their own speech
- Many creators don't know the linguistic term for what they speak (they just speak it)
- Some creators switch between mixes in one video
- Auto-detection makes the product feel magical and effortless

---

### Decision 5: No Database, No Login

DesiCaptions does not store any user data or videos.

**Why:**
- Privacy — Indian creators may be uploading personal/unreleased content
- No server costs — stateless means no storage bill
- Simpler to build solo
- Every session is fresh — SRT generated on-demand and downloaded immediately

---

## Future Improvements (Document for Report)

1. **More language mixes:** Kannada+English (Kanglish), Malayalam+English, Marathi+English, Punjabi+English
2. **Speaker diarization:** Identify Speaker 1 vs Speaker 2 for interviews/podcasts
3. **YouTube direct upload:** API integration to post SRT directly to YouTube as subtitle track
4. **Custom romanization preferences:** Let creators define their own spellings ("yaar" vs "yar")
5. **Mobile app:** React Native + same FastAPI backend
6. **Chrome extension:** Caption any Indian language video on any website in real time
7. **Batch processing:** Upload 10 videos, get 10 SRT files at once

---

*Document: Tech Stack & Design Decisions v2.0 — DesiCaptions*
