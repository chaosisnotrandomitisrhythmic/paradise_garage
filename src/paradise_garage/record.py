"""Orchestrate: Spotify playlist -> per-process tap capture -> boundary log -> per-track FLACs.

Phase 1 of `pg record`. Captures only Spotify (no bleed, no rerouting, no muting),
splits the continuous recording at detected track boundaries, names the files, and
hands them to the existing ingest (librosa + tags + catalog).
"""

import re
import subprocess
import time
from pathlib import Path

from . import capture, playback, split
from .playback import Segment
from .spotify import get_playlist_tracks, parse_playlist_id

CAPTURE_DIR = Path.home() / ".cache" / "paradise_garage" / "captures"


def _ffprobe_duration(path: Path) -> float | None:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nk=1:nw=1", str(path)],
        capture_output=True, text=True,
    ).stdout.strip()
    try:
        return float(out)
    except ValueError:
        return None


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _match_key(artist: str, title: str) -> str:
    """Fuzzy identity: first artist + punctuation-stripped title. Tolerates
    'Lil' Louis, The World' vs 'Lil' Louis' and 'X - Mix' vs 'X (Mix)'."""
    return _norm(artist.split(",")[0]) + "|" + _norm(title)


def find_missing(tracks, flac_dir: Path) -> list:
    """Playlist tracks we DON'T already have a good FLAC for. A track counts as
    present only if a library file matches (fuzzy) AND its duration matches the
    playlist track — so truncated/silent partials are treated as missing and
    get re-recorded."""
    from .tag import parse_filename

    index = {}
    for f in flac_dir.glob("*.flac"):
        a, t = parse_filename(str(f))
        index[_match_key(a, t)] = f

    missing = []
    for tr in tracks:
        path = index.get(_match_key(tr.artist, tr.title))
        ok = False
        if path:
            d = _ffprobe_duration(path)
            if d is not None and abs(d - tr.duration_sec) <= max(15.0, 0.08 * tr.duration_sec):
                ok = True
        if not ok:
            missing.append(tr)
    return missing


def _capture_one(track, flac_dir: Path, trim_silence: bool = True) -> str | None:
    """Record one track to its own FLAC (resumable: each track is finished + saved
    before the next). Returns the output path or None."""
    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    tmp = str(CAPTURE_DIR / f"{stamp}_one.wav")
    dur = track.duration_sec

    cap = capture.start_capture(tmp)
    try:
        playback.play_uri(track.uri)
        if not playback._wait_until_playing(track.uri, 12.0):
            print("    ! did not confirm playback start")
        deadline = time.monotonic() + dur + 20
        while time.monotonic() < deadline:
            time.sleep(0.25)
            if playback.current_uri() != track.uri:
                break
            if playback.position() >= dur - 0.2:
                break
    finally:
        playback.pause()
        cap.stop()

    seg = [Segment(track=track, start_sec=0.0, end_sec=dur + 1.0)]
    written = split.split_master(tmp, seg, out_dir=flac_dir, pad=0.0, trim_silence=trim_silence)
    Path(tmp).unlink(missing_ok=True)
    return written[0] if written else None


def record_missing(playlist_url: str, dry_run: bool = False) -> tuple[str, list[str]]:
    """Scan the playlist against the library and record ONLY the tracks we don't
    already have. Resumable by design — re-run after an interruption and it picks
    up just what's still missing."""
    name, tracks = get_playlist_tracks(playlist_url)
    if not tracks:
        print("  No playable tracks found in playlist.")
        return name, []

    flac_dir = split.FLAC_DIR
    missing = find_missing(tracks, flac_dir)
    have = len(tracks) - len(missing)

    print(f"\n  Playlist: {name}  ({len(tracks)} tracks)")
    print(f"  Already in library: {have} | to record: {len(missing)}\n")
    for t in missing:
        print(f"    • {t.artist} - {t.title}  ({t.duration_sec / 60:.1f}m)")

    if dry_run or not missing:
        if not missing:
            print("\n  Nothing to record — library already complete for this playlist. ✓")
        return name, []

    total = sum(t.duration_sec for t in missing)
    print(f"\n  Recording {len(missing)} tracks (~{total / 60:.0f} min). Each is saved as it "
          f"finishes, so re-running resumes from where it left off. Ctrl-C is safe.\n")
    for s in range(5, 0, -1):
        print(f"    starting in {s}…", end="\r")
        time.sleep(1)
    print(" " * 40, end="\r")

    playback.ensure_running()
    playback.pause()
    playback.set_options()

    from .cli import cmd_ingest
    written = []
    try:
        for i, t in enumerate(missing, 1):
            print(f"\n  [{i}/{len(missing)}] {t.artist} - {t.title}")
            out = _capture_one(t, flac_dir)
            if out:
                cmd_ingest([out], playlist=name)  # ingest now → counts as 'have' on resume
                written.append(out)
    finally:
        playback.pause()

    print(f"\n  Done — recorded {len(written)}/{len(missing)} missing tracks.")
    return name, written


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
