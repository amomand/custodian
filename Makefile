# Custodian convenience targets.
# These wrap the canonical commands documented in docs/launch-modes.md so
# nobody has to hand-assemble PYTHONPATH=... . The raw commands always work too.

.PHONY: play play-det web web-det app app-det app-package playtest test check debug help

help:
	@echo "Custodian make targets (see docs/launch-modes.md):"
	@echo "  make play       Terminal, model on"
	@echo "  make play-det   Terminal, deterministic (no key)"
	@echo "  make web        Web operating desk, model on"
	@echo "  make web-det    Web operating desk, deterministic"
	@echo "  make app        Desktop app window, model on (needs pywebview)"
	@echo "  make app-det    Desktop app window, deterministic"
	@echo "  make app-package  Build dist/Custodian.app (needs pyinstaller)"
	@echo "  make playtest   Playtest runner, all scenarios"
	@echo "  make test       Unit tests"
	@echo "  make check      Tests + compile + smoke checks (mirrors CI)"
	@echo "  make debug      Terminal with CUSTODIAN_DEBUG=1"

play:
	python3 main.py

play-det:
	CUSTODIAN_AI=off python3 main.py

web:
	PYTHONPATH=src python3 -m custodian.web_server

web-det:
	PYTHONPATH=src python3 -m custodian.web_server --no-ai

app:
	PYTHONPATH=src python3 -m custodian.app_shell

app-det:
	PYTHONPATH=src python3 -m custodian.app_shell --no-ai

app-package:
	python3 -m PyInstaller --noconfirm packaging/custodian.spec
	@test -n "$$(find dist/Custodian.app -path '*custodian/web_static/index.html' -print -quit)" \
		|| { echo "Custodian.app is missing the operating desk assets"; exit 1; }
	@echo "Built dist/Custodian.app"

playtest:
	python3 tools/playtest_runner.py --all --summary-only

test:
	PYTHONPATH=src python3 -m unittest discover -s tests

check: test
	python3 -m compileall src tests tools packaging main.py
	printf 'can you handle it?\nquit\n' | CUSTODIAN_AI=off python3 main.py
	python3 tools/playtest_runner.py --all --summary-only

debug:
	CUSTODIAN_DEBUG=1 python3 main.py
