import streamlit as st
import openai
import base64
import io
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
        model="gpt-4o",
        messages=messages,
        max_tokens=150,
        temperature=0.8,
    )
    return completion.choices[0].message.content or "Më falni, nuk munda të përgjigjem."


def synthesize_speech(client: openai.OpenAI, text: str, voice: str = "nova") -> bytes:
    response = client.audio.speech.create(
        model="tts-1-hd",
        voice=voice,
        input=text,
        response_format="mp3",
        speed=1.05,
    )
    return response.read()


# --- Page Config ---
st.set_page_config(
    page_title="Asistenti Shqiptar",
    page_icon="🇦🇱",
    layout="centered",
)

# --- Custom CSS with animated mic ---
st.markdown("""
<style>
    .stApp { background-color: #09090b; }
    [data-testid="stHeader"] { background-color: #09090b; }
    [data-testid="stSidebar"] { background-color: #18181b; }

    .main-header {
        text-align: center;
        padding: 1.2rem 0 0.8rem;
    }
    .main-header h1 {
        color: #fafafa;
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
    }
    .main-header p {
        color: #71717a;
        font-size: 0.75rem;
        margin: 0;
    }
    .al-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 2.2rem;
        height: 2.2rem;
        border-radius: 0.5rem;
        background: linear-gradient(135deg, #dc2626, #991b1b);
        color: white;
        font-weight: 700;
        font-size: 0.85rem;
        margin-bottom: 0.4rem;
    }

    .chat-user {
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        color: white;
        padding: 0.65rem 1rem;
        border-radius: 1rem 1rem 0.25rem 1rem;
        margin: 0.35rem 0;
        font-size: 0.88rem;
        max-width: 80%;
        margin-left: auto;
        text-align: right;
        line-height: 1.45;
    }
    .chat-assistant {
        background: linear-gradient(135deg, #27272a, #303035);
        color: #f4f4f5;
        padding: 0.65rem 1rem;
        border-radius: 1rem 1rem 1rem 0.25rem;
        margin: 0.35rem 0;
        font-size: 0.88rem;
        max-width: 80%;
        line-height: 1.45;
    }
    .chat-label {
        font-size: 0.58rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        opacity: 0.55;
        margin-bottom: 0.2rem;
    }

    /* ---- Animated mic container ---- */
    .mic-zone {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 1.5rem 0 0.5rem;
        gap: 0.5rem;
    }
    .mic-ring {
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .mic-ring::before, .mic-ring::after {
        content: '';
        position: absolute;
        border-radius: 50%;
        border: 2px solid rgba(239, 68, 68, 0.25);
        animation: mic-pulse 2s ease-in-out infinite;
    }
    .mic-ring::before {
        width: 90px; height: 90px;
        animation-delay: 0s;
    }
    .mic-ring::after {
        width: 110px; height: 110px;
        animation-delay: 0.5s;
    }

    @keyframes mic-pulse {
        0%   { transform: scale(0.95); opacity: 0.5; }
        50%  { transform: scale(1.12); opacity: 0.15; }
        100% { transform: scale(0.95); opacity: 0.5; }
    }

    .mic-label {
        color: #a1a1aa;
        font-size: 0.72rem;
        text-align: center;
        letter-spacing: 0.03em;
    }
    .mic-sublabel {
        color: #52525b;
        font-size: 0.62rem;
    }

    /* Keep recorder centered and always visible */
    div[data-testid="stAudioRecorder"] {
        display: flex !important;
        justify-content: center !important;
        visibility: visible !important;
    }

    /* Style the audio player */
    audio { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div class="main-header">
    <div class="al-badge">AL</div>
    <h1>Asistenti Shqiptar</h1>
    <p>Albanian Voice Assistant</p>
</div>
""", unsafe_allow_html=True)

# --- Session state ---
if "history" not in st.session_state:
    st.session_state.history = []
if "entries" not in st.session_state:
    st.session_state.entries = []
if "pending_audio" not in st.session_state:
    st.session_state.pending_audio = None

# --- Display chat history ---
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

# --- Play pending audio AFTER rerun so it doesn't get cut off ---
if st.session_state.pending_audio is not None:
    audio_data = st.session_state.pending_audio
    st.session_state.pending_audio = None
    b64 = base64.b64encode(audio_data).decode()
    st.markdown(
        f"""<audio autoplay controls style="display:none">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mpeg">
        </audio>""",
        unsafe_allow_html=True,
    )
    st.audio(audio_data, format="audio/mp3", autoplay=True)

st.divider()

# --- Animated mic zone + recorder ---
st.markdown("""
<div class="mic-zone">
    <div class="mic-ring"></div>
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
<div style="text-align:center; padding-top: 0.3rem;">
    <div class="mic-label">Shtyp butonin e mikrofonit dhe fillo të flasësh</div>
    <div class="mic-sublabel">Press the mic and start speaking</div>
</div>
""", unsafe_allow_html=True)

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
                audio_response = synthesize_speech(client, response_text)

            st.session_state.pending_audio = audio_response
            st.rerun()

# --- Sidebar ---
with st.sidebar:
    st.markdown("### Cilësimet / Settings")
    if st.button("🗑️ Pastro bisedat / Clear chat", use_container_width=True):
        st.session_state.history = []
        st.session_state.entries = []
        st.session_state.pending_audio = None
        if "last_audio" in st.session_state:
            del st.session_state.last_audio
        st.rerun()
    st.markdown("---")
    st.markdown(
        '<small style="color:#71717a">Powered by OpenAI Whisper, GPT-4o & TTS-HD</small>',
        unsafe_allow_html=True,
    )
