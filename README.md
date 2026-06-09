# Custodian

You are the only waking custodian aboard the colony ship *Calyx*.

The reactor is warm. The sleepers are not. Thousands of them, stacked in the
cold, trusting you to get them home.

You do not have to do this alone. arka can hold the coolant loop, watch the
cryostasis banks, plot the route. It is calm, it is quick, and it is better
company than the silence. It is usually right.

It will tell you the sleepers are quiet. It will tell you the ship is fine.

For a while, the raw feed will agree.

---

Custodian is a terminal-and-browser horror prototype about the cost of handing
the work to something that is better at it than you are. The more you let arka
run, the less you practise — and arka's account of the ship slowly stops
matching what the instruments say. By the time the gap matters, the manual skill
you need is the skill you chose not to build.

The ship is deterministic and honest. arka is the only thing aboard that can
soften a fact.

## Run it

Needs Python 3.11+. No key required.

```bash
python3 main.py
```

That plays the full slice. arka answers in fixed in-world lines unless you wire
up the model.

For conversational arka, the browser operating desk, the playtest runner, and
the one prerequisite everyone trips over, see
**[docs/launch-modes.md](docs/launch-modes.md)** — the single source of launch
truth. There is a `Makefile` too: run `make help`.

## Read more

- [`docs/launch-modes.md`](docs/launch-modes.md) - how to run every mode
- [`docs/lore/arka.md`](docs/lore/arka.md) - who arka is, and how it speaks
- [`design.md`](design.md) - the thesis, the loop, the systems
- [`docs/project-reference.md`](docs/project-reference.md) - features, layout, config, and the full doc index

The work is logged in GitHub issues, not a roadmap file.
