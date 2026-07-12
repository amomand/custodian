# Packaging Custodian as a macOS app

How to build the double-clickable `dist/Custodian.app` from source. Like
[launch-modes.md](launch-modes.md), this is plain developer documentation.
It assumes nothing beyond a checkout and Python 3.11+, so it still works
after a few weeks away.

## What the app is

`Custodian.app` is the desktop app shell (`custodian.app_shell`) frozen with
PyInstaller. Double-clicking it opens the web operating desk in a native
window: the bundle starts the same loopback HTTP server as `custodian-web`
on an OS-assigned port, and the window is a thin client on it. No ship truth
lives in the shell; play is identical to the browser desk.

The build is local-only by design: ad-hoc signed, not notarised, no
auto-updates, not for the App Store.

## Build

```bash
python3 -m venv .venv                      # once
source .venv/bin/activate
python3 -m pip install -e '.[package]'     # pywebview + pyinstaller
make app-package
```

The make target builds with `packaging/custodian.spec` and then fails
loudly if the operating desk assets did not make it into the bundle. Output
lands in `dist/Custodian.app` (gitignored, roughly 35 MB). Rebuilds are
incremental via `build/`; delete `build/` and `dist/` for a clean one.

Raw command, if make is unavailable:

```bash
python3 -m PyInstaller --noconfirm packaging/custodian.spec
```

## Run

Double-click `dist/Custodian.app` in Finder, or:

```bash
open dist/Custodian.app
# or, with visible logs and flags:
dist/Custodian.app/Contents/MacOS/custodian-app --no-ai
```

First launch from Finder may need right-click then Open, because the bundle
is only ad-hoc signed (PyInstaller signs it automatically; there is no
developer certificate involved).

A fresh deterministic run needs no API key, same as every other mode. For
model-backed arka, put your `.env` in
`~/Library/Application Support/Custodian/.env`; the packaged app has no repo
checkout to read one from. Real environment variables still win over the
file. See [launch-modes.md](launch-modes.md) for the variables themselves.

## How the pieces fit

- `packaging/app_entry.py` — tiny script PyInstaller anchors the build on;
  it just calls `custodian.app_shell.main()`.
- `packaging/custodian.spec` — the build description. It resolves every
  path from `SPECPATH` (the spec's own directory), so the build works no
  matter where pyinstaller is invoked from. `web_static` is bundled to
  `custodian/web_static` so `web_server.STATIC_ROOT` resolves the same
  frozen as from source.
- The app shell asks for port 0, so the OS assigns a free loopback port and
  the app never conflicts with a manually launched `custodian-web` on 8765.

## Troubleshooting

- **App opens then immediately closes**: run the binary directly from a
  terminal (`dist/Custodian.app/Contents/MacOS/custodian-app`) to see the
  traceback.
- **`ModuleNotFoundError` in the frozen app**: check
  `build/custodian/warn-custodian.txt` for `missing module named ...` lines;
  a module PyInstaller could not trace needs adding to `hiddenimports` in
  the spec.
- **Blank window or 404s**: the asset check in `make app-package` should
  have caught this; confirm `custodian/web_static/index.html` exists inside
  the bundle (`find dist/Custodian.app -name index.html`).
- **arka not conversational**: same three requirements as every mode (see
  launch-modes.md), except the `.env` location above.
