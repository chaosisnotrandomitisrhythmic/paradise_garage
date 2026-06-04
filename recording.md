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

## How it captures (per-process tap, not loopback)

Capture uses a **Core Audio process tap** (`native/SpotifyTap.app`) that records
**only Spotify's audio stream** — so notifications, Slack, browser tabs, and other
apps **cannot bleed in**, and there's **no output rerouting or muting**: Spotify
plays through your speakers normally while we tap it. (This replaced an earlier
system-wide BlackHole loopback, which recorded the whole mix.)

Pipeline:

1. **Reads the playlist** via the Spotify Web API (ordered tracklist).
2. **Starts the tap** on Spotify only.
3. **Plays the playlist continuously** via AppleScript; detects each track boundary
   from current-track-id transitions, position-corrected for sample accuracy.
4. **Splits** the recording at those boundaries → per-track FLAC.
5. **Names** each `Artist - Title.flac` (auto-applying the dash-in-title → parens rule).
6. **Ingests** via `pg ingest` (librosa BPM/key/energy + Vorbis tags + catalog),
   tagging each track with its source **playlist** (multi-value; a track accumulates
   every playlist it came from — virtual crates, no folder duplication).

Flags: `--limit N` (record only the first N — handy for testing), `--keep-master`
(retain the full WAV), `--trim` (silence-trim edges; off by default).

## One-time setup

1. **Build the tap helper** (compiles + signs the .app):
   ```bash
   bash native/build.sh
   ```
2. **Grant the audio-recording permission** (macOS gates process taps behind
   `kTCCServiceAudioCapture`). This must be triggered from the GUI:
   ```bash
   open native/SpotifyTap.app --args --request-permission
   ```
   Approve the **"Audio Recording"** prompt (or System Settings → Privacy & Security
   → Audio Recording → enable `SpotifyTap`). The grant is keyed to the signed binary
   — **rebuilding the helper invalidates it**, so re-approve after any `build.sh`.

## Spotify settings for optimal capture (one-time)

Spotify's **defaults are wrong** for recording (Automix, Normalize, and Autoplay
are all ON by default). In **Settings → "Show advanced settings"**:

| Setting | Value | Why |
|---|---|---|
| Audio quality → Streaming | **Very High** (320 kbps) or **Lossless** | best source fidelity (Premium) |
| **Normalize volume** | **OFF** | leveling would flatten inter-track loudness (kills the RMS energy class) and double up with Traktor's auto-gain |
| **Automix** | **OFF** | DJ-style blending between tracks — destroys boundaries |
| **Crossfade songs** | **OFF** | overlapping track audio = bleed |
| **Autoplay** | **OFF** | so capture stops cleanly at the playlist's end |
| Gapless | may stay **ON** | only removes silence; does not blend audio |

Per run, `pg record` automatically forces shuffle/repeat off and **in-app volume to 100%**
(verified: the tap captures *post* Spotify's volume — 50% → ~18 dB quieter — so 100% is required for full-scale capture). It runs in **real time** (a 60-min playlist ≈ 60 min), unattended; Ctrl-C aborts cleanly. Premium recommended (free-tier ads get recorded between tracks).

## Loudness — captured native, leveled at playback

Tracks are recorded at their **native mastered loudness** (never normalized into the
file). Ingest measures **integrated LUFS + true peak** (ffmpeg `ebur128`) and writes
**ReplayGain** tags (`replaygain_track_gain`, `replaygain_track_peak`,
`replaygain_reference_loudness` at −18 LUFS) plus a raw `lufs` tag. That gives:
- the RMS-based **energy** classifier real inter-track differences to work with,
- **play-time leveling** for loudness-aware players via ReplayGain,
- Traktor/rekordbox can still apply their own analysis auto-gain.

`lufs` and `true_peak_dbtp` are also stored in the catalog.

## Notes & limits

- Source is lossy (Spotify ≈ 320 kbps Ogg); the FLAC is a lossless container of lossy audio — fine for DJing, not archival mastering.
- The tap records at Spotify's native rate (48 kHz Float32); the split step resamples to 44.1 kHz / 16-bit to match the library.
- Spotify auth caches a token at `~/.cache/paradise_garage/spotify-token.json` (browser consent once).

## Roadmap

- **Phase 2 — Traktor:** write `collection.nml` entries (tags + beatgrid) and grid-snapped hot cues.
- **Phase 3 — Ableton:** generate a saved `.als` with locators at every song boundary.
