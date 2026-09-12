"""Winziger lokaler HTTP-Server, der POST-Bodies in Dateien schreibt.

Zweck: Geheimnisse (API-Keys, Cookies) aus dem Playwright-Browser direkt auf
die Platte holen, ohne dass sie durch das Chat-Transkript laufen.

    python savesrv.py <zielordner> <port>
"""
import http.server
import os
import sys

ZIEL = sys.argv[1]
PORT = int(sys.argv[2])


class H(http.server.BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "POST,OPTIONS")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        name = os.path.basename(self.headers.get("x-target", "dump.txt"))
        n = int(self.headers.get("Content-Length", 0))
        data = self.rfile.read(n)
        with open(os.path.join(ZIEL, name), "wb") as f:
            f.write(data)
        self.send_response(200)
        self._cors()
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *a):
        pass


http.server.HTTPServer(("127.0.0.1", PORT), H).serve_forever()
