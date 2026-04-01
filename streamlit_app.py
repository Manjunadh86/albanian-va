import streamlit as st
import openai
import base64
import io
from audio_recorder_streamlit import audio_recorder

SYSTEM_PROMPT = """Ti je një asistent virtual inteligjent që flet shqip.
Përgjigju gjithmonë në shqip, pavarësisht gjuhës së pyetjes.
Ji i sjellshëm, i qartë dhe i dobishëm. Përgjigjet e tua duhet të jenë koncize por informuese.
Nëse dikush flet në një gjuhë tjetër, përgjigju në shqip duke i treguar se ti flet vetëm shqip.

You are an intelligent virtual assistant that speaks Albanian.
Always respond in Albanian, regardless of the language of the question.
Be polite, clear, and helpful. Your responses should be concise but informative."""


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
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=500,
        temperature=0.7,
    )
    return completion.choices[0].message.content or "Më falni, nuk munda të përgjigjem."


def synthesize_speech(client: openai.OpenAI, text: str, voice: str = "nova") -> bytes:
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text,
        response_format="mp3",
    )
    return response.read()


def autoplay_audio(audio_bytes: bytes):
    b64 = base64.b64encode(audio_bytes).decode()
    html = f"""
    <audio autoplay>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    </audio>
    """
    st.html(html)


# --- Page Config ---
st.set_page_config(
    page_title="Asistenti Shqiptar",
    page_icon="🇦🇱",
    layout="centered",
)

# --- Custom CSS ---
st.markdown("""
<style>
    .stApp {
        background-color: #09090b;
    }
    .main-header {
        text-align: center;
        padding: 1.5rem 0 1rem;
    }
    .main-header h1 {
        color: #fafafa;
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0;
    }
    .main-header p {
        color: #71717a;
        font-size: 0.8rem;
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
        margin-bottom: 0.5rem;
    }
    .chat-user {
        background-color: #2563eb;
        color: white;
        padding: 0.7rem 1rem;
        border-radius: 1rem 1rem 0.3rem 1rem;
        margin: 0.4rem 0;
        font-size: 0.9rem;
        max-width: 80%;
        margin-left: auto;
        text-align: right;
    }
    .chat-assistant {
        background-color: #27272a;
        color: #f4f4f5;
        padding: 0.7rem 1rem;
        border-radius: 1rem 1rem 1rem 0.3rem;
        margin: 0.4rem 0;
        font-size: 0.9rem;
        max-width: 80%;
    }
    .chat-label {
        font-size: 0.6rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        opacity: 0.6;
        margin-bottom: 0.25rem;
    }
    .status-text {
        text-align: center;
        color: #a1a1aa;
        font-size: 0.8rem;
        padding: 0.5rem;
    }
    div[data-testid="stAudioRecorder"] {
        display: flex;
        justify-content: center;
    }
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

st.divider()

# --- Voice recorder ---
st.markdown('<p class="status-text">Shtyp butonin e mikrofonit dhe fillo të flasësh shqip<br><small style="color:#52525b">Press the mic button and start speaking Albanian</small></p>', unsafe_allow_html=True)

audio_bytes = audio_recorder(
    text="",
    recording_color="#ef4444",
    neutral_color="#52525b",
    icon_size="2x",
    pause_threshold=2.5,
    sample_rate=44100,
)

# --- Process audio when recorded ---
if audio_bytes:
    if "last_audio" not in st.session_state or st.session_state.last_audio != audio_bytes:
        st.session_state.last_audio = audio_bytes

        client = get_openai_client()

        try:
            with st.spinner("Po dëgjoj... (Transcribing)"):
                transcript = transcribe_audio(client, audio_bytes)
        except Exception as e:
            st.error(f"Transcription failed: {e}")
            transcript = ""

        if not transcript.strip():
            st.warning("Nuk munda ta kuptoj audion. Provoni përsëri.")
        else:
            st.session_state.entries.append({"role": "user", "text": transcript})
            st.session_state.history.append({"role": "user", "content": transcript})

            with st.spinner("Po mendoj... (Thinking)"):
                response_text = generate_response(client, transcript, st.session_state.history[:-1])

            st.session_state.entries.append({"role": "assistant", "text": response_text})
            st.session_state.history.append({"role": "assistant", "content": response_text})

            with st.spinner("Po flas... (Speaking)"):
                audio_response = synthesize_speech(client, response_text)

            autoplay_audio(audio_response)
            st.rerun()

# --- Sidebar ---
with st.sidebar:
    st.markdown("### Cilësimet / Settings")
    if st.button("Pastro bisedat / Clear chat", use_container_width=True):
        st.session_state.history = []
        st.session_state.entries = []
        if "last_audio" in st.session_state:
            del st.session_state.last_audio
        st.rerun()
    st.markdown("---")
    st.markdown(
        '<small style="color:#71717a">Powered by OpenAI Whisper, GPT-4o & TTS</small>',
        unsafe_allow_html=True,
    )
