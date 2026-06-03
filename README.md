# Custodian

A narrow terminal prototype for a sci-fi horror game about the cost of delegation.

This first slice uses one ship system: reactor coolant. The player can let `arka`
summarise and adjust the loop, or they can spend turns reading raw telemetry and
using manual controls. Manual familiarity is hidden and only improves through
manual action.

## Run

Fast local launch from the repo:

```bash
python3 main.py
```

The deterministic fallback works without an API key. For the model-backed arka
interpreter, set up a virtual environment and `.env`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
cp .env.example .env
```

Then add `OPENAI_API_KEY` to `.env` and launch:

```bash
python3 main.py
```

The package entrypoint still works after an editable install:

```bash
python3 -m pip install -e .
custodian
```

## Test

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

## Project Notes

The original idea note is copied into [docs/original-idea.md](docs/original-idea.md).
The current MVP design is in [design.md](design.md).
arka's editable character brief is in [docs/lore/arka.md](docs/lore/arka.md).
The AI boundary is documented in
[docs/architecture/ai-interpreter.md](docs/architecture/ai-interpreter.md).
