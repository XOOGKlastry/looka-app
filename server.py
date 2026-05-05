import os
print("CWD:", os.getcwd())
print("Files:", os.listdir('.'))
"""
looka.app — serwer Flask (dla Render)
"""
import os
import requests
from flask import Flask, request, jsonify, send_from_directory, Response

app = Flask(__name__, static_folder='.', static_url_path='')

ULDK_BASE = "https://uldk.gugik.gov.pl/"


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)


@app.route('/proxy/uldk')
def proxy_uldk():
    try:
        qs = request.query_string.decode('utf-8')
        r = requests.get(
            f"{ULDK_BASE}?{qs}",
            headers={
                "User-Agent": "looka.app/1.0",
                "Accept": "text/plain",
            },
            timeout=15,
        )
        r.raise_for_status()
        return Response(
            r.content,
            status=200,
            content_type=r.headers.get('Content-Type', 'text/plain'),
            headers={
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'public, max-age=3600',
            },
        )
    except requests.HTTPError as e:
        return jsonify({"error": f"GUGiK zwrócił HTTP {e.response.status_code}"}), 502
    except requests.RequestException as e:
        return jsonify({"error": f"Brak połączenia z GUGiK: {e}"}), 503
    except Exception as e:
        return jsonify({"error": f"Błąd serwera: {e}"}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
