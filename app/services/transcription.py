from typing import Dict
from openai import OpenAI
from ..config import settings


# FOR OPENAI ####
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

# ## FOR DEEPINFRA ####
# def transcribe_fast(state: Dict) -> Dict:
#     """
#     Transcribes an audio file using a Whisper model hosted on DeepInfra.
#     """
#     audio_path = state.get("audio_path")
#     if not audio_path:
#         state["transcribed_text"] = None
#         return state

#     # Configure the client to use DeepInfra's API
#     client = OpenAI(
#         api_key=settings.deepinfra_api_key,
#         base_url="https://api.deepinfra.com/v1/openai" # <-- CORRECTED ENDPOINT
#     )

#     try:
#         with open(audio_path, "rb") as audio_file:
#             # The model is correctly specified here
#             transcription = client.audio.transcriptions.create(
#                 model="openai/whisper-large-v3",
#                 file=audio_file,
#                 response_format="text"
#             )
#         state["transcribed_text"] = transcription.strip()
#     except Exception as e:
#         state["transcribed_text"] = f"Error during transcription: {e}"

#     return state