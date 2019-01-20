import sys

import requests

API_BASE = "http://1f757ced.ngrok.io" # sys.argv[-1]

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
        return response.json()
    except Exception as ex:
        print(response.text)
        return None
