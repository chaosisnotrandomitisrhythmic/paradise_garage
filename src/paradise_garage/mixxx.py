"""Bring a Traktor collection.nml into Mixxx's library (mixxxdb.sqlite).

Mixxx only reads Traktor's file names and playlists, not the grid or cues, so
this fills them in. Same rule as `pg traktor`: never fabricate an entry. Mixxx
scans the files first (it owns the library rows, paths and sample rates); we
only UPDATE rows it already has, matched by file NAME, so the absolute Mac paths
stored in the NML (which differ per machine) never matter.

Per track, from the NML:
- grid: TEMPO BPM + the first grid marker (CUE_V2 TYPE=4) become a constant
  BeatGrid-2.0, with source USER and bpm_lock=1 so the analyzer leaves it alone.
  Tracks with several grid markers get the first one and are flagged.
- key: MUSICAL_KEY (0-11 major, 12-23 minor, from C) becomes Mixxx's key text,
  loaded as a USER key so the analyzer does not overwrite it.
- cues: hot cues (TYPE 0) and loops (TYPE 5) keep their slot; the load marker
  (TYPE 3) becomes the main cue. Memory cues/loops without a slot go to slots
  8+ in time order (Mixxx has no memory cues). Fade markers are skipped.
- playlists: every Traktor playlist becomes a Mixxx playlist of the same name
  (refilled on re-run). Names starting with "_" and the History folder are skipped.

Mixxx MUST be closed (it holds the DB and rewrites tracks on exit); the DB is
backed up before writing.
"""

import shutil
import sqlite3
import struct
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

DB = Path.home() / ".mixxx" / "mixxxdb.sqlite"

# Mixxx CueType values (src/track/cueinfo.h)
HOTCUE, MAINCUE, LOOP = 1, 2, 4
# Traktor CUE_V2 TYPE values
T_CUE, T_FADE_IN, T_FADE_OUT, T_LOAD, T_GRID, T_LOOP = 0, 1, 2, 3, 4, 5

COLOR = {HOTCUE: 0x0044FF, LOOP: 0x32BE44, MAINCUE: 0xF8D200}  # Mixxx hotcue palette
FIRST_MEMORY_SLOT = 8  # Traktor hot cues use slots 0-7
KEY_NAMES = ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
SOURCE_USER = 2  # mixxx.track.io.Source.USER


def mixxx_running() -> bool:
    return subprocess.run(["pgrep", "-x", "mixxx"], capture_output=True).returncode == 0


# --- protobuf (proto2, hand-encoded: two tiny messages, no dependency) -------

def _varint(n: int) -> bytes:
    n &= (1 << 64) - 1  # negative int32 encodes as 10-byte two's complement
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def _field_bytes(field: int, payload: bytes) -> bytes:
    return _varint(field << 3 | 2) + _varint(len(payload)) + payload


def beatgrid_blob(bpm: float, first_frame: int) -> bytes:
    """mixxx.track.io.BeatGrid { Bpm bpm = 1; Beat first_beat = 2; } (src/proto/beats.proto)."""
    bpm_msg = _varint(1 << 3 | 1) + struct.pack("<d", bpm) + _varint(2 << 3) + _varint(SOURCE_USER)
    beat_msg = _varint(1 << 3) + _varint(first_frame) + _varint(3 << 3) + _varint(SOURCE_USER)
    return _field_bytes(1, bpm_msg) + _field_bytes(2, beat_msg)


# --- NML parsing --------------------------------------------------------------

def key_text(value: int) -> str:
    """Traktor MUSICAL_KEY VALUE (0-11 major, 12-23 minor) to Mixxx key text."""
    return KEY_NAMES[value % 12] + ("m" if value >= 12 else "")


def parse_entry(entry: ET.Element) -> dict:
    loc = entry.find("LOCATION")
    tempo = entry.find("TEMPO")
    key = entry.find("MUSICAL_KEY")
    cues = []
    for c in entry.findall("CUE_V2"):
        cues.append({
            "name": c.get("NAME", ""),
            "type": int(c.get("TYPE", "0")),
            "start_ms": float(c.get("START", "0")),
            "len_ms": float(c.get("LEN", "0")),
            "hotcue": int(c.get("HOTCUE", "-1")),
        })
    grids = sorted((c for c in cues if c["type"] == T_GRID), key=lambda c: c["start_ms"])
    return {
        "file": loc.get("FILE") if loc is not None else None,
        "bpm": float(tempo.get("BPM")) if tempo is not None and tempo.get("BPM") else None,
        "grid_ms": grids[0]["start_ms"] if grids else None,
        "grid_markers": len(grids),
        "key": int(key.get("VALUE")) if key is not None and key.get("VALUE") else None,
        "cues": [c for c in cues if c["type"] != T_GRID],
    }


