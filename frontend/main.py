import base64
import http.server
import mimetypes
import os
import socketserver
import threading
import sys
import urllib.error
import urllib.request

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

    def log(self, message: str):
        """Receive log messages from the page and forward them to the Python console."""
        try:
            print(f"[webview] {message}")
        except Exception:
            pass

# when in the frontend directory, run .\.venv\Scripts\Activate.ps1 (to get into the venv)
# then run python main.py to start the server and open the webview window

PORT = 3000
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# The backend runs on a different port, so a browser fetch from this page would
# be cross-origin and get blocked by CORS. Instead the page calls same-origin
# (localhost:3000) and we forward anything under these prefixes to the backend.
BACKEND_BASE = "http://localhost:8000"
PROXY_PREFIXES = ("/health", "/classes", "/examples", "/search",
                    "/predict", "/sort", "/shutdown", "/api")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def _should_proxy(self):
        return self.path.startswith(PROXY_PREFIXES)

    def _proxy(self):
        """Forward the current request to the backend and relay its response."""
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else None

        req = urllib.request.Request(BACKEND_BASE + self.path, data=body, method=self.command)
        for key, value in self.headers.items():
            # Skip hop-by-hop / host headers; urllib sets these itself.
            if key.lower() in ("host", "content-length", "connection"):
                continue
            req.add_header(key, value)

        try:
            with urllib.request.urlopen(req) as resp:
                self._relay(resp.status, resp.headers, resp.read())
        except urllib.error.HTTPError as e:
            # Backend answered with a 4xx/5xx; pass it through unchanged.
            self._relay(e.code, e.headers, e.read())
        except Exception as e:
            self.send_error(502, f"Backend unreachable via proxy: {e}")

    def _relay(self, status, headers, payload):
        self.send_response(status)
        ctype = headers.get("Content-Type")
        if ctype:
            self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self._should_proxy():
            self._proxy()
        else:
            super().do_GET()

    def do_POST(self):
        self._proxy()

    def do_DELETE(self):
        self._proxy()


# ThreadingTCPServer so a slow backend call (e.g. /predict, /sort) doesn't block
# the page from loading its other static assets in the meantime.
class ThreadingHTTPServer(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


def start_server():
    with ThreadingHTTPServer(("", PORT), Handler) as httpd:
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
