#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP_DIR="$PROJECT_ROOT/dist/Finder Sight.app"
DMG_PATH="$PROJECT_ROOT/dist/FinderSight-macOS.dmg"
STAGING="$(mktemp -d)"
trap 'rm -rf "$STAGING"' EXIT

cp -R "$APP_DIR" "$STAGING/"
ln -s /Applications "$STAGING/Applications"
rm -f "$DMG_PATH"
hdiutil create -volname "Finder Sight" -srcfolder "$STAGING" -ov -format UDZO "$DMG_PATH"
echo "$DMG_PATH"
