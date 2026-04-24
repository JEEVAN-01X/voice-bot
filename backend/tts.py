from google.cloud import texttospeech
import os



tts_client = texttospeech.TextToSpeechClient()

VOICE_MAP = {
    'en-IN': 'en-IN-Wavenet-A',
    'hi-IN': 'hi-IN-Wavenet-A',
    'kn-IN': 'kn-IN-Wavenet-A',
    'mr-IN': 'mr-IN-Wavenet-A',
}

def synthesize_speech(text: str, language_code: str) -> bytes:
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name=VOICE_MAP.get(language_code, 'en-IN-Wavenet-A'),
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    response = tts_client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    return response.audio_content
