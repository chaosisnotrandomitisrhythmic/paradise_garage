#!/usr/bin/env bash
# Pull FLAC library from the other machine (Air <-> Mini)
# Usage: ./sync-from-remote.sh [user@host]
set -euo pipefail

AIR="chaosisnotrandomitisrythmic@Andreass-MacBook-Air.local"
MINI="andreasdaiminger@Andreass-Mac-mini.local"

self="$(hostname)"
case "$self" in
  Andreass-MacBook-Air*) default_peer="$MINI" ;;
  Andreass-Mac-mini*)    default_peer="$AIR"  ;;
  *) echo "Unknown host '$self' — pass peer explicitly: ./sync-from-remote.sh user@host" >&2; exit 1 ;;
esac

REMOTE="${1:-$default_peer}"
SRC="$REMOTE:Music/Library/flac/"
DST="$HOME/Music/Library/flac/"

mkdir -p "$DST"
rsync -avh --progress "$SRC" "$DST"

echo "--- Pulled tracks from $REMOTE ---"
