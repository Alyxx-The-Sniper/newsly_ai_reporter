from typing import Dict
from openai import OpenAI
from ..config import settings


def transcribe_fast(state: Dict) -> Dict:
    audio_path = state.get("audio_path")
    if not audio_path:
        state["transcribed_text"] = None
        return state
    client = OpenAI(api_key=settings.openai_api_key)
    try:
        with open(audio_path, "rb") as f:
            txt = client.audio.transcriptions.create(model="whisper-1", file=f, response_format="text")
        state["transcribed_text"] = txt.strip()
    except Exception as e:
        state["transcribed_text"] = f"Error during transcription: {e}"
    return state