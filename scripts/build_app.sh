#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="${1:-$(tr -d '[:space:]' < "$PROJECT_ROOT/VERSION")}"
CONFIGURATION="${CONFIGURATION:-release}"
APP_DIR="$PROJECT_ROOT/dist/Finder Sight.app"
CONTENTS="$APP_DIR/Contents"
BUILD_DIR="$PROJECT_ROOT/.build/app-bundle"
MODULE_CACHE="$BUILD_DIR/module-cache"

cd "$PROJECT_ROOT"
rm -rf "$PROJECT_ROOT/dist"
mkdir -p "$CONTENTS/MacOS" "$CONTENTS/Resources"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
mkdir -p "$MODULE_CACHE"
export CLANG_MODULE_CACHE_PATH="$MODULE_CACHE"
export SWIFT_MODULECACHE_PATH="$MODULE_CACHE"

# Compile directly so the build also works on machines with Command Line Tools
# only. SwiftPM remains the source of truth for CI tests and project metadata.
OPTIMIZATION="-O"
if [[ "$CONFIGURATION" == "debug" ]]; then OPTIMIZATION="-Onone"; fi
SDK_PATH="$(xcrun --sdk macosx --show-sdk-path)"
ARCHITECTURES="${ARCHS:-arm64 x86_64}"
BINARIES=()
for ARCH in $ARCHITECTURES; do
    ARCH_BINARY="$BUILD_DIR/FinderSight-$ARCH"
    BRIDGE_OBJECT="$BUILD_DIR/VisionBridge-$ARCH.o"
    clang \
        -fobjc-arc \
        -target "$ARCH-apple-macosx13.0" \
        -isysroot "$SDK_PATH" \
        -I Sources/VisionBridge/include \
        -c Sources/VisionBridge/VisionBridge.m \
        -o "$BRIDGE_OBJECT"
    swiftc \
        -parse-as-library \
        -swift-version 5 \
        "$OPTIMIZATION" \
        -target "$ARCH-apple-macosx13.0" \
        -sdk "$SDK_PATH" \
        -I Sources/VisionBridge/include \
        -framework SwiftUI \
        -framework AppKit \
        -framework ImageIO \
        -framework Vision \
        "$BRIDGE_OBJECT" \
        -o "$ARCH_BINARY" \
        Sources/FinderSight/*.swift
    BINARIES+=("$ARCH_BINARY")
done

if [[ "${#BINARIES[@]}" -eq 1 ]]; then
    cp "${BINARIES[0]}" "$CONTENTS/MacOS/Finder Sight"
else
    lipo -create "${BINARIES[@]}" -output "$CONTENTS/MacOS/Finder Sight"
fi
cp "$PROJECT_ROOT/icon.icns" "$CONTENTS/Resources/AppIcon.icns"

cat > "$CONTENTS/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key><string>en</string>
    <key>CFBundleDisplayName</key><string>Finder Sight</string>
    <key>CFBundleExecutable</key><string>Finder Sight</string>
    <key>CFBundleIconFile</key><string>AppIcon</string>
    <key>CFBundleIdentifier</key><string>com.smallyunet.finder-sight</string>
    <key>CFBundleInfoDictionaryVersion</key><string>6.0</string>
    <key>CFBundleName</key><string>Finder Sight</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>CFBundleShortVersionString</key><string>$VERSION</string>
    <key>CFBundleVersion</key><string>$VERSION</string>
    <key>LSMinimumSystemVersion</key><string>13.0</string>
    <key>NSHighResolutionCapable</key><true/>
    <key>NSHumanReadableCopyright</key><string>Copyright © 2026 smallyu</string>
</dict>
</plist>
PLIST

codesign --force --deep --sign - "$APP_DIR"
echo "$APP_DIR"
