import streamlit as st
import openai
import asyncio
import io
import edge_tts
from audio_recorder_streamlit import audio_recorder

SYSTEM_PROMPT = """Ti je Elira, një vajzë shqiptare nga Tirana. Flet si një shqiptare e vërtetë — natyrisht, lirshëm, jo si tekst i përkthyer nga anglishtja.

RREGULLA TË RËNDËSISHME:
- Fol GJITHMONË shqip, si në bisedë të përditshme me miqtë
- Përdor shprehje natyrale shqiptare: "ore", "pra", "ta dish", "s'ka gjë", "hajde", "meqë ra fjala"
- Shkurto fjalët si në të folur të vërtetë: "s'kam" jo "nuk kam", "s'di" jo "nuk di", "t'them" jo "të them", "m'fal" jo "më fal"
- Mos përdor gjuhë formale, zyrtare ose të ngurtë — fol sikur je me shokët
- Përgjigju SHKURT — 1 deri 2 fjali, si bisedë me zë, jo esè
- ASNJËHERË mos përkthe nga anglishtja — mendo dhe formuloje direkt në shqip
- Nëse dikush flet anglisht ose gjuhë tjetër, thuaji bukur: "Unë flas vetëm shqip ore!"
- Përdor humor dhe ngrohtësi — ji simpatike, jo robotike"""


def get_openai_client() -> openai.OpenAI:
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    if not api_key:
        st.error("OpenAI API key not found. Add OPENAI_API_KEY to .streamlit/secrets.toml")
        st.stop()
    return openai.OpenAI(api_key=api_key)


def transcribe_audio(client: openai.OpenAI, audio_bytes: bytes) -> str:
    if len(audio_bytes) < 1000:
        return ""
    audio_file = ("recording.wav", io.BytesIO(audio_bytes), "audio/wav")
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
    )
    return transcription.text


def generate_response(client: openai.OpenAI, user_message: str, history: list[dict]) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in history[-10:]:
        messages.append(h)
    messages.append({"role": "user", "content": user_message})

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=100,
        temperature=0.8,
    )
    return completion.choices[0].message.content or "Më falni, nuk munda të përgjigjem."


ALBANIAN_VOICES = {
    "female": "sq-AL-AnilaNeural",
    "male": "sq-AL-IlirNeural",
}


def synthesize_speech(text: str, gender: str = "female") -> bytes:
    voice = ALBANIAN_VOICES.get(gender, ALBANIAN_VOICES["female"])

    async def _generate():
        comm = edge_tts.Communicate(text, voice, rate="+5%")
        chunks = []
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])
        return b"".join(chunks)

    return asyncio.run(_generate())


# --- Page Config ---
st.set_page_config(
    page_title="Asistenti Shqiptar",
    page_icon="🇦🇱",
    layout="wide",
)

