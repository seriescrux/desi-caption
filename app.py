"""
DesiCaptions — Streamlit Frontend
app.py — Main web application

Run: streamlit run app.py
"""

import os
import sys
import time
import tempfile
import threading
import json
from pathlib import Path
from typing import Optional

import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# ---------------------------------------------------------------------------
# Page config — MUST be first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="DesiCaptions",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Custom CSS — Warm Indian aesthetic, clean and professional
# ---------------------------------------------------------------------------
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

  :root {
    --saffron:  #FF6B35;
    --deep:     #1A0F0A;
    --cream:    #FFF8F0;
    --card-bg:  #FFFFFF;
    --muted:    #7A6A60;
    --border:   #EDE0D4;
    --green:    #2D9E6B;
    --blue:     #2563EB;
  }

  /* Global */
  html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background: var(--cream) !important;
    color: var(--deep);
  }

  /* Hide default Streamlit padding/header chrome */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 2rem !important; max-width: 960px !important; }

  /* Headings */
  h1, h2, h3 { font-family: 'Syne', sans-serif !important; }

  /* Hero title */
  .hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 3.2rem;
    font-weight: 800;
    line-height: 1.1;
    letter-spacing: -1.5px;
    color: var(--deep);
    margin-bottom: 0.2rem;
  }
  .hero-accent { color: var(--saffron); }
  .hero-sub {
    font-size: 1.1rem;
    color: var(--muted);
    font-weight: 400;
    margin-bottom: 2rem;
  }

  /* Cards */
  .dc-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.5rem 1.8rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 2px 12px rgba(26,15,10,0.06);
  }
  .dc-card-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--saffron);
    margin-bottom: 0.8rem;
  }

  /* Mode selector pills */
  .mode-pill {
    display: inline-block;
    padding: 0.35rem 1rem;
    border-radius: 100px;
    font-size: 0.88rem;
    font-weight: 500;
    border: 1.5px solid var(--border);
    margin: 0.2rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  /* Caption preview box */
  .caption-box {
    background: var(--deep);
    border-radius: 12px;
    padding: 1.4rem 1.6rem;
    color: #fff;
    font-family: 'DM Sans', sans-serif;
    font-size: 1rem;
    line-height: 1.7;
    min-height: 120px;
    letter-spacing: 0.01em;
    white-space: pre-wrap;
    font-weight: 400;
  }
  .caption-box .srt-index { color: #FF6B35; font-size: 0.75rem; margin-bottom: 0.1rem; }
  .caption-box .srt-ts { color: #8a7a72; font-size: 0.78rem; margin-bottom: 0.25rem; }
  .caption-box .srt-text { color: #fff; font-size: 1rem; margin-bottom: 1rem; }

  /* Live caption display */
  .live-caption {
    background: var(--deep);
    border-radius: 12px;
    padding: 1.6rem 2rem;
    color: #fff;
    font-family: 'Syne', sans-serif;
    font-size: 1.5rem;
    font-weight: 600;
    min-height: 80px;
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
    border-left: 4px solid var(--saffron);
    margin: 1rem 0;
    letter-spacing: -0.5px;
  }

  /* Status badges */
  .badge-processing {
    display: inline-block;
    background: #FFF3E8;
    color: var(--saffron);
    border: 1px solid #FFD4B8;
    border-radius: 100px;
    padding: 0.2rem 0.8rem;
    font-size: 0.78rem;
    font-weight: 600;
  }
  .badge-done {
    display: inline-block;
    background: #E8F8EF;
    color: var(--green);
    border: 1px solid #B8EDD3;
    border-radius: 100px;
    padding: 0.2rem 0.8rem;
    font-size: 0.78rem;
    font-weight: 600;
  }

  /* Language detect badge */
  .lang-badge {
    display: inline-block;
    background: #EBF0FF;
    color: var(--blue);
    border-radius: 8px;
    padding: 0.25rem 0.75rem;
    font-size: 0.82rem;
    font-weight: 600;
    margin-left: 0.5rem;
  }

  /* Comparison table */
  .compare-table { width: 100%; border-collapse: collapse; }
  .compare-table th {
    text-align: left;
    font-family: 'Syne', sans-serif;
    font-size: 0.78rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--saffron);
    padding: 0.5rem 0.8rem;
    border-bottom: 2px solid var(--border);
  }
  .compare-table td {
    padding: 0.6rem 0.8rem;
    font-size: 0.9rem;
    border-bottom: 1px solid var(--border);
    vertical-align: top;
  }
  .compare-table tr:last-child td { border-bottom: none; }
  .strike { color: #C0A898; text-decoration: line-through; }
  .check { color: var(--green); font-weight: 600; }

  /* Streamlit button overrides */
  .stButton > button {
    background: var(--saffron) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    padding: 0.55rem 1.6rem !important;
    transition: all 0.2s !important;
    letter-spacing: 0.01em !important;
  }
  .stButton > button:hover {
    background: #E55A20 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(255,107,53,0.35) !important;
  }

  /* Secondary buttons */
  .btn-secondary > button {
    background: transparent !important;
    color: var(--deep) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 10px !important;
  }
  .btn-secondary > button:hover {
    border-color: var(--saffron) !important;
    color: var(--saffron) !important;
    transform: translateY(-1px) !important;
    box-shadow: none !important;
  }

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    background: transparent !important;
    border-bottom: 2px solid var(--border);
  }
  .stTabs [data-baseweb="tab"] {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    color: var(--muted) !important;
    background: transparent !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 0.5rem 1.2rem !important;
  }
  .stTabs [aria-selected="true"] {
    color: var(--saffron) !important;
    border-bottom: 2px solid var(--saffron) !important;
  }

  /* File uploader */
  [data-testid="stFileUploader"] {
    border: 2px dashed var(--border) !important;
    border-radius: 14px !important;
    background: #FFFBF7 !important;
    transition: border-color 0.2s;
  }
  [data-testid="stFileUploader"]:hover {
    border-color: var(--saffron) !important;
  }

  /* Select boxes & inputs */
  .stSelectbox > div > div {
    border-radius: 10px !important;
    border-color: var(--border) !important;
    font-family: 'DM Sans', sans-serif !important;
  }

  /* Progress bar */
  .stProgress > div > div > div > div {
    background: var(--saffron) !important;
  }

  /* Divider */
  hr { border-color: var(--border) !important; }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background: var(--card-bg) !important;
    border-right: 1px solid var(--border) !important;
  }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------
def init_session():
    defaults = {
        "srt_content": None,
        "srt_filename": None,
        "raw_transcript": None,
        "detected_language": None,
        "processing": False,
        "live_captions": [],
        "live_active": False,
        "output_mode": "desi",
        "language": "auto",
        "last_error": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

LANGUAGE_OPTIONS = {
    "🔍 Auto-detect": "auto",
    "🟠 Hinglish (Hindi + English)": "hinglish",
    "🟢 Benglish (Bengali + English)": "benglish",
    "🔵 Tanglish (Tamil + English)": "tanglish",
    "🟣 Tenglish (Telugu + English)": "tenglish",
    "🔴 Odia + English": "odiaenglish",
}

MODE_OPTIONS = {
    "🎯 Desi Style": "desi",
    "🔤 Script + English": "bilingual",
    "🌍 English Only": "english",
}

MODE_DESCRIPTIONS = {
    "desi": "WhatsApp-style romanized code-mix — 'aaj ka din bohot accha tha, it was amazing yaar'",
    "bilingual": "Native script on line 1, English translation on line 2",
    "english": "Clean English translation for international audiences",
}

LANG_DISPLAY = {
    "auto": "",
    "hinglish": "Hinglish",
    "benglish": "Benglish",
    "tanglish": "Tanglish",
    "tenglish": "Tenglish",
    "odiaenglish": "Odia+English",
}


def load_pipeline(output_mode: str, language: str):
    """Load pipeline with caching (whisper model stays in memory)."""
    from pipeline import DesiCaptionsPipeline, PipelineConfig

    config = PipelineConfig(
        sarvam_api_key=os.getenv("SARVAM_API_KEY", ""),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        whisper_model=os.getenv("WHISPER_MODEL", "medium"),
        output_mode=output_mode,
        language=language,
        prefer_model="sarvam" if os.getenv("SARVAM_API_KEY") else "whisper",
    )
    return DesiCaptionsPipeline(config)


def format_srt_for_display(srt_content: str, max_blocks: int = 8) -> str:
    """Format SRT content for pretty display in caption-box."""
    lines = srt_content.strip().split("\n")
    output = []
    count = 0
    block = []

    for line in lines:
        line = line.strip()
        if not line:
            if block:
                output.append("\n".join(block))
                count += 1
                block = []
            if count >= max_blocks:
                break
        else:
            block.append(line)

    if block and count < max_blocks:
        output.append("\n".join(block))

    return "\n\n".join(output)


# ---------------------------------------------------------------------------
# Hero header
# ---------------------------------------------------------------------------

st.markdown("""
<div class="hero-title">
  Desi<span class="hero-accent">Captions</span>
</div>
<div class="hero-sub">
  AI-powered subtitles for Hinglish · Tanglish · Benglish · Tenglish · Odia+English
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# API key status bar
# ---------------------------------------------------------------------------

sarvam_ok = bool(os.getenv("SARVAM_API_KEY"))
gemini_ok = bool(os.getenv("GEMINI_API_KEY"))

col_k1, col_k2, col_k3 = st.columns([1, 1, 3])
with col_k1:
    if sarvam_ok:
        st.markdown('<span class="badge-done">✓ Sarvam AI</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge-processing">⚠ No Sarvam Key</span>', unsafe_allow_html=True)
with col_k2:
    if gemini_ok:
        st.markdown('<span class="badge-done">✓ Gemini</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge-processing">⚠ No Gemini Key</span>', unsafe_allow_html=True)

if not sarvam_ok or not gemini_ok:
    with st.expander("⚙️ Set up API keys"):
        st.markdown("""
        Copy `.env.example` to `.env` and fill in your keys:
        ```
        SARVAM_API_KEY=...   # free at sarvam.ai
        GEMINI_API_KEY=...   # free at makersuite.google.com
        ```
        Without Sarvam → falls back to Whisper (local, still free).  
        Without Gemini → captions won't be post-processed (raw ASR output).
        """)

st.write("")

# ---------------------------------------------------------------------------
# Main tabs
# ---------------------------------------------------------------------------

tab_file, tab_live, tab_compare = st.tabs([
    "📁  File Upload",
    "🎙️  Live Mic",
    "⚡  How It Works",
])


# ============================================================
# TAB 1 — File Upload
# ============================================================
with tab_file:
    st.write("")

    left, right = st.columns([1.1, 0.9], gap="large")

    with left:
        # --- Step 1: Upload ---
        st.markdown('<div class="dc-card-title">Step 1 — Upload your video or audio</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "Drop file here",
            type=["mp4", "mov", "avi", "mkv", "mp3", "wav", "ogg", "webm", "m4a"],
            label_visibility="collapsed",
        )

        if uploaded:
            st.caption(f"📎 {uploaded.name} · {uploaded.size / 1024 / 1024:.1f} MB")

        st.write("")

        # --- Step 2: Language ---
        st.markdown('<div class="dc-card-title">Step 2 — Language</div>', unsafe_allow_html=True)
        lang_label = st.selectbox(
            "Language",
            list(LANGUAGE_OPTIONS.keys()),
            index=0,
            label_visibility="collapsed",
        )
        selected_language = LANGUAGE_OPTIONS[lang_label]
        st.caption("Auto-detect works for all supported mixes. Select manually for best accuracy.")

        st.write("")

        # --- Step 3: Output mode ---
        st.markdown('<div class="dc-card-title">Step 3 — Output style</div>', unsafe_allow_html=True)
        mode_label = st.selectbox(
            "Output mode",
            list(MODE_OPTIONS.keys()),
            index=0,
            label_visibility="collapsed",
        )
        selected_mode = MODE_OPTIONS[mode_label]
        st.caption(MODE_DESCRIPTIONS[selected_mode])

        st.write("")

        # --- Generate button ---
        go_btn = st.button("✨ Generate Subtitles", use_container_width=True)

    with right:
        st.markdown('<div class="dc-card-title">Preview & Download</div>', unsafe_allow_html=True)

        # Show result or placeholder
        if st.session_state.processing:
            st.markdown('<div class="caption-box"><span style="color:#FF6B35">⟳ Processing...</span></div>', unsafe_allow_html=True)

        elif st.session_state.srt_content:
            # Language detected badge
            if st.session_state.detected_language and st.session_state.detected_language != "auto":
                lang_disp = LANG_DISPLAY.get(st.session_state.detected_language, st.session_state.detected_language)
                st.markdown(f'<span class="badge-done">✓ Done</span> <span class="lang-badge">🌐 {lang_disp} detected</span>', unsafe_allow_html=True)
                st.write("")

            # SRT preview
            preview = format_srt_for_display(st.session_state.srt_content)
            # Render as styled blocks
            blocks_html = ""
            for block in preview.split("\n\n"):
                lines = block.strip().split("\n")
                if len(lines) >= 3:
                    blocks_html += f'<div style="margin-bottom:1.1rem"><div class="srt-index">{lines[0]}</div><div class="srt-ts">{lines[1]}</div><div class="srt-text">{"<br>".join(lines[2:])}</div></div>'
            st.markdown(f'<div class="caption-box">{blocks_html}</div>', unsafe_allow_html=True)

            # Download button
            st.write("")
            st.download_button(
                label="⬇ Download .srt",
                data=st.session_state.srt_content,
                file_name=st.session_state.srt_filename or "desicaptions.srt",
                mime="text/plain",
                use_container_width=True,
            )

            # Stats
            seg_count = st.session_state.srt_content.count("\n\n")
            st.caption(f"~{seg_count} subtitle segments · UTF-8 encoded · SRT format")

        elif st.session_state.last_error:
            st.markdown(f'<div class="caption-box"><span style="color:#FF6B35">❌ Error:</span><br><span style="color:#ccc;font-size:0.9rem">{st.session_state.last_error}</span></div>', unsafe_allow_html=True)

        else:
            st.markdown("""
<div class="caption-box">
  <span style="color:#4a3a30">Upload a video and click<br>
  <span style="color:#FF6B35;font-weight:600">Generate Subtitles</span><br>
  to see your captions here.</span>
</div>
""", unsafe_allow_html=True)

    # --- Processing logic ---
    if go_btn:
        if not uploaded:
            st.warning("Please upload a file first.")
        else:
            st.session_state.processing = True
            st.session_state.srt_content = None
            st.session_state.last_error = None
            st.rerun()

    if st.session_state.processing and uploaded:
        progress_bar = st.progress(0.0)
        status_text = st.empty()

        try:
            # Save uploaded file to temp location
            suffix = Path(uploaded.name).suffix
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(uploaded.read())
                tmp_input = tmp.name

            # Output SRT path
            tmp_srt = tmp_input.replace(suffix, f"_{selected_mode}.srt")

            def progress_cb(pct: float, msg: str):
                progress_bar.progress(pct)
                status_text.markdown(f'<span class="badge-processing">⟳ {msg}</span>', unsafe_allow_html=True)

            pipeline = load_pipeline(selected_mode, selected_language)
            srt_path = pipeline.process_file(
                input_path=tmp_input,
                output_srt_path=tmp_srt,
                progress_callback=progress_cb,
            )

            srt_content = Path(srt_path).read_text(encoding="utf-8")
            st.session_state.srt_content = srt_content
            st.session_state.srt_filename = Path(uploaded.name).stem + f"_{selected_mode}.srt"
            st.session_state.detected_language = selected_language

        except Exception as e:
            st.session_state.last_error = str(e)
            import traceback
            print(traceback.format_exc())

        finally:
            st.session_state.processing = False
            try:
                os.unlink(tmp_input)
            except Exception:
                pass

        progress_bar.progress(1.0)
        status_text.empty()
        st.rerun()


# ============================================================
# TAB 2 — Live Mic Captioning
# ============================================================
with tab_live:
    st.write("")
    st.markdown('<div class="dc-card-title">Live microphone captioning via WebSocket</div>', unsafe_allow_html=True)

    col_l1, col_l2 = st.columns([1, 1], gap="large")

    with col_l1:
        live_lang_label = st.selectbox(
            "Language",
            list(LANGUAGE_OPTIONS.keys()),
            key="live_lang",
        )
        live_mode_label = st.selectbox(
            "Output Style",
            list(MODE_OPTIONS.keys()),
            key="live_mode",
        )
        live_lang = LANGUAGE_OPTIONS[live_lang_label]
        live_mode = MODE_OPTIONS[live_mode_label]

        ws_url = st.text_input(
            "WebSocket server URL",
            value="ws://localhost:8000/ws/live",
            help="Start the FastAPI server first: uvicorn websocket_server:app --port 8000",
        )

        st.write("")
        st.info("""
**To use live captioning:**
1. Open a terminal in the project folder
2. Run: `uvicorn websocket_server:app --port 8000`
3. Come back here and click Start
        """)

    with col_l2:
        # Live caption display
        if st.session_state.live_captions:
            last_caption = st.session_state.live_captions[-1]
            st.markdown(f'<div class="live-caption">{last_caption}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="live-caption" style="color:#4a3a30">Captions appear here in real-time...</div>', unsafe_allow_html=True)

        if st.session_state.live_captions:
            st.markdown("**Recent captions:**")
            for cap in reversed(st.session_state.live_captions[-5:]):
                st.markdown(f"> {cap}")

    # WebSocket JS integration
    ws_config = json.dumps({
        "language": live_lang,
        "mode": live_mode,
    })

    st.components.v1.html(f"""
<style>
  body {{ font-family: 'DM Sans', sans-serif; background: transparent; margin: 0; }}
  .ctrl-bar {{ display: flex; gap: 10px; padding: 1rem 0 0; }}
  .btn {{
    padding: 0.5rem 1.4rem; border-radius: 10px; border: none;
    font-weight: 600; font-size: 0.9rem; cursor: pointer; transition: all 0.2s;
  }}
  .btn-start {{ background: #FF6B35; color: white; }}
  .btn-start:hover {{ background: #E55A20; }}
  .btn-stop {{ background: #1A0F0A; color: white; }}
  .btn-stop:hover {{ background: #333; }}
  .btn-dl {{ background: transparent; color: #1A0F0A; border: 1.5px solid #EDE0D4 !important; border: none; }}
  .btn-dl:hover {{ border-color: #FF6B35 !important; color: #FF6B35; }}
  #status {{ font-size: 0.82rem; color: #7A6A60; padding: 0.5rem 0; }}
  #mic-level {{
    height: 6px; border-radius: 3px; background: #EDE0D4;
    margin: 0.5rem 0; overflow: hidden;
  }}
  #mic-bar {{ height: 100%; width: 0%; background: #FF6B35; transition: width 0.1s; border-radius: 3px; }}
</style>

<div class="ctrl-bar">
  <button class="btn btn-start" onclick="startLive()">🎙 Start</button>
  <button class="btn btn-stop" onclick="stopLive()">⬜ Stop</button>
  <button class="btn btn-dl" onclick="downloadSession()">⬇ Export SRT</button>
</div>
<div id="mic-level"><div id="mic-bar"></div></div>
<div id="status">Ready — click Start to begin</div>

<script>
let ws = null;
let mediaRecorder = null;
let stream = null;
let sessionCaptions = [];
let sessionSrt = [];
let segIndex = 1;
let currentMs = 0;
const CHUNK_MS = 3000;
const WS_URL = "{ws_url}";
const CONFIG = {ws_config};

function log(msg) {{
  document.getElementById('status').textContent = msg;
}}

async function startLive() {{
  if (ws && ws.readyState === WebSocket.OPEN) return;

  try {{
    stream = await navigator.mediaDevices.getUserMedia({{ audio: true, video: false }});
    log('Microphone connected — connecting to server...');

    ws = new WebSocket(WS_URL);

    ws.onopen = () => {{
      ws.send(JSON.stringify(CONFIG));
      log('Connected — speak now...');
      startRecording();
      startMicLevel();
    }};

    ws.onmessage = (e) => {{
      const data = JSON.parse(e.data);
      if (data.type === 'caption' && data.text) {{
        sessionCaptions.push(data.text);
        addToSrt(data.text);
        // Update display via streamlit (parent message)
        window.parent.postMessage({{
          type: 'streamlit:setComponentValue',
          value: data.text,
        }}, '*');
      }} else if (data.type === 'ready') {{
        log('Server ready — speak now!');
      }}
    }};

    ws.onclose = () => log('Connection closed');
    ws.onerror = () => log('Connection error — is the server running?');

  }} catch(err) {{
    log('Mic error: ' + err.message);
  }}
}}

function startRecording() {{
  const mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/ogg';
  mediaRecorder = new MediaRecorder(stream, {{ mimeType }});

  mediaRecorder.ondataavailable = (e) => {{
    if (e.data.size > 0 && ws && ws.readyState === WebSocket.OPEN) {{
      ws.send(e.data);
    }}
  }};

  mediaRecorder.start(CHUNK_MS);
}}

function startMicLevel() {{
  const ctx = new AudioContext();
  const analyser = ctx.createAnalyser();
  const source = ctx.createMediaStreamSource(stream);
  source.connect(analyser);
  analyser.fftSize = 256;
  const buf = new Uint8Array(analyser.frequencyBinCount);

  function tick() {{
    if (!stream.active) return;
    analyser.getByteFrequencyData(buf);
    const avg = buf.reduce((a,b)=>a+b,0)/buf.length;
    document.getElementById('mic-bar').style.width = Math.min(100, avg * 2) + '%';
    requestAnimationFrame(tick);
  }}
  tick();
}}

function stopLive() {{
  if (mediaRecorder) mediaRecorder.stop();
  if (stream) stream.getTracks().forEach(t => t.stop());
  if (ws) ws.close();
  document.getElementById('mic-bar').style.width = '0%';
  log('Stopped — ' + sessionCaptions.length + ' captions captured');
}}

function addToSrt(text) {{
  const start = msToTs(currentMs);
  const end = msToTs(currentMs + CHUNK_MS);
  sessionSrt.push(segIndex + '\\n' + start + ' --> ' + end + '\\n' + text);
  segIndex++;
  currentMs += CHUNK_MS;
}}

function msToTs(ms) {{
  const h = Math.floor(ms/3600000).toString().padStart(2,'0');
  const m = Math.floor((ms%3600000)/60000).toString().padStart(2,'0');
  const s = Math.floor((ms%60000)/1000).toString().padStart(2,'0');
  const mm = (ms%1000).toString().padStart(3,'0');
  return h+':'+m+':'+s+','+mm;
}}

function downloadSession() {{
  if (!sessionSrt.length) {{ log('No captions to export'); return; }}
  const content = sessionSrt.join('\\n\\n');
  const blob = new Blob([content], {{type: 'text/plain;charset=utf-8'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'desicaptions_live.srt';
  a.click();
  log('Downloaded ' + sessionSrt.length + ' segments');
}}
</script>
""", height=120)


# ============================================================
# TAB 3 — How It Works
# ============================================================
with tab_compare:
    st.write("")

    st.markdown('<div class="dc-card-title">The Problem with Existing Tools</div>', unsafe_allow_html=True)
    st.markdown("""
<table class="compare-table">
  <tr>
    <th>What you said</th>
    <th>Google auto-captions ❌</th>
    <th>YouTube ❌</th>
    <th>DesiCaptions ✅</th>
  </tr>
  <tr>
    <td>"aaj ka video mein hum dekhenge how to make chai, let's get started yaar"</td>
    <td class="strike">Today's video we will see how to make tea let's get started</td>
    <td class="strike">आज का वीडियो में हम देखेंगे हाउ टू मेक चाय</td>
    <td class="check">aaj ka video mein hum dekhenge how to make chai,<br>let's get started yaar ✓</td>
  </tr>
  <tr>
    <td>"vera level experience da, seriously mind-blowing"</td>
    <td class="strike">vera level experience the seriously mind-blowing</td>
    <td class="strike">வேற லெவல் எக்ஸ்பீரியன்ஸ் the</td>
    <td class="check">vera level experience da,<br>seriously mind-blowing ✓</td>
  </tr>
</table>
""", unsafe_allow_html=True)

    st.write("")
    st.markdown('<div class="dc-card-title">How DesiCaptions Works</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    steps = [
        ("🎵", "Audio In", "Upload video or use live mic. FFmpeg extracts 16kHz mono audio, chunks into 3s segments."),
        ("🎯", "Detect Language", "Sarvam AI + Whisper both analyze first chunk. Code-mix ratio determines routing."),
        ("🤖", "Transcribe", "Sarvam Saaras (primary) handles Indic words. Whisper handles English. Combined output."),
        ("✨", "Gemini Polish", "LLM post-processor adds punctuation, formats into SRT blocks in your chosen style."),
    ]
    for col, (icon, title, desc) in zip([c1, c2, c3, c4], steps):
        with col:
            st.markdown(f"""
<div style="text-align:center;padding:1.2rem 0.8rem;background:white;border-radius:14px;border:1px solid #EDE0D4;height:180px;">
  <div style="font-size:2rem;margin-bottom:0.5rem">{icon}</div>
  <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:0.9rem;margin-bottom:0.5rem">{title}</div>
  <div style="font-size:0.78rem;color:#7A6A60;line-height:1.5">{desc}</div>
</div>
""", unsafe_allow_html=True)

    st.write("")
    st.markdown('<div class="dc-card-title">Three Output Modes</div>', unsafe_allow_html=True)

    mode_ex = {
        "🎯 Desi Style (Default)": (
            "Romanized code-mixed — exactly how you speak",
            "aaj ka video mein hum dekhenge\nhow to make the perfect chai at home"
        ),
        "🔤 Script + English": (
            "Native script on line 1, English translation on line 2",
            "आज के वीडियो में हम देखेंगे\nhow to make the perfect chai"
        ),
        "🌍 English Only": (
            "Clean English for international audiences",
            "In today's video, we'll see\nhow to make the perfect chai at home"
        ),
    }
    mc1, mc2, mc3 = st.columns(3)
    for col, (mode_name, (mode_desc, example)) in zip([mc1, mc2, mc3], mode_ex.items()):
        with col:
            st.markdown(f"""
<div style="background:white;border-radius:14px;border:1px solid #EDE0D4;padding:1.2rem;height:210px;">
  <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:0.88rem;margin-bottom:0.3rem">{mode_name}</div>
  <div style="font-size:0.78rem;color:#7A6A60;margin-bottom:0.8rem">{mode_desc}</div>
  <div style="background:#1A0F0A;color:#fff;border-radius:8px;padding:0.7rem 0.9rem;font-size:0.82rem;line-height:1.6;font-family:monospace">{example}</div>
</div>
""", unsafe_allow_html=True)

    st.write("")
    st.markdown('<div class="dc-card-title">Supported Language Mixes</div>', unsafe_allow_html=True)

    lang_info = [
        ("🟠", "Hinglish", "Hindi + English", "600M+ speakers"),
        ("🟢", "Benglish", "Bengali + English", "100M+ speakers"),
        ("🔵", "Tanglish", "Tamil + English", "80M+ speakers"),
        ("🟣", "Tenglish", "Telugu + English", "96M+ speakers"),
        ("🔴", "Odia+Eng", "Odia + English", "50M+ speakers"),
    ]
    cols = st.columns(5)
    for col, (emoji, name, mix, speakers) in zip(cols, lang_info):
        with col:
            st.markdown(f"""
<div style="text-align:center;padding:1rem 0.5rem;background:white;border-radius:12px;border:1px solid #EDE0D4;">
  <div style="font-size:1.5rem">{emoji}</div>
  <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:0.88rem">{name}</div>
  <div style="font-size:0.75rem;color:#7A6A60">{mix}</div>
  <div style="font-size:0.7rem;color:#FF6B35;font-weight:600">{speakers}</div>
</div>
""", unsafe_allow_html=True)

    st.write("")
    st.markdown('<div class="dc-card-title">100% Free Stack</div>', unsafe_allow_html=True)

    st.markdown("""
<table class="compare-table">
  <tr><th>Tool</th><th>Purpose</th><th>Cost</th></tr>
  <tr><td>Sarvam AI Saaras</td><td>Indian language ASR (primary)</td><td style="color:#2D9E6B;font-weight:600">Free tier</td></tr>
  <tr><td>OpenAI Whisper</td><td>English ASR + fallback (local)</td><td style="color:#2D9E6B;font-weight:600">Free (local)</td></tr>
  <tr><td>Google Gemini 1.5 Flash</td><td>Caption post-processing</td><td style="color:#2D9E6B;font-weight:600">Free tier</td></tr>
  <tr><td>FastAPI + Streamlit</td><td>Backend + UI + hosting</td><td style="color:#2D9E6B;font-weight:600">Free</td></tr>
  <tr><td><strong>Total</strong></td><td></td><td style="color:#FF6B35;font-weight:700;font-size:1rem">₹0</td></tr>
</table>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.write("")
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center;color:#7A6A60;font-size:0.82rem;padding:0.5rem 0 1rem">
  DesiCaptions · Final Year Major Project · B.Tech CSE &amp; IT · KIIT Deemed to be University<br>
  <span style="color:#FF6B35">₹0 total cost</span> · Sarvam AI + Whisper + Gemini · 500M+ Indian creators
</div>
""", unsafe_allow_html=True)
