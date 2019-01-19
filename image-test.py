import sys
from base64 import b64encode
from io import BytesIO
from time import sleep
from picamera import PiCamera
import requests

API_BASE = sys.argv[-1]

# Explicitly open a new file called my_image.jpg
io = BytesIO()
camera = PiCamera()
camera.start_preview()
sleep(2)
camera.capture(io, 'jpeg')
b64 = b64encode(io.getvalue())

print(b64.decode())
requests.post(f"{API_BASE}/detect-face", data=b64.decode())
