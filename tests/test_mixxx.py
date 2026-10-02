"""Tests for `pg mixxx` — Traktor NML into an existing Mixxx library.

Mixxx owns the library rows; we only update tracks it already scanned, matched
by file name, so the NML's absolute Mac paths never matter.
"""

import sqlite3
import struct

import pytest

from paradise_garage import mixxx

SAMPLE_NML = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<NML VERSION="20"><HEAD COMPANY="x" PROGRAM="Traktor"></HEAD>
<COLLECTION ENTRIES="3">
<ENTRY TITLE="Analyzed" ARTIST="A"><LOCATION DIR="/:Users/:mini/:Music/:Library/:flac/:" FILE="A - Analyzed.flac" VOLUME="Macintosh HD"></LOCATION>
<TEMPO BPM="124.000000" BPM_QUALITY="100.000000"></TEMPO>
<MUSICAL_KEY VALUE="21"></MUSICAL_KEY>
<CUE_V2 NAME="AutoGrid" DISPL_ORDER="0" TYPE="4" START="100.000000" LEN="0.000000" REPEATS="-1" HOTCUE="-1"><GRID BPM="124.000000"></GRID></CUE_V2>
<CUE_V2 NAME="MIX IN" DISPL_ORDER="0" TYPE="0" START="1000.000000" LEN="0.000000" REPEATS="-1" HOTCUE="0"></CUE_V2>
<CUE_V2 NAME="Roll" DISPL_ORDER="0" TYPE="5" START="2000.000000" LEN="500.000000" REPEATS="-1" HOTCUE="3"></CUE_V2>
<CUE_V2 NAME="n.n." DISPL_ORDER="0" TYPE="0" START="3000.000000" LEN="0.000000" REPEATS="-1" HOTCUE="-1"></CUE_V2>
<CUE_V2 NAME="Load" DISPL_ORDER="0" TYPE="3" START="100.000000" LEN="0.000000" REPEATS="-1" HOTCUE="-1"></CUE_V2>
<CUE_V2 NAME="Fade" DISPL_ORDER="0" TYPE="1" START="50.000000" LEN="0.000000" REPEATS="-1" HOTCUE="-1"></CUE_V2>
</ENTRY>
<ENTRY TITLE="NoGrid" ARTIST="B"><LOCATION DIR="/:m/:" FILE="B - NoGrid.flac" VOLUME="Macintosh HD"></LOCATION></ENTRY>
<ENTRY TITLE="Missing" ARTIST="C"><LOCATION DIR="/:m/:" FILE="C - Missing.flac" VOLUME="Macintosh HD"></LOCATION></ENTRY>
</COLLECTION>
<PLAYLISTS><NODE TYPE="FOLDER" NAME="$ROOT"><SUBNODES COUNT="3">
<NODE TYPE="PLAYLIST" NAME="Feudal 2026"><PLAYLIST ENTRIES="3" TYPE="LIST" UUID="u1">
<ENTRY><PRIMARYKEY TYPE="TRACK" KEY="Macintosh HD/:Users/:mini/:Music/:Library/:flac/:B - NoGrid.flac"></PRIMARYKEY></ENTRY>
<ENTRY><PRIMARYKEY TYPE="TRACK" KEY="Macintosh HD/:Users/:mini/:Music/:Library/:flac/:A - Analyzed.flac"></PRIMARYKEY></ENTRY>
<ENTRY><PRIMARYKEY TYPE="TRACK" KEY="Macintosh HD/:m/:C - Missing.flac"></PRIMARYKEY></ENTRY>
</PLAYLIST></NODE>
<NODE TYPE="PLAYLIST" NAME="_RECORDINGS"><PLAYLIST ENTRIES="0" TYPE="LIST" UUID="u2"></PLAYLIST></NODE>
<NODE TYPE="FOLDER" NAME="History"><SUBNODES COUNT="1">
<NODE TYPE="PLAYLIST" NAME="History 2026-07-30"><PLAYLIST ENTRIES="0" TYPE="LIST" UUID="u3"></PLAYLIST></NODE>
</SUBNODES></NODE>
</SUBNODES></NODE></PLAYLISTS>
</NML>
"""

SR = 44100


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(mixxx, "mixxx_running", lambda: False)
    nml = tmp_path / "collection.nml"
    nml.write_text(SAMPLE_NML, encoding="utf-8")
    db = tmp_path / "mixxxdb.sqlite"
    con = sqlite3.connect(db)
    con.executescript("""
        CREATE TABLE track_locations (id INTEGER PRIMARY KEY, location TEXT, filename TEXT,
            directory TEXT, fs_deleted INTEGER DEFAULT 0);
        CREATE TABLE library (id INTEGER PRIMARY KEY, location INTEGER, samplerate INTEGER,
            bpm FLOAT, cuepoint INTEGER, mixxx_deleted INTEGER DEFAULT 0, key TEXT DEFAULT '',
            key_id INTEGER DEFAULT 0, keys BLOB, keys_version TEXT, keys_sub_version TEXT,
            beats BLOB, beats_version TEXT, beats_sub_version TEXT DEFAULT '', bpm_lock INTEGER DEFAULT 0);
        CREATE TABLE cues (id INTEGER PRIMARY KEY, track_id INTEGER, type INTEGER, position INTEGER,
            length INTEGER, hotcue INTEGER, label TEXT, color INTEGER);
        CREATE TABLE Playlists (id INTEGER PRIMARY KEY, name TEXT, position INTEGER, hidden INTEGER,
            date_created, date_modified, locked INTEGER);
        CREATE TABLE PlaylistTracks (id INTEGER PRIMARY KEY, playlist_id INTEGER, track_id INTEGER,
            position INTEGER, pl_datetime_added);
        INSERT INTO track_locations VALUES (1, '/home/x/Music/Library/flac/A - Analyzed.flac', 'A - Analyzed.flac', '', 0);
        INSERT INTO track_locations VALUES (2, '/home/x/Music/Library/flac/B - NoGrid.flac', 'B - NoGrid.flac', '', 0);
        INSERT INTO library (id, location, samplerate, bpm) VALUES (10, 1, 44100, 123.7);
        INSERT INTO library (id, location, samplerate, bpm) VALUES (11, 2, 44100, 98.0);
        INSERT INTO cues VALUES (1, 10, 1, 999, 0, 0, 'old', 0);
        INSERT INTO cues VALUES (2, 10, 6, 5000, 0, -1, '', 0);
    """)
    con.commit()
    con.close()
    return nml, db


def _decode_beatgrid(blob: bytes):
    # BeatGrid{1: Bpm{1: double, 2: source}, 2: Beat{1: frame, 3: source}} as hand-encoded
    assert blob[0] == 0x0A
    bpm_len = blob[1]
    bpm_msg = blob[2:2 + bpm_len]
    assert bpm_msg[0] == 0x09
    bpm = struct.unpack("<d", bpm_msg[1:9])[0]
    assert bpm_msg[9:] == b"\x10\x02"
    beat = blob[2 + bpm_len:]
    assert beat[0] == 0x12
    msg = beat[2:2 + beat[1]]
    assert msg[0] == 0x08
    frame, shift, i = 0, 0, 1
    while True:
        b = msg[i]
        frame |= (b & 0x7F) << shift
        i += 1
        shift += 7
        if not b & 0x80:
            break
    assert msg[i:] == b"\x18\x02"
    return bpm, frame


def test_grid_key_and_lock(env):
    nml, db = env
    mixxx.apply(nml, db=db)
    row = sqlite3.connect(db).execute(
        "SELECT bpm, beats, beats_version, bpm_lock, key, key_id, keys_version, cuepoint "
        "FROM library WHERE id = 10").fetchone()
    bpm, blob, version, lock, key, key_id, keys_version, cuepoint = row
    assert bpm == 124.0
    assert version == "BeatGrid-2.0" and lock == 1
    assert _decode_beatgrid(blob) == (124.0, round(0.1 * SR))
    assert key == "Am" and key_id == 22 and keys_version is None
    assert cuepoint == 2 * round(0.1 * SR)


def test_cues_slots_and_units(env):
    nml, db = env
    report = mixxx.apply(nml, db=db)
    cues = sqlite3.connect(db).execute(
        "SELECT type, position, length, hotcue, label FROM cues WHERE track_id = 10 ORDER BY type, hotcue"
    ).fetchall()
    assert cues == [
        (mixxx.HOTCUE, 2 * SR, 0, 0, "MIX IN"),
        (mixxx.HOTCUE, 2 * 3 * SR, 0, 8, ""),          # memory cue -> slot 8, "n.n." unlabeled
        (mixxx.MAINCUE, 2 * round(0.1 * SR), 0, -1, "Load"),
        (mixxx.LOOP, 2 * 2 * SR, 2 * round(0.5 * SR), 3, "Roll"),
        (6, 5000, 0, -1, ""),                          # analyzer intro cue kept
    ]
    assert report["skipped_cues"]["A - Analyzed.flac"] == ["Fade (type 1)"]


def test_reports_and_playlists(env):
    nml, db = env
    report = mixxx.apply(nml, db=db)
    assert report["not_in_mixxx"] == ["C - Missing.flac"]
    assert report["no_grid"] == ["B - NoGrid.flac"]
    assert report["playlists"] == {"Feudal 2026": {"tracks": 2, "missing": 1}}
    con = sqlite3.connect(db)
    order = [r[0] for r in con.execute(
        "SELECT track_id FROM PlaylistTracks ORDER BY position")]
    assert order == [11, 10]


def test_rerun_is_idempotent(env):
    nml, db = env
    mixxx.apply(nml, db=db)
    mixxx.apply(nml, db=db)
    con = sqlite3.connect(db)
    assert con.execute("SELECT COUNT(*) FROM cues WHERE track_id = 10").fetchone()[0] == 5
    assert con.execute("SELECT COUNT(*) FROM Playlists").fetchone()[0] == 1
    assert con.execute("SELECT COUNT(*) FROM PlaylistTracks").fetchone()[0] == 2


def test_dry_run_writes_nothing_and_makes_no_backup(env):
    nml, db = env
    before = db.read_bytes()
    report = mixxx.apply(nml, db=db, dry_run=True)
    assert db.read_bytes() == before
    assert "backup" not in report
    assert len(report["updated"]) == 2


def test_backup_made_before_write(env):
    nml, db = env
    before = db.read_bytes()
    report = mixxx.apply(nml, db=db)
    from pathlib import Path
    assert Path(report["backup"]).read_bytes() == before


def test_refuses_while_mixxx_running(env, monkeypatch):
    nml, db = env
    monkeypatch.setattr(mixxx, "mixxx_running", lambda: True)
    with pytest.raises(RuntimeError, match="quit it first"):
        mixxx.apply(nml, db=db)


def test_key_text():
    assert mixxx.key_text(0) == "C"
    assert mixxx.key_text(6) == "F#"
    assert mixxx.key_text(12) == "Cm"
    assert mixxx.key_text(23) == "Bm"
