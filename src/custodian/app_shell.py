"""Desktop app shell: the web operating desk in a native macOS window.

This wraps the existing HTTP server and browser desk rather than replacing
them. The window is just another thin client: it talks to the same loopback
server the browser modes use, so no ship truth moves into the shell.
"""

from __future__ import annotations

import argparse
import os
import threading
from pathlib import Path

from custodian.config import load_app_env
from custodian.web_server import STATIC_ROOT, make_server


WINDOW_TITLE = "Custodian"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 860

PYWEBVIEW_INSTALL_HINT = (
    "custodian-app needs pywebview for the desktop window.\n"
    "Install it with one of:\n"
    "  python3 -m pip install pywebview\n"
    "  python3 -m pip install -e '.[app]'\n"
    "Terminal and browser modes work without it; see docs/launch-modes.md."
)


class MissingWebAssets(RuntimeError):
    pass


REQUIRED_WEB_ASSETS = ("index.html", "app.js", "styles.css")


def find_web_assets() -> Path:
    """Return the operating desk asset directory, or raise if incomplete.

    Kept as a separate step so a frozen/bundled build that mislays any of
    web_static fails loudly at launch instead of serving a broken desk.
    """
    missing = [
        name for name in REQUIRED_WEB_ASSETS if not (STATIC_ROOT / name).is_file()
    ]
    if missing:
        raise MissingWebAssets(
            f"operating desk assets missing from {STATIC_ROOT}: {', '.join(missing)}"
        )
    return STATIC_ROOT


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Run the Custodian operating desk in a desktop window."
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="force deterministic arka interpretation for this app process",
    )
    args = parser.parse_args(argv)

    if args.no_ai:
        os.environ["CUSTODIAN_AI"] = "off"

    try:
        import webview
    except ImportError as exc:
        # Only translate "pywebview is not installed" into the install hint.
        # A broken pywebview dependency should surface its real traceback.
        if exc.name == "webview":
            raise SystemExit(PYWEBVIEW_INSTALL_HINT) from exc
        raise

    find_web_assets()
    load_app_env()

    # Port 0 lets the OS pick a free loopback port, so the app never fights
    # a manually launched custodian-web over 8765.
    server = make_server("127.0.0.1", 0)
    host, port = server.server_address
    server_thread = threading.Thread(
        target=server.serve_forever, name="custodian-web", daemon=True
    )
    server_thread.start()
    # flush so the line appears even when stdout is a pipe or log file
    print(f"Custodian app shell serving on http://{host}:{port}", flush=True)

    if hasattr(webview, "settings"):
        # Lets the desk's transcript download link work inside the window.
        webview.settings["ALLOW_DOWNLOADS"] = True

    try:
        webview.create_window(
            WINDOW_TITLE,
            f"http://{host}:{port}/",
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
        )
        webview.start()
    finally:
        server.shutdown()
        server_thread.join(timeout=5)
        server.server_close()


if __name__ == "__main__":
    main()
