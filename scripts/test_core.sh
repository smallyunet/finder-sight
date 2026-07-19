#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TEST_BIN="$(mktemp -d)/finder-sight-core-tests"
cd "$PROJECT_ROOT"
swiftc \
    -swift-version 5 \
    -framework AppKit \
    -framework ImageIO \
    -o "$TEST_BIN" \
    Sources/FinderSight/Models.swift \
    Sources/FinderSight/PerceptualHash.swift \
    Sources/FinderSight/ImageIndex.swift \
    Tests/CoreSmokeTests.swift
"$TEST_BIN"
