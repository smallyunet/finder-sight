.PHONY: install build clean screenshot

install:
	pip install -r requirements.txt

build:
	python3 tools/sync_version.py
	pyinstaller finder_sight.spec

clean:
	rm -rf build dist
	rm -rf __pycache__

screenshot:
	pytest tools/capture_screenshots.py
