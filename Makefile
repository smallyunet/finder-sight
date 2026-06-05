.PHONY: install install-dev build clean screenshot

PYTHON := $(shell if [ -x .venv/bin/python ]; then echo .venv/bin/python; else echo python3; fi)

install:
	$(PYTHON) -m pip install -r requirements.txt

install-dev:
	$(PYTHON) -m pip install -e ".[test,build]"

build:
	rm -rf build dist
	$(PYTHON) tools/sync_version.py
	$(PYTHON) -m PyInstaller finder_sight.spec

clean:
	rm -rf build dist
	rm -rf __pycache__

screenshot:
	pytest tools/capture_screenshots.py
