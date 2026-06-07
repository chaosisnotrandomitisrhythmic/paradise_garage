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


def find_missing(tracks, flac_dir: Path) -> tuple[list, list]:
    """Split playlist tracks into (missing, have) where have = [(track, path)].
    A track counts as present only if a library file matches (fuzzy) AND its
    duration matches the playlist track — so truncated/silent partials are
    treated as missing and get re-recorded."""
    from .tag import parse_filename

    index = {}
    for f in flac_dir.glob("*.flac"):
        a, t = parse_filename(str(f))
        index[_match_key(a, t)] = f

    missing, have = [], []
    for tr in tracks:
        path = index.get(_match_key(tr.artist, tr.title))
        ok = False
        if path:
            d = _ffprobe_duration(path)
            if d is not None and abs(d - tr.duration_sec) <= max(15.0, 0.08 * tr.duration_sec):
                ok = True
        if ok:
            have.append((tr, path))
        else:
            missing.append(tr)
    return missing, have


def _union_playlist_tags(paths: list[Path], playlist_name: str, dry_run: bool = False) -> int:
    """Add the playlist tag to already-present library tracks (file tags +
    catalog) without re-recording or re-analyzing — so the Traktor playlist
    sync picks them up too. Returns how many tracks needed the tag."""
    from mutagen.flac import FLAC

    from .catalog import load_catalog, save_catalog

    changed = 0
    catalog = None
    for p in paths:
        audio = FLAC(str(p))
        current = set(audio.get("playlist", []))
        if playlist_name in current:
            continue
        changed += 1
        if dry_run:
            continue
        merged = sorted(current | {playlist_name})
        audio["playlist"] = merged
        audio["grouping"] = merged
        audio.save()
        if catalog is None:
            catalog = load_catalog()
        entry = catalog["tracks"].get(p.name)
        if entry is not None:
            entry["playlists"] = sorted({*entry.get("playlists", []), playlist_name})
    if catalog is not None:
        save_catalog(catalog)
    return changed


