# Teacher Q&A Preparation Guide

## DesiCaptions — How to Explain Your Project

---

## 2-Minute Pitch (Memorize This)

> "Sir/Ma'am, my project is called DesiCaptions. It's an AI tool for Indian content creators — people who make YouTube, Instagram Reels, or podcast content in Indian languages.
>
> The core problem is: Indian creators speak in code-mixed languages — Hinglish, Tanglish, Benglish. Not pure Hindi, not pure English. When they try to generate subtitles using Google auto-captions, it either tries to make it fully English or fully Hindi — and the result looks nothing like what they actually said.
>
> My tool auto-detects which language mix the creator is speaking, and generates subtitles in three styles — first, desi WhatsApp style: 'aaj ka din bohot accha tha, it was amazing yaar.' Second, bilingual: native script on line one, English translation on line two. Third, full English translation for international audiences.
>
> The technology uses Sarvam AI — an Indian startup's ASR model specifically built for Indian languages — combined with OpenAI Whisper locally, and Google Gemini for post-processing the captions into desi style. Everything is completely free — Sarvam has a free API tier, Whisper runs locally, Gemini has a free tier, and I host it on Streamlit Cloud for free.
>
> The research contribution is a benchmarking study comparing Sarvam AI versus Whisper on code-mixed Indian audio using the Kathbath dataset from AI4Bharat at IIT Madras."

---

## Likely Teacher Questions — With Your Exact Answers

---

### Q1: "What is code-mixed speech? Give me an example."

> "Code-mixed speech is when a speaker naturally switches between two languages within the same sentence — not translating, just mixing. For example, a Hindi speaker might say: 'Aaj ka video mein hum dekhenge how to make the perfect chai at home, toh let's get started yaar.' That sentence has Hindi words, English words, and the grammar is somewhere in between. Linguists call this code-switching. In India it's so common that communities have given it names — Hinglish for Hindi-English, Tanglish for Tamil-English, Benglish for Bengali-English. It's the primary way hundreds of millions of Indians communicate every day, especially online and in informal settings."

---

### Q2: "Why is existing captioning bad for Indian languages?"

> "Three reasons. First, models like Google Speech API and Whisper are trained mostly on English and formal monolingual audio. They haven't seen enough real Hinglish or Tanglish speech. Second, even when they recognize the words, they try to normalize the output — they push it toward either full English or full Hindi, destroying the natural mix. Third, romanization — when an Indian person writes Hindi in English letters, they write 'bohot' not 'bahut', 'accha' not 'achha'. Existing tools don't understand WhatsApp-style romanization. So the output captions look machine-generated and unnatural to an Indian audience."

---

### Q3: "What is Sarvam AI? Is it reliable?"

> "Sarvam AI is an Indian AI startup founded in 2023, based in Bangalore. They've built a suite of AI models specifically for Indian languages, backed by significant funding and research partnerships. Their speech recognition model, called Saaras, is trained on large-scale Indic language data across 10+ Indian languages. Published benchmarks show it achieves around 8-12% Word Error Rate on standard Indian language test sets, compared to 25-30% or higher for generic models like Google Speech API. They have a free developer tier which I'm using for this project — it doesn't require a credit card and gives enough API calls for development and a demo. In a production system, you'd pay for higher usage, but for a student project it's completely free."

---

### Q4: "What makes this different from just using Google Translate?"

> "Google Translate is a translation tool — it converts from one language to another. DesiCaptions is not translating — in Mode 1, the desi style mode, I'm specifically preserving the code-mixed output exactly as it was spoken. 'aaj ka din bohot accha tha' stays as 'aaj ka din bohot accha tha' — I don't translate those words to English. The post-processing adds punctuation and formats it into subtitle blocks, but it preserves the language mix. Only in Mode 3, English Only, do I actually translate. And even that translation is done by Gemini with a prompt that preserves the informal tone — not a literal dictionary translation like Google Translate produces."

---

### Q5: "What is your original contribution? You're using existing APIs."

> "Three original contributions. First, the code-mix auto-detection pipeline — I built a novel approach that runs audio through both Sarvam AI and Whisper simultaneously, analyzes the ratio of Indian vs English words, and classifies the specific language mix. This doesn't exist as a ready-made component — I designed and built it. Second, the desi-style romanization system — I engineered specific Gemini prompts that produce WhatsApp-style romanization rather than academic transliteration. This required multiple iterations of prompt engineering and testing against real Indian social media text norms. Third, the benchmarking study comparing Sarvam AI versus Whisper specifically on code-mixed Indian speech using the Kathbath dataset — this specific comparison hasn't been published, so the findings are a genuine research contribution."

