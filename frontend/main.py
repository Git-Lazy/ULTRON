import base64
import http.server
import mimetypes
import os
import socketserver
import threading
import sys

try:
    import webview
    HAS_WEBVIEW = True
except ImportError:
    HAS_WEBVIEW = False


class Api:
    """Exposed to the page as ``pywebview.api``.

    A plain HTML <input type=file> only gives JS a sandboxed name
    (``C:\\fakepath\\foo.jpg``), so the backend can never resolve it. These
    methods open pywebview's *native* file dialog and return the real absolute
    path, which the backend (running on the same machine) can read directly.
    """

    def __init__(self):
        # Stored with a leading underscore so pywebview does NOT expose it to
        # JS. Exposing it would make pywebview serialize the native WinForms
        # window object, whose .NET properties (Bounds.Empty...) recurse
        # infinitely and crash startup with "maximum recursion depth exceeded".
        self._window = None

    _IMAGE_TYPES = ("Image Files (*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.tiff;*.webp)",
                    "All files (*.*)")

    def pick_image(self):
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=self._IMAGE_TYPES,
        )
        if not result:
            return None
        path = result[0]
        # Inline a base64 thumbnail so the existing <img> preview keeps working
        # without the backend having to serve the file back.
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("ascii")
        mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
        return {"path": path, "data_url": f"data:{mime};base64,{encoded}"}

    def pick_folder(self):
        result = self._window.create_file_dialog(webview.FOLDER_DIALOG)
        if not result:
            return None
        return {"path": result[0]}

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
        api = Api()
        api._window = webview.create_window("Ultron", f"http://localhost:{PORT}", js_api=api)
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
