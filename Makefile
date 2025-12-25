.PHONY: install build clean screenshot

install:
	pip install -r requirements.txt

build:
	pyinstaller finder_sight.spec

clean:
	rm -rf build dist
	rm -rf __pycache__

screenshot:
	pytest tools/capture_screenshots.py
