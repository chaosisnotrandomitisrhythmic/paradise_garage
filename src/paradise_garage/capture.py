"""Headless audio capture of the BlackHole 2ch virtual device via ffmpeg.

Records one continuous 44.1 kHz / 16-bit stereo master WAV (PCM for fast
seeking during the split step). The BlackHole avfoundation index is detected
at runtime rather than hardcoded.
"""

import re
import shutil
import subprocess
import time
from dataclasses import dataclass


def current_output() -> str | None:
    """Current default audio output device name, or None if SwitchAudioSource is absent."""
    if not shutil.which("SwitchAudioSource"):
        return None
    proc = subprocess.run(
        ["SwitchAudioSource", "-c", "-t", "output"], capture_output=True, text=True
    )
    return proc.stdout.strip() or None


def set_output(name: str) -> bool:
    """Set the default audio output device. Returns True on success."""
    if not shutil.which("SwitchAudioSource"):
        return False
    proc = subprocess.run(
        ["SwitchAudioSource", "-s", name, "-t", "output"], capture_output=True, text=True
    )
    return proc.returncode == 0


def find_blackhole_index() -> int:
    """Return the avfoundation audio-device index for 'BlackHole 2ch'."""
    proc = subprocess.run(
        ["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
        capture_output=True,
        text=True,
    )
    # device list is printed to stderr
    in_audio = False
    for line in proc.stderr.splitlines():
        if "audio devices" in line.lower():
            in_audio = True
            continue
        if in_audio:
            m = re.search(r"\[(\d+)\]\s+(.*)", line)
            if m and "blackhole" in m.group(2).lower():
                return int(m.group(1))
    raise RuntimeError(
        "BlackHole 2ch not found as an avfoundation audio device. "
        "Install BlackHole and confirm with: ffmpeg -f avfoundation -list_devices true -i ''"
    )


@dataclass
class Capture:
    proc: subprocess.Popen
    path: str
    t0: float  # time.monotonic() at capture start

    def stop(self) -> str:
        """Gracefully stop ffmpeg and return the master WAV path."""
        if self.proc.poll() is None:
            try:
                # 'q' tells ffmpeg to finalize the file cleanly
                self.proc.communicate(input=b"q", timeout=10)
            except Exception:
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=5)
                except Exception:
                    self.proc.kill()
        return self.path


def start_capture(out_path: str, sample_rate: int = 44100, warmup: float = 0.4) -> Capture:
    """Begin recording BlackHole to out_path (WAV/PCM s16le). Blocks `warmup`
    seconds so ffmpeg's input is live before the caller starts playback."""
    idx = find_blackhole_index()
    cmd = [
        "ffmpeg", "-y",
        "-f", "avfoundation",
        "-i", f":{idx}",
        "-ac", "2",
        "-ar", str(sample_rate),
        "-c:a", "pcm_s16le",
        out_path,
    ]
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(warmup)
    t0 = time.monotonic()
    return Capture(proc=proc, path=out_path, t0=t0)
