"""Tests for `pg traktor` cue-writing — the grid is always Traktor's own.

These cover the skip paths (no librosa/audio needed): a track Traktor hasn't
analyzed is skipped, never fabricated. The cue-writing path against an analyzed
grid needs a real FLAC + librosa and is exercised manually with --dry-run.
"""

from pathlib import Path

import pytest

from paradise_garage import traktor

# One analyzed entry (TEMPO + AutoGrid grid anchor) and one entry with no grid.
SAMPLE_NML = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<NML VERSION="20"><HEAD COMPANY="x" PROGRAM="Traktor"></HEAD>
<COLLECTION ENTRIES="2">
<ENTRY MODIFIED_DATE="2026/6/1" TITLE="Analyzed" ARTIST="A"><LOCATION DIR="/:m/:" FILE="Analyzed - Track.flac" VOLUME="Macintosh HD" VOLUMEID="Macintosh HD"></LOCATION>
<TEMPO BPM="124.000000" BPM_QUALITY="100.000000"></TEMPO>
<CUE_V2 NAME="AutoGrid" DISPL_ORDER="0" TYPE="4" START="100.000000" LEN="0.000000" REPEATS="-1" HOTCUE="-1"><GRID BPM="124.000000"></GRID></CUE_V2></ENTRY>
<ENTRY MODIFIED_DATE="2026/6/1" TITLE="NoGrid" ARTIST="B"><LOCATION DIR="/:m/:" FILE="NoGrid - Track.flac" VOLUME="Macintosh HD" VOLUMEID="Macintosh HD"></LOCATION></ENTRY>
</COLLECTION>
</NML>
"""

NOT_ANALYZED = "not analyzed in Traktor yet"


@pytest.fixture
def nml(tmp_path, monkeypatch):
    monkeypatch.setattr(traktor, "traktor_running", lambda: False)
    p = tmp_path / "collection.nml"
    p.write_text(SAMPLE_NML, encoding="utf-8")
    return p


def test_track_not_in_collection_is_skipped(nml):
    report = traktor.apply(["/x/Missing - Track.flac"], collection=nml, dry_run=True)
    assert len(report) == 1
    assert report[0]["action"] == "skipped"
    assert NOT_ANALYZED in report[0]["reason"]
    assert "Analyze (Async)" in report[0]["reason"]


def test_entry_without_grid_is_skipped(nml):
    report = traktor.apply(["/x/NoGrid - Track.flac"], collection=nml, dry_run=True)
    assert report[0]["action"] == "skipped"
    assert NOT_ANALYZED in report[0]["reason"]


def test_dry_run_does_not_write(nml):
    before = nml.read_text(encoding="utf-8")
    traktor.apply(["/x/NoGrid - Track.flac"], collection=nml, dry_run=True)
    assert nml.read_text(encoding="utf-8") == before


def test_no_fabricated_entry_helpers():
    # The librosa beatgrid CREATE path is gone — no entry/key fabrication helpers.
    assert not hasattr(traktor, "_build_entry")
    assert not hasattr(traktor, "musical_key_value")


def test_read_grid_requires_tempo_and_anchor():
    assert traktor._read_grid('<ENTRY></ENTRY>') is None
    assert traktor._read_grid('<TEMPO BPM="124.000000">') is None  # no AutoGrid anchor
    grid = traktor._read_grid(
        '<TEMPO BPM="124.000000"></TEMPO>'
        '<CUE_V2 NAME="AutoGrid" START="100.000000"></CUE_V2>'
    )
    assert grid == (124.0, 100.0)


def test_module_public_path_constant():
    # Sanity: the live collection path is unchanged and we never default-write it in tests.
    assert traktor.COLLECTION == (
        Path.home() / "Documents" / "Native Instruments" / "Traktor 4.5.0" / "collection.nml"
    )