---

### Q6: "Why three output modes? Why not just one?"

> "Because different creators have different audiences. A creator making content for young urban Indians wants Mode 1 — desi style — because their viewers read Hinglish naturally and a formal script would feel off-brand. A creator who wants to grow their audience and reach both Hindi speakers and English speakers benefits from Mode 2 — script plus English — because both communities can read it. A creator going for international reach, like an Indian travel vlogger wanting global viewers, needs Mode 3 — clean English. One tool serving all three needs means DesiCaptions is useful to the entire Indian content creator ecosystem, not just one segment."

---

### Q7: "Is this free? How?"

> "Yes, completely free for this project. Sarvam AI has a free developer tier — I signed up, got an API key with no credit card required, and have enough calls per month for development and demo purposes. OpenAI Whisper is open-source and runs locally on my laptop — it's a one-time model download and then zero cost forever. Google Gemini 1.5 Flash has a free tier of 1500 requests per day, which is more than enough. FastAPI and Streamlit are open-source Python libraries. And Streamlit Community Cloud offers free hosting for public apps — so the deployed application is free too. The total cost for this entire project is zero rupees."

---

### Q8: "What datasets did you use?"

> "I used the Kathbath dataset from AI4Bharat, which is the Indian language AI research group at IIT Madras. Kathbath contains 1700 hours of speech across 12 Indian languages with verified ground truth transcriptions. I specifically used the code-mixed subset — clips where speakers naturally mix English with their regional language. This is a published, academically recognized dataset, which means my benchmarking results are reproducible and comparable to other published research. AI4Bharat is funded by Google and the Indian government, so citing their work adds institutional credibility to my project."

---

### Q9: "What is WER? What numbers did you get?"

> "WER stands for Word Error Rate — the standard metric for measuring accuracy in speech recognition. It counts three types of mistakes: substitutions, where a wrong word is predicted; deletions, where a word is missed; and insertions, where an extra word is added. You divide the total errors by the total number of words in the correct transcript and multiply by 100 to get a percentage. Lower is better — a WER of 0% means perfect transcription. For my benchmarking, I ran 100 code-mixed audio clips — 20 each for Hinglish, Benglish, Tanglish, Tenglish, and Odia+English — through both Sarvam AI and Whisper, and compared their WER against the ground truth transcripts. [Fill in your actual numbers here once benchmarking is complete]."

---

### Q10: "Who would actually use this?"

> "The primary users are Indian content creators — people making YouTube videos, Instagram Reels, podcasts, and short-form content in code-mixed Indian languages. There are estimated to be over 500 million people consuming Indian language content online. A Hinglish content creator today has to either: pay for expensive human transcription, use bad auto-captions and manually fix them, or publish without subtitles at all. DesiCaptions gives them a free, accurate, authentically Indian-style alternative. Secondary users include educators recording lectures in code-mixed classroom English, journalists covering regional stories, and accessibility users — deaf and hard-of-hearing Indians who understand code-mixed speech and want captions that reflect the actual language being spoken."

---

## Key Terms to Know Cold

| Term | One-Line Definition |
|---|---|
| Code-mixed speech | Naturally mixing two languages in one sentence (Hinglish, Tanglish etc) |
| Hinglish | Code-mixed Hindi + English — the dominant style of urban Indian communication |
| Romanization | Writing Indian language words using English letters ("bohot" for बहुत) |
| WER | Word Error Rate — % of words incorrectly transcribed |
| SRT | SubRip Text — standard subtitle file format used by YouTube, VLC |
| Sarvam AI | Indian startup's ASR model built for Indic languages, free tier available |
| Whisper | OpenAI's open-source ASR — runs locally, zero cost |
| Gemini 1.5 Flash | Google's fast LLM — free tier, used for post-processing captions |
| ASR | Automatic Speech Recognition — converts audio to text |
| Kathbath | 1700-hour Indian language dataset from AI4Bharat, IIT Madras |
| AI4Bharat | Indian language AI research group at IIT Madras |
| Code-switching | Linguistic term for switching between languages mid-sentence |
| Post-processing | Cleaning/formatting raw ASR text into readable captions |
| WebSocket | Protocol for real-time two-way browser-server communication |
| VAD | Voice Activity Detection — identifies if audio has speech or silence |

---

*Document: Teacher Q&A Preparation v2.0 — DesiCaptions*
