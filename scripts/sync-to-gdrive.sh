#!/usr/bin/env bash
# Sync local FLAC library to Google Drive backup
# Run manually or via launchd/cron

SRC="$HOME/Music/Library/flac/"
DST="$HOME/gdrive/Music/Library/flac/"

mkdir -p "$DST"

rsync -avh --progress --delete "$SRC" "$DST"

echo "--- Synced $(find "$SRC" -name '*.flac' | wc -l | tr -d ' ') tracks to gdrive ---"
