"""Tests for `pg cues` — editorial hot cues snapped to the Mixxx grid."""

import sqlite3

from paradise_garage import cues, mixxx


def test_grid_anchor_roundtrip():
    blob = mixxx.beatgrid_blob(124.0, 48123)
    assert cues.grid_anchor_frame(blob) == 48123
    assert cues.grid_anchor_frame(None) == 0


def test_snap_to_bar():
    # 120 BPM -> 2 s bars, anchor at 0.5 s
    sec, n = cues.snap_to_bar(5.3, 0.5, 120.0)
    assert (sec, n) == (4.5, 2)
    assert cues.snap_to_bar(0.1, 0.5, 120.0) == (0.5, 0)
    assert cues.snap_to_bar(-3.0, 0.5, 120.0)[0] == 0.0  # never before the start


def test_propose_track_snaps_and_dedupes(monkeypatch):
    st = {"duration_sec": 300.0, "eff_end_sec": 290.0,
          "cues": [("IN", 1.1), ("MIX IN", 1.4), ("BREAK", 150.2), ("MIX OUT", 230.0)]}
    track = dict(pos=1, id=7, artist="A", title="T", bpm=120.0, samplerate=44100,
                 beats=mixxx.beatgrid_blob(120.0, 44100 // 2), beats_version="BeatGrid-2.0", location="x.flac")
    r = cues.propose_track(track, st=st)
    assert [c["label"] for c in r["cues"]] == ["IN", "BREAK", "MIX OUT"]  # MIX IN collided with IN
    assert [c["sec"] for c in r["cues"]] == [0.5, 150.5, 230.5]
    assert r["cues"][0]["slot"] == 0 and r["cues"][2]["slot"] == 3


def test_write_replaces_slots_1_to_4_only(tmp_path, monkeypatch):
    db = tmp_path / "mixxxdb.sqlite"
    con = sqlite3.connect(db)
    con.executescript("""
        CREATE TABLE library (id INTEGER PRIMARY KEY, cuepoint INTEGER);
        CREATE TABLE cues (id INTEGER PRIMARY KEY AUTOINCREMENT, track_id INTEGER, type INTEGER,
            position INTEGER, length INTEGER, hotcue INTEGER, label TEXT, color INTEGER);
        INSERT INTO library VALUES (7, 0);
        INSERT INTO cues (track_id, type, position, length, hotcue, label, color) VALUES
            (7, 1, 999, 0, 1, 'old pad 2', 1), (7, 1, 5000, 0, 8, 'memory', 1), (7, 2, 999, 0, -1, '', 1);
    """)
    con.commit(); con.close()
    monkeypatch.setattr(cues, "mixxx_running", lambda: False)
    prop = [{"id": 7, "samplerate": 44100, "cues": [
        {"label": "IN", "slot": 0, "sec": 1.0}, {"label": "MIX OUT", "slot": 3, "sec": 10.0}]}]
    rep = cues.write(prop, db=db)
    assert (rep["written"], rep["cues"]) == (1, 2)
    con = sqlite3.connect(db)
    rows = con.execute("SELECT type, position, hotcue, label, color FROM cues WHERE track_id = 7 ORDER BY type, hotcue").fetchall()
    assert rows == [
        (1, 2 * 44100, 0, "IN", cues.ROLE_COLOR["IN"]),
        (1, 2 * 441000, 3, "MIX OUT", cues.ROLE_COLOR["MIX OUT"]),
        (1, 5000, 8, "memory", 1),
        (2, 2 * 44100, -1, "", cues.ROLE_COLOR["IN"]),
    ]
    assert con.execute("SELECT cuepoint FROM library WHERE id = 7").fetchone()[0] == 2 * 44100
