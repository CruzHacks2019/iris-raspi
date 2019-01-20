from snowboy import snowboydecoder
import sys
import signal
import time

from funcs import capture_image_usb, say
from api import post_face, get_reminders

interrupted = False

epoch = lambda: int(time.time() * 1000)

recent_face_id = False
recent_face_id_time = -1
max_expire_time = 60 * 1000

recent_users = None

def map_range(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - leftMin) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)


reminders = get_reminders()
if reminders is None:
    print("Warning: couldn't obtain reminders!")
else:
    for (index, remind) in enumerate(reminders):
        max_epoch_delta = 1000 * 10
        remind["epoch"] = epoch() + map_range(index, 0, len(reminders) - 1, -max_epoch_delta, max_epoch_delta)
        remind["tripped"] = epoch() >= remind["epoch"]
        print(remind)

def on_req_face_identify():
    global recent_face_id, recent_face_id_time, max_expire_time, recent_users
    print("on_req_face_identify")

    print("> Capturing image from USB camera...")
    img_data = capture_image_usb()

    print("> Posting to backend...")
    response = post_face(img_data)

    print("RESPONSE")
    print(response)
    recent_users = response

    if response is None:
        say("An unknown error has occurred!")
    elif 'error' in response:
        say(response['error'])
    elif len(response) > 0:
        for person_id, person_info in recent_users.items():
            say(person_info["msg"])
        recent_face_id = True
        recent_face_id_time = epoch()
    else:
        say("An unknown error has occurred!")

def on_req_more_info():
    global recent_face_id, recent_face_id_time, max_expire_time, recent_users
    print("on_req_more_info")
    print(epoch(), recent_face_id_time)

    # check if previous command was called or if just enough time has passed for the context to be relevent
    if not recent_face_id or epoch() - recent_face_id_time > max_expire_time:
        print("  false alarm")
        return

    recent_face_id = False
    recent_face_id_time = -1

    for person_id, person_info in recent_users.items():
        print(person_info)
        say(person_info["additionalMsg"])

def signal_handler(signal, frame):
    global interrupted
    interrupted = True

# TODO: implement reminder check and alerts
# use interupt_callback to check time continuously
def interrupt_callback():
    global interrupted, reminders
    for remind in reminders:
        # check of any reminder is within 1 second
        if not remind["tripped"] and abs(epoch() - remind["epoch"]) < 1000:
            if remind["type"] == "medication":
                say("You have to take your medication!")
            else: # type == appointment
                say("You have to go to your doctor's appointment!")
            remind["tripped"] = True
    return interrupted

if len(sys.argv) == 1:
    print("Error: need to specify the patient's name")
    print("Usage: python lib/client.py john")
    sys.exit(-1)

person = sys.argv[1]

face_id_models = [
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
