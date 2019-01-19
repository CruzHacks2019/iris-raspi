from io import BytesIO

from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play


def run():
    out = input("String to say: ")
    mp3_fp = BytesIO()
    tts = gTTS(out, 'en')
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)

    song = AudioSegment.from_file(mp3_fp, format="mp3")
    play(song)


if __name__ == '__main__':
    while True:
        run()
