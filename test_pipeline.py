"""
Quick test script for the Albanian Voice Assistant pipeline.
Tests each OpenAI step independently: LLM → TTS → STT round-trip.

Usage:
    python test_pipeline.py
"""

import os
import io
import sys
import asyncio

try:
    import openai
    import edge_tts
except ImportError:
    sys.exit("Run: pip install openai edge-tts")

API_KEY = os.environ.get("OPENAI_API_KEY", "")

if not API_KEY:
    dotenv = os.path.join(os.path.dirname(__file__), ".env.local")
    if os.path.exists(dotenv):
        for line in open(dotenv):
            if line.strip().startswith("OPENAI_API_KEY"):
                API_KEY = line.split("=", 1)[1].strip().strip('"')

    secrets = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")
    if not API_KEY and os.path.exists(secrets):
        for line in open(secrets):
            if "OPENAI_API_KEY" in line:
                API_KEY = line.split("=", 1)[1].strip().strip('"')

if not API_KEY:
    sys.exit("No OPENAI_API_KEY found in env, .env.local, or .streamlit/secrets.toml")

client = openai.OpenAI(api_key=API_KEY)

SYSTEM_PROMPT = (
    "Ti je Elira, një vajzë shqiptare nga Tirana. Flet si shqiptare e vërtetë — natyrisht, lirshëm, jo si tekst i përkthyer. "
    "Përdor shprehje natyrale: 'ore', 'pra', 's'ka gjë', 'hajde'. "
    "Shkurto si në të folur: 's'kam' jo 'nuk kam', 's'di' jo 'nuk di'. "
    "Përgjigju SHKURT, 1-2 fjali, si bisedë me zë. Mos përkthe nga anglishtja — mendo direkt në shqip."
)

TEST_PROMPTS = [
    "Përshëndetje! Si je?",
    "Çfarë është kryeqyteti i Shqipërisë?",
    "Më thuaj një fakt interesant për Shqipërinë.",
]


def test_llm(prompt: str) -> str:
    print(f"\n{'='*50}")
    print(f"[TEST LLM] Prompt: {prompt}")
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=150,
        temperature=0.8,
    )
    text = resp.choices[0].message.content
    print(f"[RESPONSE] {text}")
    return text


def test_tts(text: str) -> bytes:
    print(f"\n[TEST TTS] Synthesizing with native Albanian voice: {text[:60]}...")

    async def _gen():
        comm = edge_tts.Communicate(text, "sq-AL-AnilaNeural", rate="+5%")
        chunks = []
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])
        return b"".join(chunks)

    audio = asyncio.run(_gen())
    print(f"[OK] Generated {len(audio):,} bytes of MP3 (native sq-AL-AnilaNeural)")
    return audio


def test_stt(audio_bytes: bytes) -> str:
    print(f"\n[TEST STT] Transcribing {len(audio_bytes):,} bytes...")
    audio_file = ("test.mp3", io.BytesIO(audio_bytes), "audio/mp3")
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
    )
    print(f"[TRANSCRIPT] {transcription.text}")
    return transcription.text


def main():
    print("Albanian Voice Assistant — Pipeline Test")
    print("=" * 50)

    # Step 1: LLM
    print("\n--- STEP 1: Testing LLM (GPT-4o) ---")
    for prompt in TEST_PROMPTS:
        response_text = test_llm(prompt)

    # Step 2: TTS on the last response
    print("\n--- STEP 2: Testing TTS ---")
    audio = test_tts(response_text)

    # Save audio to file for manual listening
    out_path = os.path.join(os.path.dirname(__file__), "test_output.mp3")
    with open(out_path, "wb") as f:
        f.write(audio)
    print(f"[SAVED] {out_path} — open to listen")

    # Step 3: STT round-trip (feed TTS output back to Whisper)
    print("\n--- STEP 3: Testing STT (round-trip) ---")
    transcript = test_stt(audio)

    print(f"\n{'='*50}")
    print("ALL TESTS PASSED")
    print(f"  LLM:  ✓ ({len(TEST_PROMPTS)} prompts)")
    print(f"  TTS:  ✓ ({len(audio):,} bytes)")
    print(f"  STT:  ✓ ('{transcript[:50]}...')" if len(transcript) > 50 else f"  STT:  ✓ ('{transcript}')")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
