# Project Synopsis

## DesiCaptions — AI-Powered Code-Mixed Subtitle Generator for Indian Content Creators

---

### Basic Information

| Field | Details |
|---|---|
| Project Title | DesiCaptions: AI-Powered Code-Mixed Subtitle Generator for Indian Content Creators |
| Short Name | DesiCaptions |
| Branch | Computer Science & Information Technology |
| Project Type | Final Year Major Project |
| Developer | Solo |
| Duration | 6 Months |
| Tech Domain | AI, NLP, Code-Mixed Speech Recognition, Web Development |
| Total Cost | ₹0 (100% free APIs and open-source tools) |

---

### The Big Idea (Plain Language)

When an Indian content creator records a YouTube video, they don't speak pure Hindi or pure English. They speak **Hinglish** — "Aaj ka video bohot exciting hai, toh let's get started yaar." A Bengali creator speaks **Benglish** — "Ami tomake bhalobasi, but you know, it's complicated." A Tamil creator speaks **Tanglish** — "Vera level experience da, seriously mind-blowing."

**No existing captioning tool understands this.** Google auto-captions tries to force it into either pure Hindi or pure English and fails badly at both. The result is captions that look nothing like what was actually said.

**DesiCaptions solves this.** It auto-detects the code-mixed language a speaker is using, and generates subtitles that look exactly like how they naturally talk — preserving the desi WhatsApp style, the natural code-switching. Indian content creators finally get subtitles that match their actual voice.

---

### Problem Statement

India has over 500 million YouTube and Instagram content creators and viewers who consume content in code-mixed Indian languages — not formal Hindi, not pure English, but the natural desi blend their community speaks every day.

Existing captioning tools fail them because:

1. Google/YouTube auto-captions force speech into pure English or pure Hindi — destroying the natural code-mixed style
2. OpenAI Whisper is not trained on Hinglish, Tanglish, or Benglish — it either misses regional words or aggressively translates them
3. No tool preserves code-mixed style in SRT format — there is no product today that outputs "aaj ka din bohot accha hai" instead of forcing it to one language
4. Indian creators cannot afford expensive enterprise captioning tools

---

### Proposed Solution

DesiCaptions is a free web application for Indian content creators that:

1. Accepts video/audio file upload or live microphone input
2. Auto-detects the code-mixed language being spoken (Hinglish, Benglish, Tanglish, Odia+English, Telugu+English)
3. Transcribes speech preserving the exact desi style — the natural mix the speaker uses
4. Gives users a choice of output format:
   - **Desi Style** — exactly how they spoke, romanized ("aaj ka din bohot accha tha, it was amazing yaar")
   - **Script + English** — regional script line 1, English line 2 (bilingual)
   - **English Only** — clean translation for international audiences
5. Exports in SRT format — ready for YouTube, Instagram Reels, VLC

---

### Supported Code-Mixed Language Pairs

| Language Mix | Example Subtitle | Community |
|---|---|---|
| Hinglish (Hindi+English) | "aaj ka video mein hum dekhenge how to make the perfect chai" | 600M+ Hindi speakers |
| Benglish (Bengali+English) | "ami tomake bhalobasi but you know, it's complicated yaar" | 100M+ Bengali speakers |
| Tanglish (Tamil+English) | "vera level experience da, seriously mind-blowing" | 80M+ Tamil speakers |
| Tenglish (Telugu+English) | "ee video chala useful ga untundi, trust me" | 96M+ Telugu speakers |
| Odia+English | "ae video ta bahut helpful achi, you should watch it" | 50M+ Odia speakers |

Auto-detection identifies which mix is being spoken without any user configuration needed.

---

### Output Format Options (User's Choice)

#### Option 1: Desi Style (Default)
Preserves natural code-mixed speech exactly as spoken. Romanized Indian words + English as-is.
```
1
00:00:01,000 --> 00:00:04,500
aaj ka din bohot accha tha,
it was amazing yaar
```

#### Option 2: Script + English (Bilingual)
Regional script on line 1, English translation on line 2.
```
1
00:00:01,000 --> 00:00:04,500
आज का दिन बहुत अच्छा था
Today was a really good day
```

#### Option 3: English Only
Clean English translation for international audiences.
```
1
00:00:01,000 --> 00:00:04,500
Today was a really great day,
it was truly amazing
```

---

### Why This is Novel

No existing academic paper or product specifically addresses SRT subtitle generation for code-mixed Indian speech while preserving the code-mixed style in the output. Every existing system tries to separate or translate the mix. DesiCaptions treats code-mixed output as the desired result, not a problem to fix.

This is the core research and engineering contribution of the project.

---

### Cost Breakdown — 100% Free

| Tool | Free Tier | Cost |
|---|---|---|
| Sarvam AI API | 1000+ calls/month free | ₹0 |
| Google Gemini 1.5 Flash | 1500 requests/day free | ₹0 |
| OpenAI Whisper | Runs locally, open source | ₹0 |
| FastAPI + Streamlit | Open source | ₹0 |
| Streamlit Community Cloud | Free hosting | ₹0 |
| **Total** | | **₹0** |

---

*Submitted for Final Year Major Project — B.Tech Computer Science & IT*
*DesiCaptions | Cost: ₹0 | Stack: Sarvam AI + Whisper + Gemini*
