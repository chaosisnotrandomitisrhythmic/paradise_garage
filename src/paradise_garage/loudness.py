"""Per-track loudness measurement (EBU R128 / ITU-R BS.1770) via ffmpeg.

Captured tracks stay at their NATIVE mastered loudness (so the RMS energy
classifier and Traktor's own auto-gain both keep working). We measure integrated
LUFS + true peak and store them as ReplayGain tags so loudness-aware players can
level at PLAYBACK time — non-destructively. We never normalize the audio itself.
"""

import re
import subprocess

# ReplayGain 2.0 / EBU R128 reference loudness.
REFERENCE_LUFS = -18.0


def measure(path: str) -> dict:
    """Return {lufs, true_peak_dbtp} for a file (or empty dict on failure)."""
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", path,
         "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    out = proc.stderr
    lufs = re.findall(r"I:\s*(-?[\d.]+)\s*LUFS", out)
    peak = re.findall(r"Peak:\s*(-?[\d.]+)\s*dBFS", out)
    result = {}
    if lufs:
        result["lufs"] = round(float(lufs[-1]), 1)
    if peak:
        result["true_peak_dbtp"] = round(float(peak[-1]), 1)
    return result


def replaygain_fields(lufs: float, true_peak_dbtp: float | None) -> dict:
    """Build ReplayGain Vorbis-comment fields from measured loudness."""
    fields = {
        "replaygain_track_gain": f"{REFERENCE_LUFS - lufs:.2f} dB",
        "replaygain_reference_loudness": f"{REFERENCE_LUFS:.2f} LUFS",
    }
    if true_peak_dbtp is not None:
        fields["replaygain_track_peak"] = f"{10 ** (true_peak_dbtp / 20):.6f}"
    return fields
