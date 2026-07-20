.PHONY: build dmg test clean run

VERSION ?= $(shell tr -d '[:space:]' < VERSION)

build:
	bash scripts/build_app.sh $(VERSION)

dmg: build
	bash scripts/create_dmg.sh

test:
	bash scripts/test_core.sh

run:
	swift run FinderSight

clean:
	swift package clean
	rm -rf dist
