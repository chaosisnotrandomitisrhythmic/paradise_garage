---
layout: default
title: Recording
---

# Recording — `pg record`

One command turns a Spotify playlist into named, tagged FLACs in the library —
replacing the manual BlackHole → Ableton split/export/rename dance.

```bash
cd ~/dev/personal/paradise_garage
uv run pg record https://open.spotify.com/playlist/XXXXXXXX
```

## What it does

1. **Reads the playlist** via the Spotify Web API (ordered tracklist: artist, title, duration, URI).
2. **Captures BlackHole 2ch** continuously with ffmpeg → one 44.1 kHz / 16-bit master WAV.
3. **Drives the Spotify desktop app** via AppleScript, playing the playlist **track-by-track**
   with a forced ~1 s silent gap between tracks — so every cut point lands in clean silence.
4. **Logs exact boundaries** against the capture clock and **splits** the master into per-track
   FLACs, conservatively trimming the injected silence (−60 dB threshold).
5. **Names** each file `Artist - Title.flac` (auto-applying the dash-in-title → parens rule).
6. **Ingests** each via the existing `pg ingest` (librosa BPM/key/energy + Vorbis tags + catalog).

Flags: `--keep-master` (retain the full WAV), `--no-trim` (disable silence trimming).

## Preflight (one-time + per-run)

- **Output** routes through BlackHole 2ch (a Multi-Output Device lets you monitor while capturing).
- **Spotify Settings → Playback:** Crossfade **OFF**, Normalize **OFF**, Autoplay **OFF**.
- **Spotify Premium** — free-tier ads get injected between tracks and pollute captures.
- **Volume at 100 %** — the level is captured as-is (same principle as "render at unity, not −6 dB").
- It runs in **real time**: a 60-minute playlist takes ~60 minutes — but fully unattended. Ctrl-C aborts cleanly.

## Notes & limits

- Source is lossy (Spotify ≈ 320 kbps Ogg); the FLAC is a lossless container of lossy audio — fine for DJing, not archival mastering.
- Spot-check durations against the playlist if any track flags `⚠ short?` (truncation guard).
- Spotify auth caches a token at `~/.cache/paradise_garage/spotify-token.json` (browser consent once).

## Roadmap

- **Phase 2 — Traktor:** write `collection.nml` entries (tags + beatgrid) and grid-snapped hot cues.
- **Phase 3 — Ableton:** generate a saved `.als` with locators at every song boundary.
