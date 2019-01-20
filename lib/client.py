from snowboy import snowboydecoder
import sys
import signal
import time

from funcs import capture_image_usb, say
from api import post_face, get_reminders

interrupted = False

recent_face_id = False
recent_face_id_time = -1
max_expire_time = 60 * 1000

recent_users = None

reminders = get_reminders()
if reminders is None:
    print("Warning: couldn't obtain reminders!")

epoch = lambda: int(time.time() * 1000)

def on_req_face_identify():
    global recent_face_id, recent_face_id_time, max_expire_time
    print("on_req_face_identify")

    print("> Capturing image from USB camera...")
    face64 = capture_image_usb()

    print("> Posting to backend...")
    response = post_face(face64)

    print("RESPONSE")
    print(response)
    recent_users = response

    if response is None:
        say("An unknown error has occurred!")
    elif 'msg' in response:
        say(response['msg'])
        recent_face_id = True
        recent_face_id_time = epoch()
    elif 'error' in response:
        say(response['error'])
    else:
        say("An unknown error has occurred!")

# TODO: implement requesting more info
def on_req_more_info():
    global recent_face_id, recent_face_id_time, max_expire_time
    print("on_req_more_info")
    print(epoch() - recent_face_id_time)

    # check if previous command was called or if just enough time has passed for the context to be relevent
    if not recent_face_id or epoch() - recent_face_id_time > max_expire_time:
        print("  false alarm")
        return

    recent_face_id = False
    recent_face_id_time = -1

    for person_id, person_info in recent_users:
        say(person_info["additionalMsg"])

def signal_handler(signal, frame):
    global interrupted
    interrupted = True

# TODO: implement reminder check and alerts
# use interupt_callback to check time continuously
def interrupt_callback():
    global interrupted
    pass
    return interrupted

if len(sys.argv) == 1:
    print("Error: need to specify the patient's name")
    print("Usage: python lib/client.py john")
    sys.exit(-1)

person = sys.argv[1]

face_id_models = [
  f"who_is_that-{person}",
  f"who_are_you-{person}",
  f"dont_remember_you-{person}"
]

face_id_callbacks = [on_req_face_identify] * len(face_id_models)

more_info_models = [
  f"i_dont_understand-{person}",
  f"still_dont_remember-{person}"
]

more_info_callbacks = [on_req_more_info] * len(more_info_models)

# assemble all to-be-loaded models for processing
combined_models = face_id_models + more_info_models
final_models = ["hotword-models/" + model + ".pmdl" for model in combined_models]

# merge all callback paths
combined_callbacks = face_id_callbacks + more_info_callbacks

# set sensitivities for all models
sensitivity_list = [0.5] * len(final_models)

# capture SIGINT signal, e.g., Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

detector = snowboydecoder.HotwordDetector(final_models, audio_gain=1, sensitivity=sensitivity_list)
print('Listening... Press Ctrl+C to exit')

# main loop
detector.start(detected_callback=combined_callbacks,
               interrupt_check=interrupt_callback,
               sleep_time=0.03)

detector.terminate()