# --- Custom CSS ---
st.markdown("""
<style>
    .stApp { background-color: #09090b; }
    [data-testid="stHeader"] { background-color: #09090b; }
    [data-testid="stSidebar"] {
        background-color: #0f0f12;
        border-right: 1px solid #1e1e24;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        padding-top: 0.5rem;
    }

    .main-header {
        text-align: center;
        padding: 1rem 0 0.6rem;
    }
    .main-header h1 {
        color: #fafafa;
        font-size: 1.4rem;
        font-weight: 700;
        margin: 0;
    }
    .main-header p {
        color: #71717a;
        font-size: 0.72rem;
        margin: 0;
    }
    .al-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 2rem;
        height: 2rem;
        border-radius: 0.5rem;
        background: linear-gradient(135deg, #dc2626, #991b1b);
        color: white;
        font-weight: 700;
        font-size: 0.8rem;
        margin-bottom: 0.3rem;
    }

    .chat-user {
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        color: white;
        padding: 0.6rem 0.9rem;
        border-radius: 1rem 1rem 0.25rem 1rem;
        margin: 0.3rem 0;
        font-size: 0.85rem;
        max-width: 85%;
        margin-left: auto;
        text-align: right;
        line-height: 1.4;
    }
    .chat-assistant {
        background: linear-gradient(135deg, #27272a, #303035);
        color: #f4f4f5;
        padding: 0.6rem 0.9rem;
        border-radius: 1rem 1rem 1rem 0.25rem;
        margin: 0.3rem 0;
        font-size: 0.85rem;
        max-width: 85%;
        line-height: 1.4;
    }
    .chat-label {
        font-size: 0.55rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        opacity: 0.5;
        margin-bottom: 0.15rem;
    }

    /* ---- Sidebar mic styles ---- */
    .sidebar-mic-wrap {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 1rem 0;
    }
    .mic-orb {
        position: relative;
        width: 100px;
        height: 100px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 0.8rem;
    }
    .mic-orb::before {
        content: '';
        position: absolute;
        width: 100%;
        height: 100%;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(239,68,68,0.12) 0%, transparent 70%);
        animation: orb-breathe 2.5s ease-in-out infinite;
    }
    .mic-orb::after {
        content: '';
        position: absolute;
        width: 80%;
        height: 80%;
        border-radius: 50%;
        border: 2px solid rgba(239,68,68,0.2);
        animation: orb-ring 3s ease-in-out infinite;
    }
    @keyframes orb-breathe {
        0%, 100% { transform: scale(1); opacity: 0.6; }
        50% { transform: scale(1.15); opacity: 0.3; }
    }
    @keyframes orb-ring {
        0%, 100% { transform: scale(0.9); opacity: 0.4; }
        50% { transform: scale(1.1); opacity: 0.1; }
    }

    .mic-status {
        text-align: center;
        color: #a1a1aa;
        font-size: 0.7rem;
        letter-spacing: 0.04em;
        margin-bottom: 0.3rem;
    }
    .mic-hint {
        text-align: center;
        color: #52525b;
        font-size: 0.58rem;
    }

    [data-testid="stSidebar"] div[data-testid="stAudioRecorder"] {
        display: flex !important;
        justify-content: center !important;
    }

    audio { border-radius: 8px; }

    .empty-chat {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 40vh;
        color: #3f3f46;
        text-align: center;
        font-size: 0.85rem;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# --- Session state ---
if "history" not in st.session_state:
    st.session_state.history = []
if "entries" not in st.session_state:
    st.session_state.entries = []
if "pending_audio" not in st.session_state:
    st.session_state.pending_audio = None

# ===========================
# SIDEBAR — mic always here
# ===========================
with st.sidebar:
    st.markdown("""
    <div class="sidebar-mic-wrap">
        <div class="mic-orb"></div>
    </div>
    """, unsafe_allow_html=True)

    audio_bytes = audio_recorder(
        text="",
        recording_color="#ef4444",
        neutral_color="#71717a",
        icon_size="3x",
        pause_threshold=2.0,
        sample_rate=44100,
        key="main_recorder",
    )

    st.markdown("""
    <div class="mic-status">Shtyp dhe fol</div>
    <div class="mic-hint">Press & speak</div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    if st.button("🗑️  Pastro / Clear", use_container_width=True):
        st.session_state.history = []
        st.session_state.entries = []
        st.session_state.pending_audio = None
        if "last_audio" in st.session_state:
            del st.session_state.last_audio
        st.rerun()

    st.markdown(
        '<br><small style="color:#3f3f46">Powered by OpenAI Whisper<br>GPT-4o-mini · Albanian Neural TTS</small>',
        unsafe_allow_html=True,
    )

# ===========================
# MAIN AREA — header + chat
# ===========================
st.markdown("""
<div class="main-header">
    <div class="al-badge">AL</div>
    <h1>Asistenti Shqiptar</h1>
    <p>Albanian Voice Assistant</p>
</div>
""", unsafe_allow_html=True)

# --- Play pending audio ---
if st.session_state.pending_audio is not None:
    audio_data = st.session_state.pending_audio
    st.session_state.pending_audio = None
    st.audio(audio_data, format="audio/mp3", autoplay=True)

# --- Chat history ---
if not st.session_state.entries:
    st.markdown("""
    <div class="empty-chat">
        <div>
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🎙️</div>
            Shtyp butonin në të majtë dhe fillo të flasësh shqip<br>
            <span style="color:#2a2a2e; font-size: 0.75rem;">Press the mic on the left and start speaking Albanian</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    for entry in st.session_state.entries:
        if entry["role"] == "user":
            st.markdown(
                f'<div class="chat-user"><div class="chat-label">Ti</div>{entry["text"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="chat-assistant"><div class="chat-label">Asistenti</div>{entry["text"]}</div>',
                unsafe_allow_html=True,
            )

# --- Process audio when recorded ---
if audio_bytes:
    if "last_audio" not in st.session_state or st.session_state.last_audio != audio_bytes:
        st.session_state.last_audio = audio_bytes
        client = get_openai_client()

        try:
            with st.spinner("🎧 Po dëgjoj..."):
                transcript = transcribe_audio(client, audio_bytes)
        except Exception as e:
            st.error(f"Transcription failed: {e}")
            transcript = ""

        if not transcript.strip():
            st.warning("Nuk munda ta kuptoj audion. Provoni përsëri.")
        else:
            st.session_state.entries.append({"role": "user", "text": transcript})
            st.session_state.history.append({"role": "user", "content": transcript})

            with st.spinner("🧠 Po mendoj..."):
                response_text = generate_response(
                    client, transcript, st.session_state.history[:-1]
                )

            st.session_state.entries.append({"role": "assistant", "text": response_text})
            st.session_state.history.append({"role": "assistant", "content": response_text})

            with st.spinner("🔊 Po flas..."):
                audio_response = synthesize_speech(response_text)

            st.session_state.pending_audio = audio_response
            st.rerun()
