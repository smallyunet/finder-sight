#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TEST_BIN="$(mktemp -d)/finder-sight-core-tests"
BRIDGE_OBJECT="$(mktemp -d)/VisionBridge.o"
MODULE_CACHE="$(mktemp -d)"
export CLANG_MODULE_CACHE_PATH="$MODULE_CACHE"
export SWIFT_MODULECACHE_PATH="$MODULE_CACHE"
cd "$PROJECT_ROOT"
clang \
    -fobjc-arc \
    -I Sources/VisionBridge/include \
    -c Sources/VisionBridge/VisionBridge.m \
    -o "$BRIDGE_OBJECT"
swiftc \
    -swift-version 5 \
    -framework AppKit \
    -framework ImageIO \
    -framework Vision \
    -I Sources/VisionBridge/include \
    "$BRIDGE_OBJECT" \
    -o "$TEST_BIN" \
    Sources/FinderSight/Models.swift \
    Sources/FinderSight/PerceptualHash.swift \
    Sources/FinderSight/VisualFeature.swift \
    Sources/FinderSight/ImageIndex.swift \
    Tests/CoreSmokeTests.swift
"$TEST_BIN"
