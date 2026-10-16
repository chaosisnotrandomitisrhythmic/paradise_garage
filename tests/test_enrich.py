"""Tests for `pg enrich` — album, date, label and cover art from Spotify.

Only missing fields are added; artist/title/analysis/playlist/Traktor tags must
come through byte-identical. Spotify is a dict-backed fake.
"""

import json
import subprocess

import pytest
from mutagen.flac import FLAC

from paradise_garage import enrich

ART = b"\xff\xd8\xff\xe0fake-jpeg"


def make_flac(path, artist, title, seconds=2.0, **tags):
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                    f"anullsrc=r=44100:cl=stereo", "-t", str(seconds), str(path)], check=True)
    audio = FLAC(path)
    audio["ARTIST"], audio["TITLE"] = artist, title
    for k, v in tags.items():
        audio[k] = v
    audio.save()
    return path


def sp_track(uri, name, artist, ms, album_id="alb1", album_type="album", date="1990-01-01"):
    return {"uri": uri, "name": name, "duration_ms": ms, "artists": [{"name": artist}],
            "track_number": 3, "disc_number": 1, "external_ids": {"isrc": "GBXX1"},
            "album": {"id": album_id, "album_type": album_type, "release_date": date, "name": album_id}}


class FakeSpotify:
    def __init__(self, tracks, search_results=None):
        self._tracks = {t["uri"]: t for t in tracks}
        self._search = search_results or {}
        self.searches = []

    def tracks(self, uris):
        return {"tracks": [self._tracks.get(u) for u in uris]}

    def albums(self, ids):
        return {"albums": [{"id": i, "name": f"Album {i}", "release_date": "1990-01-01",
                            "label": "Trax", "artists": [{"name": "Album Artist"}],
                            "images": [{"url": f"https://i/{i}", "width": 640}]} for i in ids]}

    def search(self, q, type, limit):
        self.searches.append(q)
        for needle, items in self._search.items():
            if needle in q:
                return {"tracks": {"items": items}}
        return {"tracks": {"items": []}}


@pytest.fixture
def lib(tmp_path):
    d = tmp_path / "flac"
    d.mkdir()
    return d


def run(paths, sp, tmp_path, **kw):
    kw.setdefault("harvest_dir", tmp_path / "no-harvest")
    return enrich.enrich(paths, sp, matches_path=tmp_path / "matches.json",
                         fetch_cover=lambda meta: ART, **kw)


def test_dry_run_writes_nothing(lib, tmp_path):
    f = make_flac(lib / "A - One.flac", "A", "One")
    before = f.read_bytes()
    sp = FakeSpotify([sp_track("spotify:track:1", "One", "A", 2000)],
                     {"One": [sp_track("spotify:track:1", "One", "A", 2000)]})
    [m] = run([f], sp, tmp_path)
    assert m.uri == "spotify:track:1" and m.source == "search"
    assert "album" in m.changed and "cover" in m.changed
    assert f.read_bytes() == before
    assert not (tmp_path / "matches.json").exists()


def test_apply_adds_fields_and_cover_keeps_everything_else(lib, tmp_path):
    f = make_flac(lib / "A - One.flac", "A", "One",
                  TRAKTOR4="blob;;\x01", PLAYLIST="Ambient Set", COMMENT="Camelot: 8A | Energy: low")
    keep = {k: FLAC(f)[k] for k in ("TRAKTOR4", "PLAYLIST", "COMMENT", "ARTIST", "TITLE")}
    sp = FakeSpotify([sp_track("spotify:track:1", "One", "A", 2000)],
                     {"One": [sp_track("spotify:track:1", "One", "A", 2000)]})
    run([f], sp, tmp_path, apply=True)

    audio = FLAC(f)
    assert audio["album"] == ["Album alb1"]
    assert audio["albumartist"] == ["Album Artist"]
    assert audio["date"] == ["1990-01-01"] and audio["label"] == ["Trax"]
    assert audio["spotify_uri"] == ["spotify:track:1"] and audio["tracknumber"] == ["3"]
    assert [p.type for p in audio.pictures] == [3] and audio.pictures[0].data == ART
    for k, v in keep.items():
        assert audio[k] == v
    saved = json.loads((tmp_path / "matches.json").read_text())["tracks"]
    assert saved["A - One.flac"]["uri"] == "spotify:track:1"


