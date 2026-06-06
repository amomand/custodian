from __future__ import annotations

import argparse
import ipaddress
import json
import mimetypes
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from custodian.web_session import SessionNotFound, SessionStore


STATIC_ROOT = Path(__file__).with_name("web_static")


class CustodianHttpServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        RequestHandlerClass: type[BaseHTTPRequestHandler],
        store: SessionStore | None = None,
    ) -> None:
        super().__init__(server_address, RequestHandlerClass)
        self.store = store or SessionStore()


class CustodianRequestHandler(BaseHTTPRequestHandler):
    server: CustodianHttpServer

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            self._send_static("index.html")
            return

        parts = _api_parts(path)
        try:
            if (
                len(parts) == 4
                and parts[0] == "session"
                and parts[2] == "snapshot"
                and parts[3] == "dev"
            ):
                if not _is_loopback_address(self.client_address[0]):
                    self._send_json(
                        {"error": "dev snapshot requires loopback client"},
                        HTTPStatus.FORBIDDEN,
                    )
                    return
                self._send_json(self.server.store.snapshot(parts[1], include_dev=True))
                return
            if len(parts) == 3 and parts[0] == "session" and parts[2] == "snapshot":
                self._send_json(self.server.store.snapshot(parts[1]))
                return
            if len(parts) == 3 and parts[0] == "session" and parts[2] == "transcript":
                self._send_json(self.server.store.transcript(parts[1]))
                return
        except SessionNotFound:
            self._send_json({"error": "session not found"}, HTTPStatus.NOT_FOUND)
            return

        if path.startswith("/static/"):
            self._send_static(path.removeprefix("/static/"))
            return

        self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        parts = _api_parts(path)

        try:
            if parts == ("session",):
                session = self.server.store.create()
                self._send_json(session.snapshot(), HTTPStatus.CREATED)
                return

            if len(parts) == 3 and parts[0] == "session" and parts[2] == "command":
                body = self._read_json()
                command = str(body.get("command", ""))
                response = self.server.store.command(parts[1], command)
                self._send_json(
                    {
                        "session_id": response.session_id,
                        "messages": list(response.messages),
                        "snapshot": response.snapshot,
                    }
                )
                return

            if len(parts) == 3 and parts[0] == "session" and parts[2] == "save":
                self._read_json(required=False)
                self._send_json(self.server.store.save(parts[1]))
                return

            if len(parts) == 3 and parts[0] == "session" and parts[2] == "load":
                body = self._read_json()
                text = body.get("save")
                if text is None:
                    raise ValueError("load requires save text")
                self._send_json(
                    self.server.store.load(
                        parts[1],
                        text=str(text),
                    )
                )
                return
        except SessionNotFound:
            self._send_json({"error": "session not found"}, HTTPStatus.NOT_FOUND)
            return
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        except OSError as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args: Any) -> None:
        if os.getenv("CUSTODIAN_WEB_LOG", "").strip().lower() in {"1", "true", "yes", "on"}:
            super().log_message(format, *args)

    def _read_json(self, *, required: bool = True) -> dict:
        length = int(self.headers.get("content-length", "0"))
        if length <= 0:
            if required:
                raise ValueError("request body required")
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("JSON object required")
        return data

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(body)))
        self.send_header("cache-control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_static(self, relative_path: str) -> None:
        path = (STATIC_ROOT / unquote(relative_path)).resolve()
        try:
            path.relative_to(STATIC_ROOT.resolve())
        except ValueError:
            self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return

        if not path.is_file():
            self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return

        body = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("content-type", content_type)
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def make_server(
    host: str = "127.0.0.1",
    port: int = 8765,
    *,
    store: SessionStore | None = None,
) -> CustodianHttpServer:
    return CustodianHttpServer((host, port), CustodianRequestHandler, store)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the Custodian browser session shell.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="force deterministic arka interpretation for this server process",
    )
    args = parser.parse_args(argv)

    if args.no_ai:
        os.environ["CUSTODIAN_AI"] = "off"

    server = make_server(args.host, args.port)
    host, port = server.server_address
    print(f"Custodian browser shell listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        server.server_close()


def _api_parts(path: str) -> tuple[str, ...]:
    if not path.startswith("/api/"):
        return ()
    return tuple(part for part in path.removeprefix("/api/").split("/") if part)


def _is_loopback_address(host: str) -> bool:
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return host == "localhost"


if __name__ == "__main__":
    main()
