import sys

import requests

API_BASE = "http://5dd7b57f.ngrok.io" # sys.argv[-1]

def post_face(face):
    """Posts face (a base-64 encoded bytes object) and returns... something."""
    response = requests.post(f"{API_BASE}/detect-face", data=face.decode())
    try:
        return response.json()
    except Exception as ex:
        print(response.text)
        return None
