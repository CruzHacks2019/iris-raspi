import sys

import requests

API_BASE = sys.argv[-1]  # TODO


def post_face(face):
    """Posts face (a base-64 encoded bytes object) and returns... something."""
    response = requests.post(f"{API_BASE}/detect-face", data=face.decode())
    return response.json()