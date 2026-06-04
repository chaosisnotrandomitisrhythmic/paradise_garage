"""Orchestrate: Spotify playlist -> per-process tap capture -> boundary log -> per-track FLACs.

Phase 1 of `pg record`. Captures only Spotify (no bleed, no rerouting, no muting),
splits the continuous recording at detected track boundaries, names the files, and
hands them to the existing ingest (librosa + tags + catalog).
"""

import time
from pathlib import Path

from . import capture, playback, split
from .spotify import get_playlist_tracks, parse_playlist_id

CAPTURE_DIR = Path.home() / ".cache" / "paradise_garage" / "captures"


def _preflight(name: str, n: int, total_sec: float):
    print(f"\n  Playlist: {name}  ({n} tracks, ~{total_sec / 60:.0f} min real-time)\n")
    print("  ONE-TIME Spotify setup (Settings → click 'Show advanced settings'):")
    print("    • Audio quality → Streaming: Very High (320kbps) or Lossless — needs Premium")
    print("    • Normalize volume: OFF   (else loudness/energy gets flattened; Traktor auto-gains anyway)")
    print("    • Automix: OFF            (DJ-style blending — ON by default!)")
    print("    • Crossfade songs: OFF    (tracks would bleed together)")
    print("    • Autoplay: OFF           (so playback stops at the playlist's end — ON by default!)")
    print("    • Gapless: may stay ON    (removes silence only, no audio bleed)")
    print("  Per run (handled automatically): shuffle/repeat off, in-app volume 100%.")
    print("  Capture is Spotify-only via the tap — no notification/other-app bleed, no muting.")
    print(f"\n  Captures in real time (~{total_sec / 60:.0f} min), unattended. Ctrl-C aborts cleanly.\n")
    for s in range(5, 0, -1):
        print(f"    starting in {s}…", end="\r")
        time.sleep(1)
    print(" " * 40, end="\r")


def record_playlist(
    playlist_url: str,
    keep_master: bool = False,
    trim_silence: bool = False,
    limit: int | None = None,
    start: int = 1,
) -> tuple[str, list[str]]:
    name, tracks = get_playlist_tracks(playlist_url)
    if not tracks:
        print("  No playable tracks found in playlist.")
        return name, []

    if start > 1:
        tracks = tracks[start - 1:]
        print(f"  (--start {start}: beginning at playlist track {start})")
    if limit:
        tracks = tracks[:limit]
        print(f"  (--limit {limit}: recording {len(tracks)} tracks)")

    playlist_uri = f"spotify:playlist:{parse_playlist_id(playlist_url)}"
    total = sum(t.duration_sec for t in tracks)
    _preflight(name, len(tracks), total)

    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    master_path = str(CAPTURE_DIR / f"{stamp}_master.wav")

    playback.ensure_running()
    playback.pause()           # clean start: don't record any pre-roll
    playback.set_options()

    cap = capture.start_capture(master_path)
    try:
        segments = playback.play_and_log(tracks, playlist_uri)
    finally:
        playback.pause()
        cap.stop()

    if not segments:
        print("  No segments captured.")
        return name, []

    print(f"\n  Splitting recording into {len(segments)} tracks…")
    written = split.split_master(master_path, segments, trim_silence=trim_silence)

    if keep_master:
        print(f"\n  Master kept: {master_path}")
    else:
        Path(master_path).unlink(missing_ok=True)

    return name, written