def test_second_run_changes_nothing_and_skips_search(lib, tmp_path):
    f = make_flac(lib / "A - One.flac", "A", "One")
    sp = FakeSpotify([sp_track("spotify:track:1", "One", "A", 2000)],
                     {"One": [sp_track("spotify:track:1", "One", "A", 2000)]})
    run([f], sp, tmp_path, apply=True)
    sp.searches.clear()
    [m] = run([f], sp, tmp_path, apply=True)
    assert m.source == "tag" and m.changed == [] and sp.searches == []
    assert len(FLAC(f).pictures) == 1


def test_existing_album_kept_unless_force(lib, tmp_path):
    f = make_flac(lib / "A - One.flac", "A", "One", ALBUM="My Own Title")
    sp = FakeSpotify([sp_track("spotify:track:1", "One", "A", 2000)],
                     {"One": [sp_track("spotify:track:1", "One", "A", 2000)]})
    run([f], sp, tmp_path, apply=True)
    assert FLAC(f)["album"] == ["My Own Title"]
    run([f], sp, tmp_path, apply=True, force=True)
    assert FLAC(f)["album"] == ["Album alb1"]


def test_source_priority_harvest_before_search(lib, tmp_path):
    f = make_flac(lib / "Bené - Dois.flac", "Bené", "Dois")
    hd = tmp_path / "harvested"
    hd.mkdir()
    (hd / "x.json").write_text(json.dumps({"tracks": [
        {"artist": "Bene", "title": "Dois", "duration_ms": 2000, "uri": "spotify:track:H"}]}))
    sp = FakeSpotify([sp_track("spotify:track:H", "Dois", "Bené", 2000)])
    [m] = run([f], sp, tmp_path, harvest_dir=hd)
    assert (m.uri, m.source) == ("spotify:track:H", "harvest")
    assert sp.searches == []


def test_search_prefers_album_over_compilation_and_checks_length(lib, tmp_path):
    f = make_flac(lib / "A - One.flac", "A", "One", seconds=120)
    items = [
        sp_track("spotify:track:comp", "One", "A", 120000, "c", "compilation", "1985-01-01"),
        sp_track("spotify:track:long", "One", "A", 300000, "l", "album", "1980-01-01"),
        sp_track("spotify:track:orig", "One", "A", 121000, "o", "album", "1991-01-01"),
    ]
    sp = FakeSpotify(items, {"One": items})
    [m] = run([f], sp, tmp_path)
    assert m.uri == "spotify:track:orig"


def test_loose_title_is_reported_not_written(lib, tmp_path):
    f = make_flac(lib / "A - One.flac", "A", "One", seconds=120)
    items = [sp_track("spotify:track:x", "One - 2011 Remaster", "A", 125000)]
    sp = FakeSpotify(items, {"One": items})
    [m] = run([f], sp, tmp_path, apply=True)
    assert m.uri == "" and m.note.startswith("near:")
    assert "album" not in FLAC(f)


def test_wrong_artist_is_not_matched(lib, tmp_path):
    f = make_flac(lib / "A - One.flac", "A", "One")
    items = [sp_track("spotify:track:x", "One", "Somebody Else", 2000)]
    [m] = run([f], FakeSpotify(items, {"One": items}), tmp_path)
    assert m.uri == "" and m.note == "no Spotify result"


def test_manual_uri_overrides_tag_with_force(lib, tmp_path):
    f = make_flac(lib / "A - One.flac", "A", "One", SPOTIFY_URI="spotify:track:wrong", ALBUM="Ibiza Hits")
    sp = FakeSpotify([sp_track("spotify:track:right", "One", "A", 2000, "orig")])
    [m] = run([f], sp, tmp_path, apply=True, force=True, override={"A - One.flac": "spotify:track:right"})
    assert m.source == "manual"
    assert FLAC(f)["spotify_uri"] == ["spotify:track:right"] and FLAC(f)["album"] == ["Album orig"]
