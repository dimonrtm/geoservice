"""Проверка proxy boundary с настоящим parser; без БД и доменного Save."""

import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path.cwd()))
from utility_service.web_api.parsers.geometry_save_request import (
    parse_geometry_save_request,
)


class Handler(BaseHTTPRequestHandler):
    def do_PUT(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        parsed = parse_geometry_save_request(body)
        result = json.dumps({"vertices": len(parsed.geometry.coordinates)}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(result)))
        self.end_headers()
        self.wfile.write(result)

    def log_message(self, *_args):
        pass


def request(host, port, body):
    connection = http.client.HTTPConnection(host, port, timeout=15)
    try:
        connection.request(
            "PUT",
            "/api/v1/work-orders/probe/edit-versions/probe/features/probe/geometry",
            body=body,
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        payload = response.read()
        return {
            "status": response.status,
            "content_type": response.getheader("Content-Type"),
            "response": payload.decode()[:200],
        }
    finally:
        connection.close()


if sys.argv[1] == "server":
    ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
else:
    results = []
    for count in (3, 60_000):
        # Разные последовательные XY на прямой: без дубликатов и самопересечений.
        body = json.dumps(
            {
                "commandId": "00000000-0000-4000-8000-000000000001",
                "draftVersionToken": "1",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [round(55 + i / 10_000_000, 7), 54.1234567]
                        for i in range(count)
                    ],
                },
            },
            separators=(",", ":"),
        ).encode()
        for attempt in range(30):
            try:
                direct = request("utility_service", 8000, body)
                proxied = request("proxy", 80, body)
                break
            except OSError:
                if attempt == 29:
                    raise
                time.sleep(0.2)
        results.append(
            {
                "vertices": count,
                "body_bytes": len(body),
                "direct_parser": direct,
                "current_nginx": proxied,
            }
        )
    assert results[0]["direct_parser"]["status"] == 200
    assert results[0]["current_nginx"]["status"] == 200
    assert results[1]["direct_parser"]["status"] == 200
    assert results[1]["current_nginx"]["status"] == 413
    print(
        json.dumps(
            {
                "scope": "real parser + real nginx; no auth, database or domain Save",
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
