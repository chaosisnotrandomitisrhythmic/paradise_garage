"""Capture Spotify on Linux through a silent PipeWire sink.

Spotify's stream goes to a virtual null sink ("pg_capture", 44.1 kHz) and we record
that sink's monitor — so nothing plays through the speakers, no other app bleeds in,
and the signal is Spotify's own digital output. WirePlumber remembers the routing per
app, which is why `release()` moves Spotify back to the default output when done.

Recorded at 24 bit so Spotify Lossless (up to 24/44.1) survives intact.
"""

import json
import subprocess
import time
from dataclasses import dataclass

SINK = "pg_capture"
RATE = 44100
BITS = 24


def _pactl(*args: str) -> str:
    return subprocess.run(["pactl", *args], capture_output=True, text=True, check=True).stdout


def ensure_sink():
    """Create the silent capture sink if it isn't there (it lasts until PipeWire restarts)."""
    names = [line.split("\t")[1] for line in _pactl("list", "short", "sinks").splitlines() if "\t" in line]
    if SINK not in names:
        _pactl("load-module", "module-null-sink", f"sink_name={SINK}", f"rate={RATE}", "channels=2",
               f"sink_properties=device.description={SINK}")
    _pactl("set-sink-volume", SINK, "100%")


def _spotify_inputs() -> list[int]:
    inputs = json.loads(_pactl("-f", "json", "list", "sink-inputs"))
    return [s["index"] for s in inputs if s["properties"].get("application.name") == "Spotify"]


def route_spotify() -> bool:
    """Move Spotify's stream onto the capture sink at 100% volume. False if Spotify has no stream yet."""
    found = _spotify_inputs()
    for idx in found:
        _pactl("move-sink-input", str(idx), SINK)
        _pactl("set-sink-input-volume", str(idx), "100%")
    return bool(found)


def release():
    """Send Spotify back to the default output so normal listening is audible again."""
    default = _pactl("get-default-sink").strip()
    for idx in _spotify_inputs():
        _pactl("move-sink-input", str(idx), default)


@dataclass
class Capture:
    path: str
    t0: float  # time.monotonic() once the recorder is live
    proc: subprocess.Popen

    def stop(self) -> str:
        self.proc.terminate()
        self.proc.wait(timeout=5)
        return self.path


def start_capture(out_path: str, warmup: float = 0.5, bundle_prefix: str | None = None) -> Capture:
    if bundle_prefix:
        raise RuntimeError("browser capture (pg capture) is macOS-only for now")
    ensure_sink()
    proc = subprocess.Popen(
        ["parecord", f"--device={SINK}.monitor", f"--rate={RATE}", "--channels=2",
         f"--format=s{BITS}le", "--latency-msec=50", "--file-format=wav", out_path],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )
    time.sleep(warmup)
    if proc.poll() is not None:
        raise RuntimeError(f"parecord exited: {proc.stderr.read().decode().strip()}")
    return Capture(path=out_path, t0=time.monotonic(), proc=proc)
