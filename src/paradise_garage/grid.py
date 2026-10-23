"""Check and repair Mixxx beat grids from the kick drum.

A grid is right when its BPM is exact (a 0.08 BPM error drifts a whole beat over
a ten-minute track) and its anchor sits on the kicks, not between them. This
measures both from the audio: low-band (40-150 Hz) onset strength, a fine BPM
sweep around the stored tempo scored by how tightly the onsets cluster on one
beat phase, and that phase as the anchor.

`measure()` reports, per track, the stored grid against the measured one;
`write()` replaces the grid (constant BeatGrid-2.0, source USER, BPM locked)
for the tracks whose error is above the threshold. Mixxx MUST be closed to
write; `--dry-run` works while it runs.
"""

import shutil
import sqlite3
import time
from pathlib import Path

import numpy as np

from .cues import grid_anchor_frame
from .mixxx import DB, beatgrid_blob, mixxx_running

BPM_SPAN = 1.0        # sweep +- this around the stored BPM
BPM_STEP = 0.002
PHASE_TOL = 0.02      # s: an onset counts as "on the beat" within this
OFF_BEATS = 0.08      # anchor error (in beats) above which a grid is "off"
OFF_BPM = 0.02        # BPM error above which a grid is "off"
MIN_CONF = 0.30       # onset concentration below this: live drums / tempo drift, do not trust the measurement
DRIFT_SEGMENTS = 4    # phase is measured per segment too; if it wanders between them the tempo is not constant
MAX_DRIFT = 0.12      # beats: more spread than this between segments -> tempo change, no constant grid fits


REFINE_WINDOW = 0.15  # s: the click of a kick precedes its bass body by up to this much
RISE_FRACTION = 0.3   # the transient starts where the 1 ms envelope first reaches this share of its peak


def _onsets(path: str):
    """Strong low-band onsets (for BPM and rough phase) plus the raw signal
    (for the exact transient)."""
    import librosa

    y, sr = librosa.load(path, sr=None, mono=True)
    hop = 128
    spec = np.abs(librosa.stft(y, n_fft=1024, hop_length=hop))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=1024)
    low = spec[(freqs >= 40) & (freqs <= 150)].mean(axis=0)
    low = np.maximum(0, np.diff(low, prepend=0))
    t = librosa.frames_to_time(np.arange(len(low)), sr=sr, hop_length=hop)
    strong = low > np.percentile(low, 90)
    return t[strong], low[strong], y, sr


def _refine_phase(y, sr: int, bpm: float, phase: float) -> float:
    """Time-domain transient: average the 1 ms RMS envelope over every beat
    (window REFINE_WINDOW before the bass phase to a quarter after), then take
    the attack of that averaged profile: the point after its quiet minimum where
    it first reaches RISE_FRACTION of the way up to its peak. Averaging first
    makes the kick, which is on every beat, dominate hats and claps that are not."""
    beat = 60.0 / bpm
    win = int(REFINE_WINDOW * sr)
    tail = win // 4
    k = max(1, int(0.001 * sr))
    env = np.sqrt(np.convolve(y * y, np.ones(k) / k, mode="same"))
    prof = np.zeros(win + tail)
    count = 0
    for i in range(int((len(y) / sr - phase) / beat)):
        c = int((phase + i * beat) * sr)
        if c - win < 0 or c + tail > len(env):
            continue
        seg = env[c - win:c + tail]
        if seg.max() < 1e-3:
            continue
        prof += seg / seg.max()
        count += 1
    if count < 8:
        return phase
    ipk = int(prof.argmax())
    if ipk == 0:
        return phase
    imin = int(prof[:ipk].argmin())
    floor, peak = prof[imin], prof[ipk]
    rise = imin + int(np.argmax(prof[imin:] >= floor + RISE_FRACTION * (peak - floor)))
    return float((phase + (rise - win) / sr) % beat)


def measure_file(path: str, bpm_hint: float) -> dict:
    """Best BPM near the hint and the kick phase (seconds, 0..beat) on that BPM."""
    tt, ww, y, sr = _onsets(path)
    best = None
    for bpm in np.arange(bpm_hint - BPM_SPAN, bpm_hint + BPM_SPAN, BPM_STEP):
        beat = 60.0 / bpm
        vec = (ww * np.exp(1j * (tt % beat) / beat * 2 * np.pi)).sum()
        r = abs(vec) / ww.sum()
        if best is None or r > best[1]:
            best = (float(bpm), float(r), float(np.angle(vec) % (2 * np.pi) / (2 * np.pi) * beat))
    bpm, conc, phase = best
    beat = 60.0 / bpm
    # tempo drift check: the low-band phase per segment of the track, on the one BPM
    edges = np.linspace(tt.min(), tt.max(), DRIFT_SEGMENTS + 1)
    seg_phase = []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (tt >= a) & (tt < b)
        if m.sum() < 20:
            continue
        v = (ww[m] * np.exp(1j * (tt[m] % beat) / beat * 2 * np.pi)).sum()
        seg_phase.append(float(np.angle(v) % (2 * np.pi)) / (2 * np.pi))     # 0..1 beat
    drift = 0.0
    if len(seg_phase) >= 2:
        d = np.array(seg_phase)
        spread = [max(((d - x + 0.5) % 1.0) - 0.5) - min(((d - x + 0.5) % 1.0) - 0.5) for x in d]
        drift = float(min(spread))
    phase = _refine_phase(y, sr, bpm, phase)
    on = np.abs(((tt - phase + beat / 2) % beat) - beat / 2) < PHASE_TOL
    first = float(tt[on][0]) if on.any() else phase
    return {"bpm": bpm, "concentration": conc, "phase_s": phase, "first_kick_s": first,
            "drift_beats": drift, "samplerate": sr}


