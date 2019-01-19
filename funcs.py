import sys
from base64 import b64encode
from io import BytesIO

import requests
from google.cloud import texttospeech
from picamera import PiCamera
from pydub import AudioSegment
from pydub.playback import play

API_BASE = sys.argv[-1]
camera = PiCamera()
camera.start_preview()
ttsclient = texttospeech.TextToSpeechClient()


def say(text):
    """Plays some text using GCP's TTS API."""
    # Set the text input to be synthesized
    synthesis_input = texttospeech.types.SynthesisInput(text=text)

    # Build the voice request, select the language code ("en-US") and the ssml
    # voice gender ("neutral")
    voice = texttospeech.types.VoiceSelectionParams(
        language_code='en-US',
        ssml_gender=texttospeech.enums.SsmlVoiceGender.NEUTRAL)

    # Select the type of audio file you want returned
    audio_config = texttospeech.types.AudioConfig(
        audio_encoding=texttospeech.enums.AudioEncoding.MP3)

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = ttsclient.synthesize_speech(synthesis_input, voice, audio_config)

    song = AudioSegment.from_file(BytesIO(response.audio_content), format="mp3")
    play(song)


def post_image():
    """Captures an image from the camera and posts it to the API in base64 encoding."""
    io = BytesIO()
    camera.capture(io, 'jpeg')
    b64 = b64encode(io.getvalue())
    requests.post(f"{API_BASE}/detect-face", data=b64.decode())
