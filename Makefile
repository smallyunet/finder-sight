.PHONY: install build clean

install:
	pip install -r requirements.txt

build:
	pyinstaller finder_sight.spec

clean:
	rm -rf build dist
	rm -rf __pycache__
