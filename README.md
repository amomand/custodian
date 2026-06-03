# Custodian

A narrow terminal prototype for a sci-fi horror game about the cost of delegation.

This first slice uses one ship system: reactor coolant. The player can let `arka`
summarise and adjust the loop, or they can spend turns reading raw telemetry and
using manual controls. Manual familiarity is hidden and only improves through
manual action.

## Run

```bash
python3 -m pip install -e .
custodian
```

Without installing:

```bash
PYTHONPATH=src python3 -m custodian
```

## Test

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

## Project Notes

The original idea note is copied into [docs/original-idea.md](docs/original-idea.md).
The current MVP design is in [design.md](design.md).
