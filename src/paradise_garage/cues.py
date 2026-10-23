"""Editorial hot cues for a Mixxx playlist: IN / MIX IN / BREAK / MIX OUT.

The structure analyzer (structure.py) proposes the four mixing anchors; this
snaps them to the beat grid Mixxx already holds for the track and writes them
as hot cues 1-4, one colour per role, so a four-pad controller shows the same
picture on every track:

    pad 1  IN       blue    groove/bass entry: load here, beatmatch here
    pad 2  MIX IN   green   first full-energy downbeat: bring the fader up
    pad 3  BREAK    yellow  the breakdown
    pad 4  MIX OUT  red     a phrase of runway before the end: start blending out

The main (load) cue is set to IN. Hot cues in slots 1-4 are replaced on every
run; slots 5+ (memory cues from Traktor, hand-made cues) are left alone, so a
track can be re-proposed without losing hand work. Positions are rough anchors
to fine-tune by ear in Mixxx; re-running overwrites the tuning, so run it once
per track and then edit in Mixxx.

Mixxx MUST be closed to write (same rule as `pg mixxx`); --dry-run works while
it runs.
"""

import shutil
import sqlite3
import time
from pathlib import Path

from .mixxx import DB, HOTCUE, MAINCUE, mixxx_running

ROLES = ["IN", "MIX IN", "BREAK", "MIX OUT"]
ROLE_SLOT = {r: i for i, r in enumerate(ROLES)}
# Mixxx's default hot cue palette, so the colours also exist in its colour menu
ROLE_COLOR = {"IN": 0x0044FF, "MIX IN": 0x32BE44, "BREAK": 0xF8D200, "MIX OUT": 0xC50A08}


# --- beat grid blob (mixxx.track.io.BeatGrid, proto2) ------------------------

def _read_varint(b: bytes, i: int) -> tuple[int, int]:
    n = shift = 0
    while True:
        c = b[i]
        i += 1
        n |= (c & 0x7F) << shift
        shift += 7
        if not c & 0x80:
            return n, i


def _fields(b: bytes) -> dict[int, list]:
    i, out = 0, {}
    while i < len(b):
        key, i = _read_varint(b, i)
        field, wtype = key >> 3, key & 7
        if wtype == 0:
            v, i = _read_varint(b, i)
        elif wtype == 1:
            v, i = b[i:i + 8], i + 8
        elif wtype == 2:
            n, i = _read_varint(b, i)
            v, i = b[i:i + n], i + n
        elif wtype == 5:
            v, i = b[i:i + 4], i + 4
        else:
            raise ValueError(f"unsupported wire type {wtype}")
        out.setdefault(field, []).append(v)
    return out


def grid_anchor_frame(blob: bytes | None) -> int:
    """First beat (frame position) of a BeatGrid-2.0 blob; 0 if there is no grid."""
    if not blob:
        return 0
    top = _fields(blob)
    if 2 not in top:
        return 0
    beat = _fields(top[2][0])
    return int(beat.get(1, [0])[0])


# --- proposing ----------------------------------------------------------------

def snap_to_bar(t_sec: float, anchor_sec: float, bpm: float) -> tuple[float, int]:
    """Nearest bar line on the grid: (seconds, bar index from the anchor)."""
    bar = 4 * 60.0 / bpm
    n = round((t_sec - anchor_sec) / bar)
    return max(0.0, anchor_sec + n * bar), n


def playlist_tracks(con: sqlite3.Connection, playlist: str) -> list[dict]:
    rows = con.execute(
        "SELECT pt.position, l.id, l.artist, l.title, l.bpm, l.samplerate, l.beats, "
        "l.beats_version, tl.location FROM PlaylistTracks pt "
        "JOIN Playlists p ON p.id = pt.playlist_id JOIN library l ON l.id = pt.track_id "
        "JOIN track_locations tl ON tl.id = l.location "
        "WHERE p.name LIKE ? AND p.hidden = 0 ORDER BY pt.position", (f"%{playlist}%",)
    ).fetchall()
    return [dict(pos=r[0], id=r[1], artist=r[2], title=r[3], bpm=r[4], samplerate=r[5],
                 beats=r[6], beats_version=r[7] or "", location=r[8]) for r in rows]


def propose_track(track: dict, st: dict | None = None) -> dict:
    """Snapped cues for one library row (needs bpm + samplerate; grid optional)."""
    from . import structure

    bpm, sr = track["bpm"], track["samplerate"]
    if not bpm or not sr:
        return {**track, "cues": [], "reason": "no bpm/samplerate yet (let Mixxx analyze it)"}
    anchor = grid_anchor_frame(track["beats"]) / sr if track["beats_version"].startswith("BeatGrid") else 0.0
    if st is None:
        st = structure.analyze_structure(track["location"], bpm=bpm)
    bar = 4 * 60.0 / bpm
    cues, seen = [], []
    for label, t in sorted(st["cues"], key=lambda c: c[1]):
        snapped, n = snap_to_bar(t, anchor, bpm)
        if any(abs(snapped - s) < bar / 2 for s in seen):  # heuristics can coincide
            continue
        seen.append(snapped)
        cues.append({"label": label, "slot": ROLE_SLOT[label], "sec": snapped, "raw_sec": t, "bar": n})
    out = {k: v for k, v in track.items() if k != "beats"}
    out.update(anchor_sec=anchor, duration_sec=st["duration_sec"], cues=cues)
    return out


def propose(playlist: str, db: Path = DB, progress=None) -> list[dict]:
    con = sqlite3.connect(db)
    try:
        tracks = playlist_tracks(con, playlist)
    finally:
        con.close()
    out = []
    for t in tracks:
        r = propose_track(t)
        out.append(r)
        if progress:
            progress(r)
    return out


# --- writing ------------------------------------------------------------------

def write(proposals: list[dict], db: Path = DB, dry_run: bool = False) -> dict:
    if not dry_run and mixxx_running():
        raise RuntimeError("Mixxx is running — quit it first (it holds the DB and rewrites tracks on exit).")
    report = {"written": 0, "cues": 0, "skipped": []}
    if not dry_run:
        backup = db.with_name(f"mixxxdb.sqlite.bak-{time.strftime('%Y%m%d_%H%M%S')}")
        shutil.copy2(db, backup)
        report["backup"] = str(backup)
    con = sqlite3.connect(db)
    try:
        for p in proposals:
            if not p["cues"]:
                report["skipped"].append(p)
                continue
            tid, sr = p["id"], p["samplerate"]
            con.execute("DELETE FROM cues WHERE track_id = ? AND type = ? AND hotcue BETWEEN 0 AND 3",
                        (tid, HOTCUE))
            con.execute("DELETE FROM cues WHERE track_id = ? AND type = ?", (tid, MAINCUE))
            rows = []
            for c in p["cues"]:
                pos = 2 * round(c["sec"] * sr)  # engine samples = frames * 2
                rows.append((tid, HOTCUE, pos, 0, c["slot"], c["label"], ROLE_COLOR[c["label"]]))
                if c["label"] == "IN":
                    rows.append((tid, MAINCUE, pos, 0, -1, "", ROLE_COLOR["IN"]))
                    con.execute("UPDATE library SET cuepoint = ? WHERE id = ?", (pos, tid))
            con.executemany(
                "INSERT INTO cues (track_id, type, position, length, hotcue, label, color) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
            report["written"] += 1
            report["cues"] += len(p["cues"])
        if dry_run:
            con.rollback()
        else:
            con.commit()
    finally:
        con.close()
    return report


def fmt_time(sec: float) -> str:
    return f"{int(sec // 60)}:{int(sec % 60):02d}"
