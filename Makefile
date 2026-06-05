.PHONY: install install-dev build clean screenshot

install:
	python3 -m pip install -r requirements.txt

install-dev:
	python3 -m pip install -e ".[test,build]"

build:
	rm -rf build dist
	python3 tools/sync_version.py
	python3 -m PyInstaller finder_sight.spec

clean:
	rm -rf build dist
	rm -rf __pycache__

screenshot:
	pytest tools/capture_screenshots.py
