import subprocess
import time
import requests
import sys
import os

def resource_path(relative_path):
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)

def wait_for_service(url, timeout=120):
    start = time.time()
    while time.time() - start < timeout:
        try:
            requests.get(url, timeout=1)
            return True
        except Exception:
            time.sleep(0.5)
    return False

model = subprocess.Popen(
    [resource_path("./dist/model.exe")],
    creationflags=subprocess.CREATE_NO_WINDOW
)
if not wait_for_service("http://localhost:8001/health"):
    print("Model failed to start!")
    model.terminate()
    exit(1)
print("Model Started!")
backend = subprocess.Popen(
    [resource_path("./dist/backend.exe")],
    creationflags=subprocess.CREATE_NO_WINDOW
)
if not wait_for_service("http://localhost:8000/health"):
    print("Backend failed to start!")
    model.terminate()
    backend.terminate()
    exit(1)
print("Backend Started!")
frontend = subprocess.Popen(
    [resource_path("./dist/frontend.exe")],
    creationflags=subprocess.CREATE_NO_WINDOW
)
print("Frontend Started!")

frontend.wait()
requests.get("http://localhost:8000/shutdown")