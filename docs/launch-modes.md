# Launching Custodian

This is the single source of truth for how to run Custodian in each mode. It is
ordinary developer documentation: plain commands, no in-world voice. The README
sells the fiction; this file tells you exactly what to type.

Requirements: Python 3.11+. No API key is needed to play.

## The one thing that trips everyone up

Custodian runs the same either way, but **arka only talks back conversationally
when all three of these are true:**

1. `custodian_ai` is on — you did **not** pass `--no-ai` or set `CUSTODIAN_AI=off`.
2. `OPENAI_API_KEY` is set — in your environment or in a repo-root `.env`.
3. The `openai` package is installed — `python3 -m pip install -r requirements.txt`.

Miss any one of them and arka silently falls back to its deterministic in-world
line. That fallback looks identical to running with `--no-ai`, so it is easy to
think the model is on when it is not. To see exactly which requirement is
missing, run with `CUSTODIAN_DEBUG=1` and read the reason on stderr.

The deterministic fallback is a real, supported run mode — not a degraded one.
The ship behaves the same; only arka's free-text replies change.

## Modes

### Terminal, model on

```bash
python3 main.py
```

`main.py` puts `src/` on the path for you. Needs the three prerequisites above
for conversational arka; otherwise it runs deterministically.

### Terminal, deterministic (no key)

```bash
CUSTODIAN_AI=off python3 main.py
```

This is the default behaviour when no key or SDK is present, made explicit. This
is the command CI uses for its terminal smoke test.

### Web operating desk, model on

```bash
PYTHONPATH=src python3 -m custodian.web_server
```

Then open <http://127.0.0.1:8765>. Needs `OPENAI_API_KEY` and `openai`
installed for conversational arka. Use `--host`/`--port` to change the bind
address.

### Web operating desk, deterministic

```bash
PYTHONPATH=src python3 -m custodian.web_server --no-ai
```

`--no-ai` forces deterministic arka for that server process.

### Desktop app window (macOS)

```bash
python3 -m pip install pywebview   # one-off, or: pip install -e '.[app]'
PYTHONPATH=src python3 -m custodian.app_shell
```

Opens the web operating desk in a native window, no browser and no manual
server start. The shell starts the same loopback HTTP server as
`custodian-web` on an OS-assigned port, so it never clashes with a manually
launched web desk. Pass `--no-ai` for a deterministic run, same as the other
modes.

The window is only a wrapper: play, saves, and arka behaviour are identical
to the browser desk. Saves still round-trip through the save buffer panel.

For model-backed arka, the app reads a repo-root `.env` when running from
source, and also `~/Library/Application Support/Custodian/.env` so a future
packaged build works without a repo checkout. Real environment variables
always win, then the repo `.env`, then the app-support copy.

Packaging this into a double-clickable `.app` is a follow-up
(issue #40); this mode is the source-run foundation for it.

### Playtest runner

```bash
python3 tools/playtest_runner.py --all --summary-only
python3 tools/playtest_runner.py --scenario <name>
python3 tools/playtest_runner.py --commands-file path/to/route.txt
```

Deterministic transcript routes. No key required.

### Debugging the fallback

```bash
CUSTODIAN_DEBUG=1 python3 main.py
```

Prints to stderr why the model path fell back (`CUSTODIAN_AI` disabled,
`OPENAI_API_KEY` missing, OpenAI SDK missing, or a failed model call).

## Make targets

A small `Makefile` wraps the commands above so nobody hand-assembles
`PYTHONPATH=...`:

```bash
make play        # terminal, model on
make play-det    # terminal, deterministic
make web         # web operating desk, model on
make web-det     # web operating desk, deterministic
make app         # desktop app window, model on (needs pywebview)
make app-det     # desktop app window, deterministic
make playtest    # playtest runner, all scenarios
make test        # unit tests
make check       # tests + compile + smoke checks (mirrors CI)
make debug       # terminal with CUSTODIAN_DEBUG=1
```

The make targets are a convenience only; the raw commands above always work.

## Enabling conversational arka

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Put your key in a repo-root `.env` (ignored by git):

```bash
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-5.4-mini
OPENAI_REASONING_EFFORT=none
CUSTODIAN_AI=on
CUSTODIAN_CLEAR=on
```

## Environment variables

| Variable | Effect |
| --- | --- |
| `OPENAI_API_KEY` | Enables model-backed arka interpretation. |
| `OPENAI_MODEL` | Model name. Default `gpt-5.4-mini`. |
| `OPENAI_REASONING_EFFORT` | Reasoning effort. Default `none`. |
| `CUSTODIAN_AI=off` | Force deterministic fallback. |
| `CUSTODIAN_DEBUG=1` | Print AI fallback diagnostics to stderr. |
| `CUSTODIAN_CLEAR=off` | Disable interactive launch and event screen clears. |
| `CUSTODIAN_BOOT=off` | Skip the interactive A.R.K.A boot screen. |
| `CUSTODIAN_REFRESH=off` | Append every turn instead of refreshing the screen. |
| `CUSTODIAN_COMPLETE=off` | Disable interactive tab completion. |
| `CUSTODIAN_WEB_LOG=1` | Print local browser shell HTTP request logs. |

## Development checks

These mirror what CI runs (`.github/workflows/ci.yml`), and none of them need an
API key:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
python3 -m compileall src tests tools main.py
printf 'can you handle it?\nquit\n' | CUSTODIAN_AI=off python3 main.py
python3 tools/playtest_runner.py --all --summary-only
```

Developer-only terminal diagnostics use a colon prefix: `:debug`, `:metrics`,
`:help`.

## Troubleshooting

If arka keeps interpreting everything as interest in the coolant loop, the model
path is not active. Work through the three requirements at the top of this file:

1. You are not passing `--no-ai` and `CUSTODIAN_AI` is not `off`.
2. `.env` exists in the repo root and contains `OPENAI_API_KEY` (or the variable
   is exported), and the virtual environment is active if you are using one.
3. `python3 -m pip install -r requirements.txt` has been run.

Then run `CUSTODIAN_DEBUG=1 python3 main.py` for the specific fallback reason.
