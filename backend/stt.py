from google.cloud import speech
import os

os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", "./google-creds.json")

stt_client = speech.SpeechClient()

def transcribe_audio(audio_bytes: bytes, language_code: str) -> str:
    audio = speech.RecognitionAudio(content=audio_bytes)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=8000,
        language_code=language_code,
        alternative_language_codes=['en-IN'],
        enable_automatic_punctuation=True,
        model='phone_call',
    )
    response = stt_client.recognize(config=config, audio=audio)
    if response.results:
        best = response.results[0].alternatives[0]
        return best.transcript, best.confidence
    return '', 0.0