def _tracks(con: sqlite3.Connection, playlist: str | None, ids: list[int]) -> list[dict]:
    if ids:
        q = ("SELECT 0, l.id, l.artist, l.title, l.bpm, l.samplerate, l.beats, l.beats_version, tl.location "
             f"FROM library l JOIN track_locations tl ON tl.id = l.location WHERE l.id IN ({','.join('?' * len(ids))})")
        rows = con.execute(q, ids).fetchall()
    else:
        rows = con.execute(
            "SELECT pt.position, l.id, l.artist, l.title, l.bpm, l.samplerate, l.beats, l.beats_version, tl.location "
            "FROM PlaylistTracks pt JOIN Playlists p ON p.id = pt.playlist_id JOIN library l ON l.id = pt.track_id "
            "JOIN track_locations tl ON tl.id = l.location WHERE p.name LIKE ? AND p.hidden = 0 ORDER BY pt.position",
            (f"%{playlist}%",)).fetchall()
    return [dict(pos=r[0], id=r[1], artist=r[2], title=r[3], bpm=r[4], samplerate=r[5], beats=r[6],
                 beats_version=r[7] or "", location=r[8]) for r in rows]


def measure(playlist: str | None = None, ids: list[int] = (), db: Path = DB, progress=None) -> list[dict]:
    con = sqlite3.connect(db)
    try:
        tracks = _tracks(con, playlist, list(ids))
    finally:
        con.close()
    out = []
    for t in tracks:
        if not t["bpm"] or not t["samplerate"]:
            r = {**t, "reason": "no bpm/samplerate yet"}
        else:
            m = measure_file(t["location"], t["bpm"])
            beat = 60.0 / m["bpm"]
            anchor = grid_anchor_frame(t["beats"]) / t["samplerate"] if t["beats_version"].startswith("BeatGrid") else None
            err_beats = None
            if anchor is not None:
                d = (anchor - m["phase_s"]) % beat
                err_beats = min(d, beat - d) / beat
            r = {**t, **m, "bpm_db": t["bpm"], "anchor_s": anchor, "bpm_err": m["bpm"] - t["bpm"], "anchor_err_beats": err_beats,
                 "off": err_beats is None or err_beats > OFF_BEATS or abs(m["bpm"] - t["bpm"]) > OFF_BPM,
                 "uncertain": m["concentration"] < MIN_CONF or abs(m["bpm"] - t["bpm"]) >= BPM_SPAN - BPM_STEP
                              or m["drift_beats"] > MAX_DRIFT}
        r.pop("beats", None)
        out.append(r)
        if progress:
            progress(r)
    return out


def write(results: list[dict], db: Path = DB, dry_run: bool = False, only_off: bool = True) -> dict:
    if not dry_run and mixxx_running():
        raise RuntimeError("Mixxx is running — quit it first (it holds the DB and rewrites tracks on exit).")
    todo = [r for r in results if "bpm_err" in r and not r["uncertain"] and (r["off"] or not only_off)]
    report = {"written": [], "skipped": [r for r in results if r not in todo]}
    if not dry_run and todo:
        backup = db.with_name(f"mixxxdb.sqlite.bak-{time.strftime('%Y%m%d_%H%M%S')}")
        shutil.copy2(db, backup)
        report["backup"] = str(backup)
    con = sqlite3.connect(db)
    try:
        for r in todo:
            sr = r["samplerate"]
            first_frame = round(r["phase_s"] * sr)   # first beat inside the track, on the kick phase
            con.execute(
                "UPDATE library SET bpm = ?, beats = ?, beats_version = 'BeatGrid-2.0', beats_sub_version = '', "
                "bpm_lock = 1 WHERE id = ?", (r["bpm"], beatgrid_blob(r["bpm"], first_frame), r["id"]))
            report["written"].append(r)
        if dry_run:
            con.rollback()
        else:
            con.commit()
    finally:
        con.close()
    return report
