from snowboy import snowboydecoder
import sys
import signal
import time

from funcs import capture_image_usb, say
from api import post_face, get_reminders

from apscheduler.schedulers.background import BackgroundScheduler

interrupted = False

epoch = lambda: int(time.time() * 1000)
anti_epoch = lambda epoch: time.strftime("%a, %d %b %Y on %H:%M:%S", time.localtime(epoch))

recent_face_id = False
recent_face_id_time = -1
max_expire_time = 60 * 1000

recent_users = None

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
        say_string = ""
        for person_id, person_info in recent_users.items():
            say_string = person_info["msg"]
        say(say_string)
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
        print("> false alarm")
        return

    recent_face_id = False
    recent_face_id_time = -1

    say_string = ""
    for person_id, person_info in recent_users.items():
        print(person_info)
        say_string += person_info["additionalMsg"]

    say(say_string)

# TODO: add query reminders ability
def on_req_query_reminders():
    valid_reminds = [reminder for reminder in reminders if not reminder["tripped"]]
    say_string = f"You have {len(valid_reminds)} upcomming events. "
    for remind in reminders:
        date_time = anti_epoch(int(remind['epoch'] / 1000))
        if remind["type"] == "medication":
            say_string = f"You'll need to take your medication by {date_time}. "
        else: # type == appointment
            say_string = f"You'll need to attend your doctor's appointment by {date_time}. "

    say(say_string)

def signal_handler(signal, frame):
    global interrupted, scheduler
    scheduler.shutdown()
    interrupted = True

def track_reminders():
    print("Checking reminders...")
    reminders = get_reminders()
    for remind in reminders:
        remind["tripped"] = epoch() >= remind["epoch"]

    ticking_reminds = [remind for remind in reminders if not remind["tripped"]]
    for remind in ticking_reminds:
        delta_time = remind["epoch"] - epoch()
        check_times = [5 * 60 * 1000, 15 * 60 * 1000, 30 * 60 * 1000]
        error_margin = 10 * 1000

        # check if any reminders are within 1 second
        if delta_time <= 5 * 1000:
            if remind["type"] == "medication":
                say("You have to take your medication now!")
            else: # type == appointment
                say("You have to go to your doctor's appointment now!")
            remind["tripped"] = True
            return

        for ctime in check_times:
            if abs(delta_time - ctime) <= error_margin:
                mins = int(ctime / 60 / 1000)
                # check if any reminders are within the given minute marks, give or take 10 seconds
                if remind["type"] == "medication":
                    say(f"You have to take your medication in {mins} minutes!")
                else: # type == appointment
                    say(f"You have to go to your doctor's appointment in {mins} minutes!")
                return

def interrupt_callback():
    global interrupted
    return interrupted

if len(sys.argv) == 1:
    print("Error: need to specify the patient's name")
    print("Usage: python3.6 lib/client.py john")
    sys.exit(-1)

person = sys.argv[1]

print("Starting the reminder checker...")
scheduler = BackgroundScheduler()
scheduler.add_job(track_reminders, 'interval', seconds=10)
scheduler.start()

face_id_models = [ f"who_are_you-{person}", f"dont_remember_you-{person}" ]
face_id_callbacks = [on_req_face_identify] * len(face_id_models)

more_info_models = [ f"i_dont_understand-{person}", f"still_dont_remember-{person}" ]
more_info_callbacks = [on_req_more_info] * len(more_info_models)

reminder_recall_models = [ f"my_todo_list-{person}" ]
reminder_recall_callbacks = [on_req_query_reminders] * len(reminder_recall_models)

# assemble all to-be-loaded models for processing
combined_models = face_id_models + more_info_models + reminder_recall_models
final_models = ["hotword-models/" + model + ".pmdl" for model in combined_models]
combined_callbacks = face_id_callbacks + more_info_callbacks + reminder_recall_callbacks

# set sensitivities for all models
sensitivity_list = [0.5] * len(final_models)

# capture SIGINT signal, e.g., Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

detector = snowboydecoder.HotwordDetector(final_models, audio_gain=1, sensitivity=sensitivity_list)
print('Listening... Press Ctrl+C to exit')

# main loop
detector.start(detected_callback=combined_callbacks, interrupt_check=interrupt_callback, sleep_time=0.03)

detector.terminate()
