from base64 import b64encode
from io import BytesIO

from google.cloud import texttospeech
from picamera import PiCamera
from pydub import AudioSegment
from pydub.playback import play

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


def capture_image():
    """Captures an image from the camera and returns the base64-encoded bytes."""
    io = BytesIO()
    camera.capture(io, 'jpeg')
    return b64encode(io.getvalue())
