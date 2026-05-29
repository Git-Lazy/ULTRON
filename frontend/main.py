import http.server
import os
import socketserver
import threading
import sys

try:
    import webview
    HAS_WEBVIEW = True
except ImportError:
    HAS_WEBVIEW = False

# when in the frontend directory, run .\.venv\Scripts\Activate.ps1 (to get into the venv)
# then run python main.py to start the server and open the webview window

PORT = 3000
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)


def start_server():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Frontend server running on http://localhost:{PORT}")
        httpd.serve_forever()


if __name__ == "__main__":
    threading.Thread(target=start_server, daemon=True).start()
    
    # Only use webview if it's available (not in Docker)
    if HAS_WEBVIEW and not os.environ.get('DOCKER_CONTAINER'):
        webview.create_window("Ultron", f"http://localhost:{PORT}")
        webview.start()
    else:
        # In Docker or without webview, just keep the server running
        print("Running in headless mode (no webview)")
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            sys.exit(0)
