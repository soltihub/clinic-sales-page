"""WSGI entry point (PythonAnywhere). Reuses the handlers in app.py."""
import io
from email.message import Message
import app

class _W(app.H):
    def __init__(self, environ):
        self.environ = environ
        self.path = environ.get("PATH_INFO", "/") or "/"
        self.headers = Message()
        for k, v in environ.items():
            if k.startswith("HTTP_"): self.headers[k[5:].replace("_", "-").title()] = v
        if environ.get("CONTENT_LENGTH"): self.headers["Content-Length"] = environ["CONTENT_LENGTH"]
        self.rfile = environ["wsgi.input"]
        ip = (environ.get("HTTP_X_REAL_IP") or environ.get("REMOTE_ADDR") or "0").split(",")[0].strip()
        self.client_address = (ip, 0)
        self.out = None
    def send(self, code, body, ctype="text/html; charset=utf-8", extra=None):
        b = body.encode() if isinstance(body, str) else body
        h = [("Content-Type", ctype), ("Content-Length", str(len(b))),
             ("X-Content-Type-Options", "nosniff"), ("X-Frame-Options", "DENY"),
             ("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; media-src 'self'")]
        h += list((extra or {}).items())
        self.out = (code, h, b)

REASONS = {200:"OK",303:"See Other",400:"Bad Request",401:"Unauthorized",404:"Not Found",405:"Method Not Allowed",413:"Payload Too Large",429:"Too Many Requests"}
app.db()

def application(environ, start_response):
    w = _W(environ)
    m = environ.get("REQUEST_METHOD", "GET")
    if m == "GET": w.do_GET()
    elif m == "POST": w.do_POST()
    else: w.send(405, "Method not allowed", "text/plain")
    code, h, b = w.out
    start_response(f"{code} {REASONS.get(code,'OK')}", h)
    return [b]
