"""Drive the Spotify desktop app via AppleScript and log track boundaries.

With the per-process tap, audio is recorded only while Spotify is producing it,
so we play the playlist CONTINUOUSLY (no pausing between tracks — a pause would
not be recorded and would desync the timeline). Boundaries come from polling the
current-track-id transitions; each boundary is position-corrected (subtract the
new track's player position at the moment we notice the change) for sample
accuracy independent of poll latency.
"""

import subprocess
import time
from dataclasses import dataclass

from .spotify import Track


@dataclass
class Segment:
    track: Track
    start_sec: float   # offset into the recording where this track begins
    end_sec: float


def _osa(script: str) -> str:
    return subprocess.run(["osascript", "-e", script], capture_output=True, text=True).stdout.strip()


def _spotify(body: str) -> str:
    return _osa(f'tell application "Spotify" to {body}')


def ensure_running():
    _osa('tell application "Spotify" to activate')
    for _ in range(20):
        if _osa('tell application "Spotify" to return running') == "true":
            return
        time.sleep(0.25)


def set_options(volume: int = 100):
    _spotify("set shuffling to false")
    _spotify("set repeating to false")
    _spotify(f"set sound volume to {volume}")


def position() -> float:
    try:
        return float(_spotify("return player position"))
    except ValueError:
        return 0.0


def state() -> str:
    return _spotify("return player state")


def current_uri() -> str:
    return _spotify("return id of current track")


def play_in_context(track_uri: str, playlist_uri: str):
    _spotify(f'play track "{track_uri}" in context "{playlist_uri}"')


def pause():
    _spotify("pause")


def _wait_until_playing(uri: str, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if current_uri() == uri and "playing" in state():
            return True
        time.sleep(0.15)
    return False


def play_and_log(
    tracks: list[Track],
    playlist_uri: str,
    poll: float = 0.12,
    start_timeout: float = 15.0,
    end_eps: float = 1.0,
) -> list[Segment]:
    """Play the playlist top-to-bottom and return per-track Segments whose offsets
    are relative to the first track's audio (the start of the recording)."""
    uris = [t.uri for t in tracks]
    starts: dict[int, float] = {}

    play_in_context(tracks[0].uri, playlist_uri)
    if not _wait_until_playing(tracks[0].uri, start_timeout):
        print("    ! first track did not start playing")
        return []

    origin = time.monotonic() - position()   # monotonic time of the recording's t=0
    starts[0] = 0.0
    idx = 0
    print(f"    [1/{len(tracks)}] {tracks[0].artist} - {tracks[0].title}")

    while idx < len(tracks) - 1:
        time.sleep(poll)
        cur = current_uri()
        if cur == uris[idx]:
            continue
        now = time.monotonic()
        pos = position()
        if cur == uris[idx + 1]:
            idx += 1
            starts[idx] = (now - pos) - origin
            print(f"    [{idx + 1}/{len(tracks)}] {tracks[idx].artist} - {tracks[idx].title}")
        elif cur in uris:
            # jumped ahead (skip) — resync to wherever we are
            idx = uris.index(cur)
            starts[idx] = (now - pos) - origin
            print(f"    [{idx + 1}/{len(tracks)}] (resync) {tracks[idx].artist} - {tracks[idx].title}")
        else:
            # left the playlist (autoplay/radio past the end) — stop
            print("    (playback left the playlist — stopping)")
            break

    # let the last detected track finish, then stop
    last = idx
    last_dur = tracks[last].duration_sec
    deadline = time.monotonic() + last_dur + 5
    while time.monotonic() < deadline:
        if current_uri() != uris[last] or position() >= last_dur - end_eps:
            break
        time.sleep(poll)
    pause()

    # build segments: end of track i = start of track i+1; last uses its duration
    segments: list[Segment] = []
    ordered = sorted(starts.keys())
    for n, i in enumerate(ordered):
        start = starts[i]
        if n + 1 < len(ordered):
            end = starts[ordered[n + 1]]
        else:
            end = start + tracks[i].duration_sec
        segments.append(Segment(track=tracks[i], start_sec=start, end_sec=end))
    return segments
