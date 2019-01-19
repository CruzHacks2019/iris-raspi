import sys
from base64 import b64encode
from io import BytesIO
from time import sleep
# from picamera import PiCamera
import os
import requests

API_BASE = sys.argv[-1]

os.system("fswebcam --resolution 1280x720 --no-banner temp.jpg")
img_content = open("temp.jpg", "rb").read()
b64 = b64encode(img_content)

print(b64.decode())
response = requests.post(f"{API_BASE}/detect-face", data=b64.decode())
print(response.text)
