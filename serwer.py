"""
grunt.report — lokalny serwer demo
Uruchamia:
  - serwer HTTP serwujący index.html (frontend)
  - proxy do GUGiK ULDK (rozwiązuje problem CORS)

Wymaga: TYLKO Python 3.8+ (wszystko ze standardowej biblioteki, zero pip install)

Uruchomienie:
  python serwer.py

Następnie otwórz w przeglądarce:
  http://localhost:8000
"""

import http.server
import socketserver
import urllib.request
import urllib.parse
import urllib.error
import json
import os
import sys
from pathlib import Path

PORT = 8000
ULDK_BASE = "https://uldk.gugik.gov.pl/"

SCRIPT_DIR = Path(__file__).parent.resolve()


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SCRIPT_DIR), **kwargs)

    def do_GET(self):
        if self.path.startswith("/proxy/uldk"):
            self.handle_uldk_proxy()
        else:
            super().do_GET()

    def handle_uldk_proxy(self):
        """Proxuje GET na ULDK GUGiK - omija CORS"""
        try:
            parsed = urllib.parse.urlparse(self.path)
            query = parsed.query

            uldk_url = f"{ULDK_BASE}?{query}"
            print(f"[PROXY] → {uldk_url}", flush=True)

            req = urllib.request.Request(
                uldk_url,
                headers={
                    "User-Agent": "grunt.report-demo/1.0",
                    "Accept": "text/plain",
                },
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                body = response.read()
                content_type = response.headers.get("Content-Type", "text/plain")

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "public, max-age=3600")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            print(f"[PROXY] ← {len(body)} bajtów", flush=True)

        except urllib.error.HTTPError as e:
            print(f"[PROXY] ✗ HTTP {e.code}: {e.reason}", flush=True)
            self.send_error_json(502, f"GUGiK zwrócił HTTP {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            print(f"[PROXY] ✗ Network: {e.reason}", flush=True)
            self.send_error_json(503, f"Brak połączenia z GUGiK: {e.reason}")
        except Exception as e:
            print(f"[PROXY] ✗ Error: {e}", flush=True)
            self.send_error_json(500, f"Błąd serwera: {e}")

    def send_error_json(self, code, message):
        body = json.dumps({"error": message}).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        if "/proxy/uldk" not in str(args[0] if args else ""):
            sys.stderr.write(f"[HTTP] {format % args}\n")


def check_files():
    index_path = SCRIPT_DIR / "index.html"
    if not index_path.exists():
        print(f"\n  BŁĄD: nie znaleziono pliku 'index.html'")
        print(f"  Szukam tutaj: {index_path}\n")
        sys.exit(1)


def main():
    check_files()
    socketserver.TCPServer.allow_reuse_address = True

    try:
        with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
            print()
            print("  ╔══════════════════════════════════════════════════════╗")
            print("  ║                                                      ║")
            print("  ║     grunt.report — demo lokalne (GUGiK ULDK)        ║")
            print("  ║                                                      ║")
            print("  ╠══════════════════════════════════════════════════════╣")
            print("  ║                                                      ║")
            print(f"  ║   ▶  Otwórz w przeglądarce:                          ║")
            print(f"  ║                                                      ║")
            print(f"  ║      http://localhost:{PORT}                          ║")
            print("  ║                                                      ║")
            print("  ║   ▶  Zatrzymanie serwera: Ctrl+C                     ║")
            print("  ║                                                      ║")
            print("  ╚══════════════════════════════════════════════════════╝")
            print()
            print("  Logi (zapytania do GUGiK pojawią się tutaj):")
            print("  " + "─" * 54)
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n  Serwer zatrzymany. Do widzenia.\n")
        sys.exit(0)
    except OSError as e:
        if e.errno in (48, 98):
            print(f"\n  BŁĄD: Port {PORT} jest już zajęty.")
            print(f"  Spróbuj poczekać 30 sekund i uruchomić ponownie,")
            print(f"  albo zmień PORT na początku tego pliku (np. 8001).\n")
        else:
            print(f"\n  BŁĄD: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()