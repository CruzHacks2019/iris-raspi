from snowboy import snowboydecoder
import sys
import signal

from funcs import capture_image_usb, say
from api import post_face

interrupted = False

def on_hotword_trigger():
    print("> Capturing image from USB camera...", end="")
    face64 = capture_image_usb()
    print("done!")

    print("> Posting to backend...", end="")
    response = post_face(face64)
    print("done!")

    print("RESPONSE")
    print(response)

    if response and response.msg:
        say(response.msg)

def signal_handler(signal, frame):
    global interrupted
    interrupted = True

def interrupt_callback():
    global interrupted
    return interrupted

if len(sys.argv) == 1:
    print("Error: need to specify model name")
    print("Usage: python client.py your.model")
    sys.exit(-1)

model = sys.argv[1]

# capture SIGINT signal, e.g., Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

detector = snowboydecoder.HotwordDetector(model, audio_gain=1, sensitivity=0.5)
print('Listening... Press Ctrl+C to exit')

# main loop
detector.start(detected_callback=on_hotword_trigger,
               interrupt_check=interrupt_callback,
               sleep_time=0.03)

detector.terminate()
