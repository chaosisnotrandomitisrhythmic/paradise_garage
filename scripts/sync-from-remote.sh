#!/usr/bin/env bash
# Pull library from Mac Mini (run from MacBook Air)
# Usage: ./sync-from-remote.sh [mini-hostname-or-ip]

REMOTE="${1:-andreasdaiminger@Andreass-Mac-mini.local}"
SRC="$REMOTE:Music/Library/flac/"
DST="$HOME/Music/Library/flac/"

mkdir -p "$DST"

rsync -avh --progress "$SRC" "$DST"

echo "--- Pulled tracks from $REMOTE ---"
