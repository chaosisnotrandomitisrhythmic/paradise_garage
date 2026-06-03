"""Per-process audio capture of Spotify via the Core Audio process-tap helper.

Captures ONLY Spotify's audio stream (native/SpotifyTap.app) — no notification or
other-app bleed, and no system-output rerouting or muting. Spotify keeps playing
through whatever output you're on while we tap it.

The helper must run AS the app (via LaunchServices `open`) so macOS applies the
app's "Audio Recording" (kTCCServiceAudioCapture) grant rather than attributing
the request to the ungranted parent shell.
"""

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

APP_PATH = Path(__file__).parent.parent.parent / "native" / "SpotifyTap.app"
# pgrep/pkill match string for the running helper process
PROC_MATCH = "SpotifyTap.app/Contents/MacOS/spotify-tap"


@dataclass
class Capture:
    path: str
    t0: float  # time.monotonic() once the tap is live (recording can begin)

    def stop(self) -> str:
        subprocess.run(["pkill", "-TERM", "-f", PROC_MATCH], capture_output=True)
        time.sleep(0.6)  # let ExtAudioFile finalize the WAV header
        return self.path


def _running() -> bool:
    return subprocess.run(["pgrep", "-f", PROC_MATCH], capture_output=True).returncode == 0


def start_capture(out_path: str, warmup: float = 1.8) -> Capture:
    if not APP_PATH.exists():
        raise RuntimeError(
            f"{APP_PATH} not found — build the tap helper first: "
            f"bash native/build.sh"
        )
    # clear any stale instance, then launch via LaunchServices
    subprocess.run(["pkill", "-f", PROC_MATCH], capture_output=True)
    time.sleep(0.3)
    subprocess.run(["open", str(APP_PATH), "--args", "--out", out_path], check=True)

    # wait for the helper to actually be running before returning
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline and not _running():
        time.sleep(0.15)
    if not _running():
        raise RuntimeError(
            "tap helper did not start. If this is the first run, grant it once:\n"
            f"  open {APP_PATH} --args --request-permission\n"
            "then approve under System Settings → Privacy & Security → Audio Recording."
        )
    time.sleep(warmup)  # tap/aggregate-device init settle
    return Capture(path=out_path, t0=time.monotonic())
