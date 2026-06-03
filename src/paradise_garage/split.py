"""Cut the continuous master capture into per-track FLACs at logged boundaries.

Each segment is extracted with ffmpeg and (by default) conservatively trimmed
of the silent gaps we injected between tracks. The silence threshold is gentle
(-60 dB) so it removes only true digital silence, not quiet musical intros/fades.
Output is 16-bit FLAC to match the existing library.
"""

import subprocess
from pathlib import Path

from .playback import Segment
from .spotify import track_filename

FLAC_DIR = Path.home() / "Music" / "Library" / "flac"


def _silence_filter() -> str:
    return (
        "silenceremove="
        "start_periods=1:start_silence=0.05:start_threshold=-60dB:"
        "stop_periods=-1:stop_silence=0.2:stop_threshold=-60dB"
    )


def split_master(
    master_path: str,
    segments: list[Segment],
    out_dir: Path = FLAC_DIR,
    pad: float = 0.5,
    trim_silence: bool = True,
) -> list[str]:
    """Write one FLAC per segment. Returns the list of output paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    for seg in segments:
        start = max(0.0, seg.start_sec - pad)
        duration = (seg.end_sec - seg.start_sec) + 2 * pad
        if duration <= 0:
            print(f"  SKIP  {seg.track.artist} - {seg.track.title} (zero-length segment)")
            continue

        fname = track_filename(seg.track.artist, seg.track.title)
        out_path = out_dir / fname

        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{start:.3f}",
            "-t", f"{duration:.3f}",
            "-i", master_path,
        ]
        if trim_silence:
            cmd += ["-af", _silence_filter()]
        cmd += [
            "-ac", "2",
            "-ar", "44100",
            "-sample_fmt", "s16",
            "-c:a", "flac",
            "-compression_level", "8",
            str(out_path),
        ]

        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            print(f"  FAIL  {fname}\n{proc.stderr[-400:]}")
            continue
        written.append(str(out_path))
        print(f"  CUT   {fname}")

    return written
