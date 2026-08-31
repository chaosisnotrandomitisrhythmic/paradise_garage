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

Flags: `--limit N` (record only the first N — handy for testing), `--start N`
(begin at playlist track N), `--keep-master` (retain the full WAV), `--trim`
(silence-trim edges; off by default).

### Resume / record only what's missing

```bash
pg record <playlist-url> --skip-existing        # record only tracks not already in the library
pg record <playlist-url> --skip-existing --dry-run   # just show what's missing
```

Scans each playlist track against the library — a track counts as *present* only
if a file matches (fuzzy: first-artist + punctuation-normalized title, so
`Lil' Louis, The World` matches `Lil' Louis` and `X - Mix` matches `X (Mix)`)
**and** its duration matches the playlist (so truncated/silent partials are treated
as missing and re-recorded). Then it records **only the missing tracks, one at a
time, ingesting each as it finishes** — so it's **safe to interrupt and re-run**:
the next run automatically resumes with just what's still missing.

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

## Algorithmic playlists — `pg harvest`

Radio and personal-Mix ids (`37i9dQZF1E4…`) are first-party-only: the Web API
404s them for third-party apps, so `pg record` can't resolve them. `pg harvest`
drives a real Chrome over the DevTools Protocol and dispatches genuine
`Input.dispatchMouseEvent` wheel events — the tracklist is a virtualized list
that ignores programmatic `scrollTop`, but not a real wheel.

```bash
pg harvest "https://open.spotify.com/playlist/37i9dQZF1E4vq1cso24MIt" --remote
pg record harvest:officer-john-radio --skip-existing
```

Only track ids come from the DOM, keyed by `aria-rowindex` so recycled rows land
in playlist order. Artist/title/`duration_ms` come from `/v1/tracks`, which is
not restricted — the restriction is on reading the playlist, not its tracks.

- **`--remote`** attaches to a dedicated "CDP Chrome" on port 9223 (`fastcdp-setup`
  builds the launcher). Its own profile, no approval prompt — this is the mini's
  path. Without it, your everyday Chrome is used, which needs *Allow remote
  debugging* at `chrome://inspect/#remote-debugging` **and a Chrome relaunch**,
  plus a per-connection approval click.
- **No Spotify login needed.** Verified signed-out: the page shows a login wall
  and still renders the full tracklist.
- **A short harvest is an error, not a warning.** If fewer ids come back than the
  page's own "N songs", nothing is written — a truncated list would silently
  become a truncated recording queue.
- **The snapshot is deliberately fixed.** Radio contents drift; you record the
  list as it was, not as it is tonight. Re-run `pg harvest` to refresh it.
- ⚠️ Loading the web player registers Chrome as a Spotify Connect device — the
  condition that wedges the AppleScript tap. Harvest as a discrete step and check
  Spotify desktop is on "This Computer" before recording.

The batch recorder accepts `PG_PLAYLIST_URL="harvest:<slug>"`.

## Traktor — `pg traktor` (grid-snapped cues)

**Required first step: import the track into Traktor and run _Analyze (Async)_
before `pg traktor`.** The grid is always Traktor's own — we never fabricate one.

```bash
pg traktor "~/Music/Library/flac/Artist - Title.flac" [...] [--dry-run]
```

Writes hot cues into Traktor's `collection.nml`:
- If Traktor has **already analyzed** the track, it reads that entry's `TEMPO BPM`
  + `AutoGrid` anchor and **snaps cues to Traktor's own grid** (most accurate).
- If the track **isn't analyzed in Traktor yet** (no `TEMPO` + `AutoGrid` anchor),
  it's **skipped** with `SKIP <file> — not analyzed in Traktor yet…`. Add it to
  Traktor, run Analyze (Async), then re-run. We no longer fabricate a beatgrid from
  librosa — its downbeat estimate landed ~1 beat off and snapped every cue wrong.

Cues come from librosa structural analysis — `IN` (bass entry), `BREAK` (deepest
dip), `OUT` (outro) — snapped to the nearest bar **of Traktor's grid**. They're
**rough auto-suggestions to fine-tune by ear**, not surgical.

Safety: **Traktor must be quit** (it rewrites the NML on exit — the command refuses
if it's running), the collection is **backed up** (`collection.nml.bak-<ts>`) before
writing, and the result is XML-validated. Relaunch Traktor to see the cues.

## Roadmap

- **Phase 3 — Ableton:** generate a saved `.als` with locators at every song boundary.