def _capture_one(track, flac_dir: Path, trim_silence: bool = True) -> str | None:
    """Record one track to its own FLAC (resumable: each track is finished + saved
    before the next). Returns the output path or None."""
    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    tmp = str(CAPTURE_DIR / f"{stamp}_one.wav")
    dur = track.duration_sec

    cap = capture.start_capture(tmp)
    t_cap = time.monotonic()
    watch_offset = 0.0   # dead time (retries/handshakes) before playback really started
    try:
        outer = 0
        while True:
            # AirPlay/Sonos outputs can swallow the play command while the route
            # re-handshakes between tracks — retry instead of trusting one shot.
            started = False
            for attempt in range(3):
                playback.play_uri(track.uri)
                if playback._wait_until_playing(track.uri, 12.0):
                    started = True
                    break
                print(f"    ! playback didn't confirm (attempt {attempt + 1}/3)")
            if not started:
                print("    ! playback never started — skipping (retry via --skip-existing)")
                return None
            if playback.position() > 3.0:
                # Spotify resumed the track at a remembered position (deterministic
                # for tracks previously played near their end) — rewind while
                # paused and restart the capture so the file head is clean.
                print(f"    ! resumed at {playback.position():.0f}s — rewinding, restarting capture")
                playback.pause()
                playback.seek(0.0)
                cap.stop()
                Path(tmp).unlink(missing_ok=True)
                cap = capture.start_capture(tmp)
                t_cap = time.monotonic()
                playback.resume()   # resume from 0, NOT play_uri (would re-jump)
                if not playback._wait_until_playing(track.uri, 12.0):
                    print("    ! playback never restarted after rewind — skipping")
                    return None
            watch_offset = time.monotonic() - t_cap
            # Detect the TRUE end by watching the player position, not the API duration
            # (they can disagree, and a standalone track loops back to 0 at its real end).
            deadline = time.monotonic() + dur + 60
            peak = 0.0
            t_loop = time.monotonic()
            why = "deadline"
            empty_since = None
            stalled = False
            last_pos, last_advance = -1.0, time.monotonic()
            while time.monotonic() < deadline:
                time.sleep(0.25)
                cur = playback.current_uri()
                pos = playback.position()
                st = playback.state()
                if pos != last_pos:
                    last_pos, last_advance = pos, time.monotonic()
                elif time.monotonic() - last_advance > 20.0:
                    # position frozen mid-track (AirPlay stall) — the capture from
                    # here on is silence; treat the whole track as failed
                    why = f"stalled (pos frozen at {pos:.1f}s)"
                    stalled = True
                    break
                if cur != track.uri:                       # advanced to another track
                    if cur == "":
                        # transient '' during AirPlay rebuffer — a real track end
                        # always reports the NEXT uri; only bail if '' persists
                        empty_since = empty_since or time.monotonic()
                        if time.monotonic() - empty_since < 3.0:
                            continue
                    why = f"uri-changed (cur={cur!r})"
                    break
                empty_since = None
                if "playing" not in st and pos < 1.0:      # stopped at the end
                    why = f"stopped (state={st!r} pos={pos:.2f})"
                    break
                if peak > 5.0 and pos + 1.5 < peak:        # position jumped back = looped/ended
                    why = f"pos-jumped-back (pos={pos:.2f} peak={peak:.2f})"
                    break
                if pos >= dur - 0.3:                       # reached the API end (when it matches)
                    why = "reached-end"
                    break
                peak = max(peak, pos)
            elapsed = time.monotonic() - t_loop
            print(f"    loop exit: {why} after {elapsed:.1f}s (api dur {dur:.1f}s, peak pos {peak:.1f}s)")

            # Playback can also die right AFTER confirming (AirPlay route collapse:
            # 'stopped'/'paused'/uri-flip at pos≈0 within seconds) — re-play instead
            # of failing; the capture keeps rolling and the dead time is silence
            # that the split window accounts for via watch_offset.
            died_at_start = not stalled and peak < 5.0 and elapsed < 8.0
            if died_at_start and outer < 2:
                outer += 1
                print(f"    ! playback died at start — re-playing ({outer}/2)")
                continue
            break
    finally:
        playback.pause()
        cap.stop()

    if stalled:
        print(f"    ! playback stalled — skipping (retry via --skip-existing), keeping {tmp}")
        return None

    # Sanity-check the raw capture before splitting (debug instrumentation).
    import subprocess as _sp
    probe = _sp.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", tmp], capture_output=True, text=True)
    wav_dur = float(probe.stdout.strip()) if probe.stdout.strip() else 0.0
    vol = _sp.run(
        ["ffmpeg", "-hide_banner", "-i", tmp, "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True)
    levels = [ln.strip() for ln in vol.stderr.splitlines() if "_volume" in ln]
    print(f"    raw capture: {wav_dur:.1f}s | {' | '.join(x.split('] ')[-1] for x in levels)}")

    # The temp file is [tap warmup + retry dead time] + [full track] + [trailing].
    # Cover the WHOLE file (ffmpeg stops at EOF) and let the silence-trim strip
    # both ends — but the cut window must include watch_offset, or start-retry
    # dead time would push the track's tail past the window and clip it.
    seg = [Segment(track=track, start_sec=0.0, end_sec=watch_offset + dur + 30.0)]
    written = split.split_master(tmp, seg, out_dir=flac_dir, pad=0.0, trim_silence=trim_silence)
    out = written[0] if written else None
    # A sane capture is at least half the API duration AND has no ≥10s silent
    # stretch (a stalled/dropped capture records silence that can pad the file
    # back to a plausible duration — caught one at 259s/469s padded to 497s).
    # Otherwise treat as failed, remove the stub FLAC (it would crash ingest /
    # pollute the library) and keep the raw WAV for forensics.
    if out:
        d = _ffprobe_duration(Path(out))
        reason = None
        if d is None or d < dur * 0.5:
            reason = f"{'unreadable' if d is None else f'{d:.1f}s'} vs expected {dur:.1f}s"
        else:
            sil = _sp.run(
                ["ffmpeg", "-hide_banner", "-i", out,
                 "-af", "silencedetect=noise=-50dB:d=10", "-f", "null", "-"],
                capture_output=True, text=True)
            if "silence_start" in sil.stderr:
                reason = "contains a ≥10s silent stretch (stall/dropout)"
        if reason:
            print(f"    ! capture failed ({reason}) — removing stub, keeping {tmp}")
            Path(out).unlink(missing_ok=True)
            return None
    Path(tmp).unlink(missing_ok=True)
    return out


def record_missing(
    playlist_url: str, dry_run: bool = False, limit: int | None = None
) -> tuple[str, list[str]]:
    """Scan the playlist against the library and record ONLY the tracks we don't
    already have. Resumable by design — re-run after an interruption and it picks
    up just what's still missing. --limit N records only the first N missing
    tracks (chunked sessions for big playlists)."""
    name, tracks = get_playlist_tracks(playlist_url)
    if not tracks:
        print("  No playable tracks found in playlist.")
        return name, []

    flac_dir = split.FLAC_DIR
    missing, have = find_missing(tracks, flac_dir)

    print(f"\n  Playlist: {name}  ({len(tracks)} tracks)")
    print(f"  Already in library: {len(have)} | to record: {len(missing)}")
    # already-present tracks still belong to this playlist — union the tag so
    # `pg traktor --playlists` includes them (no re-record, no re-analysis)
    n_tagged = _union_playlist_tags(sorted({p for _, p in have}), name, dry_run=dry_run)
    if n_tagged:
        verb = "would tag" if dry_run else "tagged"
        print(f"  ({verb} {n_tagged} already-present track(s) with playlist '{name}')")
    if limit and limit < len(missing):
        missing = missing[:limit]
        print(f"  (--limit {limit}: recording the first {limit} missing tracks this session)")
    print()
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
    failed = []
    try:
        for i, t in enumerate(missing, 1):
            print(f"\n  [{i}/{len(missing)}] {t.artist} - {t.title}")
            try:
                out = _capture_one(t, flac_dir)
                if out:
                    cmd_ingest([out], playlist=name)  # ingest now → counts as 'have' on resume
                    written.append(out)
                else:
                    failed.append(t)
            except KeyboardInterrupt:
                raise
            except Exception as e:  # one bad track must not abort the whole run
                print(f"    ! failed: {e}")
                failed.append(t)
    finally:
        playback.pause()

    if failed:
        print(f"\n  ! {len(failed)} track(s) failed — re-run with --skip-existing to retry:")
        for t in failed:
            print(f"    • {t.artist} - {t.title}")

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
