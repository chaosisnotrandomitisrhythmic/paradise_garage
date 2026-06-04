#!/usr/bin/env bash
# Build the Spotify process-tap helper as a .app bundle.
#
# Process taps are gated by the TCC "Audio Recording" permission
# (kTCCServiceAudioCapture). macOS only shows the consent prompt for a real
# LaunchServices app in a GUI session, so we ship a minimal .app:
#
#   SpotifyTap.app/Contents/MacOS/spotify-tap   (the recorder)
#   SpotifyTap.app/Contents/Info.plist          (NSAudioCaptureUsageDescription + stable bundle id)
#
# Grant it once with:   open SpotifyTap.app --args --request-permission
#
# NOTE: ad-hoc signing changes the cdhash on every rebuild, invalidating the TCC
# grant — re-approve under System Settings → Privacy & Security → Audio Recording
# after rebuilding (or sign with a stable identity).
set -euo pipefail
cd "$(dirname "$0")"

APP="SpotifyTap.app"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS"
cp Info.plist "$APP/Contents/Info.plist"

swiftc -O \
    -framework CoreAudio -framework AudioToolbox -framework AppKit \
    -Xlinker -sectcreate -Xlinker __TEXT -Xlinker __info_plist -Xlinker Info.plist \
    -o "$APP/Contents/MacOS/spotify-tap" spotify-tap.swift

codesign --force --sign - \
    --entitlements spotify-tap.entitlements \
    --options runtime \
    "$APP"

echo "built + signed: $(pwd)/$APP"
codesign -d --entitlements - "$APP" 2>/dev/null | grep -i audio-input && echo "entitlement ✓" || true
