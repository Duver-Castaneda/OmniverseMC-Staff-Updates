"""
healthcheck_wrapper.py — starts a minimal HTTP health server on port 8000
then runs the Discord bot in the same process using asyncio.
"""
import asyncio
import http.server
import threading
import runpy

# ── Tiny health server (daemon thread) ───────────────────────────────────────
class _HealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, *args):
        pass  # suppress access logs


def _start_health_server(port: int = 8000):
    server = http.server.HTTPServer(("0.0.0.0", port), _HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    _start_health_server(8000)
    # Run bot.py as __main__ so its `if __name__ == "__main__":` block executes
    runpy.run_path("bot.py", run_name="__main__")
