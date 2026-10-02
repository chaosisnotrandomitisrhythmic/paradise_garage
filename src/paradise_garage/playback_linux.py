"""Drive the Spotify desktop app on Linux over MPRIS (D-Bus), mirroring playback.py.

Same function names as the AppleScript version so record.py can use either. One
Linux-only quirk: a track started with OpenUri plays ~2 s and then restarts from 0.
`prime()` absorbs that before recording starts: play, wait out the restart, pause,
rewind — the capture then starts and `resume()` plays the track cleanly from 0.
"""

import re
import shutil
import subprocess
import time

from . import capture_linux

DEST = "org.mpris.MediaPlayer2.spotify"
# Pausing drops the last ~1.5 s still buffered in Spotify's stream, and when a track
# ends Spotify rolls on into its album context. So keep the capture running past the
# end and cut the file to the exact track length instead (see record._capture_one).
DRAIN_SEC = 3.0
PLAYER = "org.mpris.MediaPlayer2.Player"
BUS = ["gdbus", "call", "--session", "--dest", DEST, "--object-path", "/org/mpris/MediaPlayer2"]


def _call(method: str, *args: str) -> str:
    return subprocess.run(BUS + ["--method", f"{PLAYER}.{method}", *args],
                          capture_output=True, text=True).stdout


def _get(prop: str) -> str:
    return subprocess.run(BUS + ["--method", "org.freedesktop.DBus.Properties.Get", PLAYER, prop],
                          capture_output=True, text=True).stdout


def _set(prop: str, value: str):
    subprocess.run(BUS + ["--method", "org.freedesktop.DBus.Properties.Set", PLAYER, prop, value],
                   capture_output=True, text=True)


def _running() -> bool:
    out = subprocess.run(["busctl", "--user", "list"], capture_output=True, text=True).stdout
    return DEST in out


def ensure_running():
    capture_linux.ensure_sink()  # must exist before Spotify opens a stream, or audio hits the speakers
    if _running():
        return
    launcher = ["uwsm-app", "--", "spotify"] if shutil.which("uwsm-app") else ["spotify"]
    subprocess.Popen(["setsid", *launcher], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        if _running():
            time.sleep(2)  # let the client finish logging in
            return
        time.sleep(0.5)
    raise RuntimeError("Spotify did not start (no MPRIS service on the session bus)")


def set_options(volume: int = 100):
    # volume is the PipeWire stream volume, set when the stream is routed (route_spotify)
    _set("Shuffle", "<false>")
    _set("LoopStatus", "<'None'>")


def position() -> float:
    m = re.search(r"int64 (-?\d+)", _get("Position"))
    return int(m.group(1)) / 1e6 if m else 0.0


def state() -> str:
    m = re.search(r"'(\w+)'", _get("PlaybackStatus"))
    return m.group(1).lower() if m else ""


def current_uri() -> str:
    """spotify:track:<id>, like `id of current track` in the AppleScript version."""
    m = re.search(r"mpris:trackid': <'([^']*)'>", _get("Metadata"))
    tid = m.group(1) if m else ""
    m = re.match(r"/com/spotify/track/(\w+)$", tid)
    return f"spotify:track:{m.group(1)}" if m else tid


def play_uri(track_uri: str):
    _call("OpenUri", track_uri)


def pause():
    _call("Pause")


def resume():
    _call("Play")


def seek(seconds: float):
    uri = current_uri()
    if not uri.startswith("spotify:track:"):
        return
    path = "/com/spotify/track/" + uri.rsplit(":", 1)[1]
    _call("SetPosition", f"objectpath '{path}'", str(int(seconds * 1e6)))


def _wait_until_playing(uri: str, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if current_uri() == uri and "playing" in state():
            return True
        time.sleep(0.15)
    return False


def prime(track_uri: str, settle: float = 4.0) -> bool:
    """Load the track and leave it paused at 0, past Spotify's start-up restart.
    Returns False if it never started playing."""
    play_uri(track_uri)
    if not _wait_until_playing(track_uri, 12.0):
        return False
    capture_linux.route_spotify()
    time.sleep(settle)
    pause()
    seek(0.0)
    time.sleep(0.5)
    return True


def release():
    """After a recording session: send Spotify back to the normal output."""
    pause()
    capture_linux.release()