def _key_filename(primary_key: str) -> str:
    # "Macintosh HD/:Users/:x/:Music/:Library/:flac/:Artist - Title.flac"
    return primary_key.rsplit("/:", 1)[-1]


def parse_playlists(root: ET.Element) -> dict[str, list[str]]:
    """Playlist name -> ordered file names. Skips '_*' playlists and the History folder."""
    out: dict[str, list[str]] = {}

    def walk(node: ET.Element, skip: bool):
        name = node.get("NAME", "")
        skip = skip or (node.get("TYPE") == "FOLDER" and name.lower() == "history")
        if node.get("TYPE") == "PLAYLIST" and not skip and not name.startswith("_"):
            pl = node.find("PLAYLIST")
            keys = [pk.get("KEY") for pk in pl.iter("PRIMARYKEY")] if pl is not None else []
            out[name] = [_key_filename(k) for k in keys if k]
        subs = node.find("SUBNODES")
        if subs is not None:
            for child in subs.findall("NODE"):
                walk(child, skip)

    playlists = root.find("PLAYLISTS")
    if playlists is not None:
        for node in playlists.findall("NODE"):
            walk(node, False)
    return out


# --- cue mapping --------------------------------------------------------------

def _frames(ms: float, samplerate: int) -> int:
    return round(ms / 1000.0 * samplerate)


def map_cues(cues: list[dict], samplerate: int) -> tuple[list[dict], list[str]]:
    """Traktor cues -> Mixxx cue rows (position/length in engine samples = frames * 2)."""
    rows, skipped = [], []
    used = {c["hotcue"] for c in cues if c["hotcue"] >= 0}
    next_slot = FIRST_MEMORY_SLOT

    for c in sorted(cues, key=lambda c: (c["hotcue"] < 0, c["start_ms"])):
        pos = 2 * _frames(c["start_ms"], samplerate)
        if c["type"] == T_LOAD:
            rows.append({"type": MAINCUE, "position": pos, "length": 0, "hotcue": -1, "label": c["name"]})
            continue
        if c["type"] not in (T_CUE, T_LOOP):
            skipped.append(f'{c["name"] or "marker"} (type {c["type"]})')
            continue
        if c["type"] == T_LOOP and c["len_ms"] <= 0:
            skipped.append(f'{c["name"] or "loop"} (zero length)')
            continue
        slot = c["hotcue"]
        if slot < 0:  # memory cue/loop: next free slot from 8
            while next_slot in used:
                next_slot += 1
            slot = next_slot
            used.add(slot)
        mtype = LOOP if c["type"] == T_LOOP else HOTCUE
        length = 2 * _frames(c["len_ms"], samplerate) if mtype == LOOP else 0
        label = "" if c["name"] in ("n.n.", "AutoGrid") else c["name"]
        rows.append({"type": mtype, "position": pos, "length": length, "hotcue": slot, "label": label})
    return rows, skipped


# --- apply --------------------------------------------------------------------

def _library_index(con: sqlite3.Connection) -> dict[str, list[tuple]]:
    idx: dict[str, list[tuple]] = {}
    for tid, fname, sr in con.execute(
        "SELECT l.id, tl.filename, l.samplerate FROM library l "
        "JOIN track_locations tl ON l.location = tl.id "
        "WHERE l.mixxx_deleted = 0 AND tl.fs_deleted = 0"
    ):
        idx.setdefault(fname, []).append((tid, sr))
    return idx


