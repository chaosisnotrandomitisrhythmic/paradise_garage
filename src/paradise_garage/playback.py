"""Drive the Spotify desktop app via AppleScript and log track boundaries.

Strategy: play the playlist track-by-track (not auto-advance) with a forced
silent gap between tracks. This guarantees a clean silent cut point at every
boundary — immune to crossfade/gapless bleed — and gives precise start/end
offsets measured against the capture clock (time.monotonic() at capture start).
"""

import subprocess
import time
from dataclasses import dataclass

from .spotify import Track


@dataclass
class Segment:
    track: Track
    start_sec: float   # offset into the master capture where this track's audio begins
    end_sec: float     # offset where it ends


def _osa(script: str) -> str:
    proc = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return proc.stdout.strip()


def _osa_spotify(body: str) -> str:
    return _osa(f'tell application "Spotify" to {body}')


def ensure_running():
    _osa('tell application "Spotify" to activate')
    for _ in range(20):
        if _osa('tell application "Spotify" to return running') == "true":
            return
        time.sleep(0.25)


def set_options(volume: int = 100):
    _osa_spotify("set shuffling to false")
    _osa_spotify("set repeating to false")
    _osa_spotify(f"set sound volume to {volume}")


def position() -> float:
    out = _osa_spotify("return player position")
    try:
        return float(out)
    except ValueError:
        return 0.0


def state() -> str:
    return _osa_spotify("return player state")


def current_uri() -> str:
    return _osa_spotify("return id of current track")


def play_uri(uri: str):
    _osa_spotify(f'play track "{uri}"')


def pause():
    _osa_spotify("pause")


def _wait_until_playing(uri: str, timeout: float) -> bool:
    """Block until `uri` is the current track and playing (skips ads). Returns success."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        cur = current_uri()
        if cur == uri and "playing" in state():
            return True
        time.sleep(0.15)
    return False


def play_and_log(
    tracks: list[Track],
    t0: float,
    gap: float = 1.2,
    poll: float = 0.25,
    end_eps: float = 0.6,
    start_timeout: float = 10.0,
) -> list[Segment]:
    segments: list[Segment] = []

    for i, track in enumerate(tracks):
        if i > 0:
            pause()
            time.sleep(gap)  # records a clean silent gap into the master

        play_uri(track.uri)
        ok = _wait_until_playing(track.uri, start_timeout)
        start = time.monotonic() - t0  # stamp after playback is confirmed live
        if not ok:
            print(f"    ! {track.artist} - {track.title}: did not confirm start; best-effort")

        dur = track.duration_sec
        end = start  # fallback
        while True:
            time.sleep(poll)
            cur = current_uri()
            pos = position()
            st = state()
            now = time.monotonic() - t0

            if cur != track.uri:
                # Spotify advanced/changed on its own -> this track ended
                end = now
                break
            if pos >= dur - end_eps:
                end = now
                pause()
                break
            if "stopped" in st:
                end = now
                break

        segments.append(Segment(track=track, start_sec=start, end_sec=end))
        measured = end - start
        flag = "  ⚠ short?" if measured < dur - 5 else ""
        print(
            f"    [{i + 1}/{len(tracks)}] {track.artist} - {track.title}  "
            f"({measured:.0f}s / {dur:.0f}s){flag}"
        )

    pause()
    return segments
