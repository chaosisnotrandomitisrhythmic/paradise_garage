"""Orchestrate: Spotify playlist -> headless capture -> boundary log -> per-track FLACs.

This is Phase 1 of `pg record`. It produces named FLACs in ~/Music/Library/flac/
and returns their paths; the CLI then runs the existing ingest (librosa + tags +
catalog) over them. Traktor NML + Ableton .als generation are later phases.
"""

import time
from pathlib import Path

from . import capture, playback, split
from .spotify import get_playlist_tracks

CAPTURE_DIR = Path.home() / ".cache" / "paradise_garage" / "captures"


def _preflight(name: str, n: int, total_sec: float):
    print(f"\n  Playlist: {name}  ({n} tracks, ~{total_sec / 60:.0f} min real-time)\n")
    print("  PREFLIGHT — confirm before this runs unattended:")
    print("    • Output auto-routes to BlackHole 2ch and restores after (use --device for a Multi-Output to monitor)")
    print("    • Spotify: Settings → Playback → Crossfade OFF, Normalize OFF, Autoplay OFF")
    print("    • Spotify Premium (free-tier ads pollute captures)")
    print("    • Output volume at 100% (level is captured as-is — see the 'render unity' rule)")
    print(f"\n  Capturing in real time — this takes ~{total_sec / 60:.0f} min. Ctrl-C aborts cleanly.\n")
    for s in range(5, 0, -1):
        print(f"    starting in {s}…", end="\r")
        time.sleep(1)
    print(" " * 40, end="\r")


def record_playlist(
    playlist_url: str,
    keep_master: bool = False,
    trim_silence: bool = True,
    route: bool = True,
    limit: int | None = None,
    device: str = "BlackHole 2ch",
) -> tuple[str, list[str]]:
    name, tracks = get_playlist_tracks(playlist_url)
    if not tracks:
        print("  No playable tracks found in playlist.")
        return name, []

    if limit:
        tracks = tracks[:limit]
        print(f"  (--limit {limit}: recording first {len(tracks)} tracks only)")

    total = sum(t.duration_sec for t in tracks)
    _preflight(name, len(tracks), total)

    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    master_path = str(CAPTURE_DIR / f"{stamp}_master.wav")

    # Route system output to BlackHole for the capture, restore afterward.
    prev_output = None
    if route:
        prev_output = capture.current_output()
        if prev_output is None:
            print("  ! SwitchAudioSource not found — cannot auto-route; "
                  "make sure output already goes to BlackHole.")
        elif prev_output != device:
            if capture.set_output(device):
                print(f"  Routed output: {prev_output} → {device} (will restore after)")
            else:
                print(f"  ! Could not switch output to {device!r}; check the device name.")

    playback.ensure_running()
    playback.set_options()

    cap = capture.start_capture(master_path)
    try:
        segments = playback.play_and_log(tracks, cap.t0)
    except KeyboardInterrupt:
        print("\n  Aborted by user — finalizing partial capture.")
        segments = []
        raise
    finally:
        playback.pause()
        cap.stop()
        if route and prev_output and capture.current_output() != prev_output:
            capture.set_output(prev_output)
            print(f"  Restored output → {prev_output}")

    if not segments:
        print("  No segments captured.")
        return name, []

    print(f"\n  Splitting master into {len(segments)} tracks…")
    written = split.split_master(master_path, segments, trim_silence=trim_silence)

    if not keep_master:
        Path(master_path).unlink(missing_ok=True)
    else:
        print(f"\n  Master kept: {master_path}")

    return name, written