def apply(collection: Path, db: Path = DB, dry_run: bool = False, playlists: bool = True) -> dict:
    if not collection.exists():
        raise RuntimeError(f"collection.nml not found at {collection}")
    if not db.exists():
        raise RuntimeError(f"Mixxx DB not found at {db} — start Mixxx once and let it scan the library")
    if not dry_run and mixxx_running():
        raise RuntimeError("Mixxx is running — quit it first (it holds the DB and rewrites tracks on exit).")

    root = ET.parse(collection).getroot()
    entries = [parse_entry(e) for e in root.iter("ENTRY") if e.find("LOCATION") is not None]

    report = {"updated": [], "not_in_mixxx": [], "ambiguous": [], "no_samplerate": [],
              "no_grid": [], "multi_grid": [], "skipped_cues": {}, "playlists": {}}
    if not dry_run:
        backup = db.with_name(f"mixxxdb.sqlite.bak-{time.strftime('%Y%m%d_%H%M%S')}")
        shutil.copy2(db, backup)
        report["backup"] = str(backup)

    con = sqlite3.connect(db)
    idx = _library_index(con)
    try:
        for e in entries:
            hits = idx.get(e["file"], [])
            if not hits:
                report["not_in_mixxx"].append(e["file"])
                continue
            if len(hits) > 1:
                report["ambiguous"].append(e["file"])
                continue
            tid, sr = hits[0]
            if not sr:
                report["no_samplerate"].append(e["file"])
                continue

            fields = {}
            if e["bpm"] and e["grid_ms"] is not None:
                beat_ms = 60000.0 / e["bpm"]
                anchor = e["grid_ms"]
                while anchor < 0:  # keep the anchor inside the track
                    anchor += beat_ms
                fields.update(bpm=e["bpm"], beats=beatgrid_blob(e["bpm"], _frames(anchor, sr)),
                              beats_version="BeatGrid-2.0", beats_sub_version="", bpm_lock=1)
                if e["grid_markers"] > 1:
                    report["multi_grid"].append(e["file"])
            else:
                report["no_grid"].append(e["file"])
            if e["key"] is not None:
                fields.update(key=key_text(e["key"]), key_id=e["key"] + 1,
                              keys=None, keys_version=None, keys_sub_version=None)

            cue_rows, skipped = map_cues(e["cues"], sr)
            if skipped:
                report["skipped_cues"][e["file"]] = skipped
            main = next((c for c in cue_rows if c["type"] == MAINCUE), None)
            if main:
                fields["cuepoint"] = main["position"]

            if fields:
                sets = ", ".join(f"{k} = ?" for k in fields)
                con.execute(f"UPDATE library SET {sets} WHERE id = ?", (*fields.values(), tid))
            if cue_rows:
                con.execute("DELETE FROM cues WHERE track_id = ? AND type IN (?, ?, ?)",
                            (tid, HOTCUE, MAINCUE, LOOP))
                con.executemany(
                    "INSERT INTO cues (track_id, type, position, length, hotcue, label, color) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    [(tid, c["type"], c["position"], c["length"], c["hotcue"], c["label"], COLOR[c["type"]])
                     for c in cue_rows])
            report["updated"].append({"file": e["file"], "bpm": e["bpm"],
                                      "key": fields.get("key"), "cues": len(cue_rows)})

        if playlists:
            for name, files in parse_playlists(root).items():
                ids = [idx[f][0][0] for f in files if len(idx.get(f, [])) == 1]
                row = con.execute("SELECT id FROM Playlists WHERE name = ? AND hidden = 0", (name,)).fetchone()
                if row:
                    pid = row[0]
                    con.execute("DELETE FROM PlaylistTracks WHERE playlist_id = ?", (pid,))
                    con.execute("UPDATE Playlists SET date_modified = CURRENT_TIMESTAMP WHERE id = ?", (pid,))
                else:
                    pos = con.execute("SELECT COALESCE(MAX(position), 0) + 1 FROM Playlists").fetchone()[0]
                    pid = con.execute(
                        "INSERT INTO Playlists (name, position, hidden, date_created, date_modified, locked) "
                        "VALUES (?, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0)", (name, pos)).lastrowid
                con.executemany(
                    "INSERT INTO PlaylistTracks (playlist_id, track_id, position, pl_datetime_added) "
                    "VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                    [(pid, tid, i + 1) for i, tid in enumerate(ids)])
                report["playlists"][name] = {"tracks": len(ids), "missing": len(files) - len(ids)}

        if dry_run:
            con.rollback()
        else:
            con.commit()
    finally:
        con.close()
    return report
