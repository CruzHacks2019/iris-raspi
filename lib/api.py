import sys
import time
import requests

API_BASE = "http://689afc05.ngrok.io" # sys.argv[-1]

epoch = lambda: int(time.time() * 1000)

def post_face(face_data):
    """Posts face (a base-64 encoded bytes object) and returns...something."""
    response = requests.post(f"{API_BASE}/detect-face", data=face_data)
    try:
        return response.json()
    except Exception as ex:
        print(response.text)
        return None

def get_reminders():
    """Retrieves all reminders for use with proactive notifications"""
    response = requests.get(f"{API_BASE}/reminders")
    try:
        reminders = response.json()
        for remind in reminders:
            remind["tripped"] = epoch() >= remind["epoch"]
        return reminders
    except Exception as ex:
        print(ex)
        print(response.text)
        return None
