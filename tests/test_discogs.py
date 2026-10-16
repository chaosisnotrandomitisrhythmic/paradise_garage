"""Tests for `pg discogs` and the `source` tag.

Owned records overwrite Spotify's album data; Traktor/playlist/comment tags
survive; pushes happen only after a yes. Discogs is a dict-backed fake.
"""

from pathlib import Path

import pytest
from mutagen.flac import FLAC

from paradise_garage import cli, discogs, enrich
from test_enrich import ART, FakeSpotify, make_flac, sp_track

COVER = b"\xff\xd8\xff\xe0discogs-cover"

VIRTUAL_DREAMS = {
    "id": 101, "title": "Virtual Dreams", "year": 2020, "released": "2020-07-00",
    "artists": [{"name": "Various", "join": ""}],
    "labels": [{"name": "Music From Memory", "catno": "MFM050"}],
    "formats": [{"name": "Vinyl", "qty": "3"}],
    "images": [{"type": "primary", "uri": "https://img/101"}],
    "tracklist": [
        {"type_": "heading", "title": "Side A"},
        {"type_": "track", "position": "A1", "title": "Oneski", "duration": "6:43",
         "artists": [{"name": "Richard H. Kirk"}]},
        {"type_": "track", "position": "A2", "title": "Isolation (Part Two)", "duration": "8:28",
         "artists": [{"name": "Pulusha"}]},
        {"type_": "track", "position": "B1", "title": "Arcadian", "duration": "",
         "artists": [{"name": "Link (2)"}]},
    ],
}


class FakeDiscogs(discogs.Client):
    def __init__(self, releases, collection_ids=()):
        self.releases = {r["id"]: r for r in releases}
        self.collection_ids = list(collection_ids)
        self.posted = []

    def release(self, release_id):
        return self.releases[int(release_id)]

    def collection(self):
        return [{"id": i} for i in self.collection_ids]

    def in_collection(self, release_id):
        return int(release_id) in self.collection_ids

    def add_to_collection(self, release_id):
        self.posted.append(int(release_id))
        self.collection_ids.append(int(release_id))

    def cover(self, rel):
        return COVER


@pytest.fixture
def lib(tmp_path):
    d = tmp_path / "flac"
    d.mkdir()
    return d


def test_tracks_flatten_and_names():
    ts = discogs.tracks(VIRTUAL_DREAMS)
    assert [t.position for t in ts] == ["A1", "A2", "B1"]
    assert ts[2].artist == "Link" and ts[0].duration == 403.0 and ts[2].duration is None
    meta = discogs.release_meta(VIRTUAL_DREAMS)
    assert meta["albumartist"] == "Various Artists" and meta["date"] == "2020-07"
    assert (meta["label"], meta["catalognumber"], meta["owned"]) == ("Music From Memory", "MFM050", "vinyl")


def test_pull_overwrites_spotify_album_keeps_the_rest(lib):
    f = make_flac(lib / "Richard H. Kirk - Oneski.flac", "Richard H. Kirk", "Oneski", seconds=400,
                  ALBUM="Entering Valhalla", TRAKTOR4="blob;;\x01", PLAYLIST="Ambient Set",
                  COMMENT="Camelot: 8A | Energy: low", SPOTIFY_URI="spotify:track:x")
    keep = {k: FLAC(f)[k] for k in ("TRAKTOR4", "PLAYLIST", "COMMENT", "SPOTIFY_URI", "ARTIST", "TITLE")}
    dc = FakeDiscogs([VIRTUAL_DREAMS], [101])

    [dry, *_] = discogs.pull(dc, [f])
    assert dry.path == f and "album" in dry.changed and "cover" in dry.changed
    assert FLAC(f)["album"] == ["Entering Valhalla"]

    discogs.pull(dc, [f], apply=True)
    a = FLAC(f)
    assert a["album"] == ["Virtual Dreams"] and a["catalognumber"] == ["MFM050"]
    assert a["owned"] == ["vinyl"] and a["discogs_position"] == ["A1"] and a["tracknumber"] == ["1"]
    assert [p.data for p in a.pictures] == [COVER]
    for k, v in keep.items():
        assert a[k] == v
    # a second pull changes nothing
    assert all(not pl.changed for pl in discogs.pull(dc, [f]) if pl.path)


def test_pull_reports_missing_and_other_versions(lib):
    f = make_flac(lib / "Richard H. Kirk - Oneski.flac", "Richard H. Kirk", "Oneski", seconds=300)
    link = make_flac(lib / "Link - Arcadian.flac", "Link", "Arcadian", seconds=5)
    pls = {pl.track.position: pl for pl in discogs.pull(FakeDiscogs([VIRTUAL_DREAMS], [101]), [f, link])}
    assert pls["A1"].path is None and pls["A1"].note.startswith("length differs")
    assert pls["A2"].path is None and pls["A2"].note == ""
    assert pls["B1"].path == link   # no Discogs length -> title + artist decide


def test_compilation_track_artist_must_match(lib):
    f = make_flac(lib / "Somebody - Oneski.flac", "Somebody", "Oneski", seconds=403)
    [a1, *_] = discogs.pull(FakeDiscogs([VIRTUAL_DREAMS], [101]), [f])
    assert a1.path is None


def test_enrich_leaves_owned_album_alone_and_sets_source(lib, tmp_path):
    f = make_flac(lib / "Richard H. Kirk - Oneski.flac", "Richard H. Kirk", "Oneski", seconds=403)
    discogs.pull(FakeDiscogs([VIRTUAL_DREAMS], [101]), [f], apply=True)
    t = sp_track("spotify:track:1", "Oneski", "Richard H. Kirk", 403000)
    enrich.enrich([f], FakeSpotify([t], {"Oneski": [t]}), apply=True, matches_path=tmp_path / "m.json",
                  harvest_dir=tmp_path / "none", fetch_cover=lambda m: ART)
    a = FLAC(f)
    assert a["album"] == ["Virtual Dreams"] and [p.data for p in a.pictures] == [COVER]
    assert a["spotify_uri"] == ["spotify:track:1"] and a["source"] == ["spotify"]


def test_existing_source_is_kept(lib, tmp_path):
    f = make_flac(lib / "A - One.flac", "A", "One", SOURCE="vinyl")
    t = sp_track("spotify:track:1", "One", "A", 2000)
    [m] = enrich.enrich([f], FakeSpotify([t], {"One": [t]}), apply=True, matches_path=tmp_path / "m.json",
                        harvest_dir=tmp_path / "none", fetch_cover=lambda m: ART)
    assert "source" not in m.changed and FLAC(f)["source"] == ["vinyl"]


def test_tag_file_by_position_for_a_rip(lib):
    f = make_flac(lib / "rip.flac", "", "")
    rt, changed = discogs.tag_file(FakeDiscogs([VIRTUAL_DREAMS]), f, 101, "a2")
    a = FLAC(f)
    assert rt.title == "Isolation (Part Two)" and "cover" in changed
    assert a["artist"] == ["Pulusha"] and a["discogs_position"] == ["A2"] and a["owned"] == ["vinyl"]


def test_tag_file_not_owned_has_no_owned_tag(lib):
    f = make_flac(lib / "Link - Arcadian.flac", "Link", "Arcadian")
    discogs.tag_file(FakeDiscogs([VIRTUAL_DREAMS]), f, 101, owned=False)
    a = FLAC(f)
    assert a["album"] == ["Virtual Dreams"] and "owned" not in a and "media" not in a


def test_push_only_after_yes(monkeypatch, capsys):
    dc = FakeDiscogs([VIRTUAL_DREAMS, dict(VIRTUAL_DREAMS, id=102)], [])
    monkeypatch.setattr(discogs, "Client", lambda: dc)
    answers = iter(["n", "y"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    cli.cmd_discogs(["push", "101", "102"])
    assert dc.posted == [102]
    cli.cmd_discogs(["push", "102"])            # already there: no question, no post
    assert dc.posted == [102] and "already" in capsys.readouterr().out


def test_add_vinyl_rips_skips_known_lines(tmp_path):
    rips = tmp_path / "vinyl-rips.md"
    rips.write_text("# To rip from vinyl\n\n- [ ] A2 Pulusha – Isolation (Part Two) (8:28): not on Spotify\n")
    pls = [discogs.Placement(VIRTUAL_DREAMS, t) for t in discogs.tracks(VIRTUAL_DREAMS)[1:]]
    assert discogs.add_vinyl_rips(pls, rips) == 1
    text = rips.read_text()
    assert text.count("Pulusha") == 1 and "B1 Link – Arcadian" in text and "MFM050" in text


def test_source_command(lib, capsys):
    f = make_flac(lib / "A - One.flac", "A", "One")
    cli.cmd_source(["soundcloud", str(f)])
    assert FLAC(f)["source"] == ["soundcloud"]
    cli.cmd_source(["myspace", str(f)])
    assert FLAC(f)["source"] == ["soundcloud"] and "Usage" in capsys.readouterr().out


def test_spelling_variants_match(lib):
    rel = dict(VIRTUAL_DREAMS, tracklist=[
        {"type_": "track", "position": "A1", "title": "Birds And Flutes", "artists": [{"name": "MLO"}]},
        {"type_": "track", "position": "E3", "title": "∞", "artists": [{"name": "Human Mesh Dance"}]},
        {"type_": "track", "position": "D3", "title": "E Foi", "artists": [{"name": "Luli E Lucina"}]},
    ])
    files = [make_flac(lib / "MLO - Birds & Flutes.flac", "MLO", "Birds & Flutes"),
             make_flac(lib / "human mesh dance - Infinity.flac", "human mesh dance", "Infinity"),
             make_flac(lib / "Lucina - E Foi.flac", "Lucina", "E Foi")]
    pls = discogs.pull(FakeDiscogs([rel], [101]), files)
    assert [pl.path for pl in pls] == files


# ---- artist pictures ---------------------------------------------------------

class FakeArtists(FakeDiscogs):
    """Releases plus artist pages and the two searches artist_images uses."""

    def __init__(self, releases, artists, track_hits=None, name_hits=None):
        super().__init__(releases)
        self.artists, self.track_hits, self.name_hits = artists, track_hits or {}, name_hits or {}
        self.searched = []

    def artist(self, artist_id):
        return self.artists[artist_id]

    def image(self, url):
        return b"img:" + url.encode()

    def get(self, path, **params):
        self.searched.append(params)
        if params.get("type") == "release":
            return {"results": [{"id": i} for i in self.track_hits.get((params["artist"], params["track"]), [])]}
        return {"results": self.name_hits.get(params["q"], [])}


def _art(i, name, img=True):
    return {"id": i, "name": name, "images": [{"type": "primary", "uri": f"https://img/a{i}"}] if img else []}


VD_IDS = dict(VIRTUAL_DREAMS, tracklist=[
    {"type_": "track", "position": "A1", "title": "Oneski", "artists": [{"name": "Richard H. Kirk", "id": 11}]},
    {"type_": "track", "position": "B1", "title": "Arcadian", "artists": [{"name": "Link (2)", "id": 22}]},
])


def test_artist_from_own_release_without_search(lib, tmp_path):
    make_flac(lib / "Link - Arcadian.flac", "Link", "Arcadian", DISCOGS_RELEASE_ID="101")
    dc = FakeArtists([VD_IDS], {22: _art(22, "Link (2)")})
    [row] = discogs.artist_images(dc, sorted(lib.glob("*.flac")), folder=tmp_path / "img",
                                  record=tmp_path / "rec.json")
    assert (row["id"], row["status"]) == (22, "would write") and dc.searched == []
    assert not (tmp_path / "img").exists() and not (tmp_path / "rec.json").exists()


def test_track_search_picks_the_right_namesake(lib, tmp_path):
    make_flac(lib / "Link - Arcadian.flac", "Link", "Arcadian")
    # a name search would find two "Link"s; the track search lands on the right one
    dc = FakeArtists([VD_IDS], {22: _art(22, "Link (2)")}, track_hits={("Link", "Arcadian"): [101]},
                     name_hits={"Link": [{"id": 21, "title": "Link"}, {"id": 22, "title": "Link (2)"}]})
    [row] = discogs.artist_images(dc, sorted(lib.glob("*.flac")), apply=True, folder=tmp_path / "img",
                                  record=tmp_path / "rec.json")
    assert row["id"] == 22 and row["how"].startswith("track search")
    assert (tmp_path / "img" / "Link.jpg").read_bytes() == b"img:https://img/a22"


def test_ambiguous_name_takes_unnumbered_or_asks_and_a_pick_wins(lib, tmp_path):
    make_flac(lib / "Link - Something.flac", "Link", "Something")
    hits = {"Link": [{"id": 21, "title": "Link"}, {"id": 22, "title": "Link (2)"}]}
    dc = FakeArtists([], {21: _art(21, "Link")}, name_hits=hits)
    kw = dict(folder=tmp_path / "img", record=tmp_path / "rec.json")
    [row] = discogs.artist_images(dc, sorted(lib.glob("*.flac")), **kw)
    assert row["id"] == 21 and row["how"].startswith("CHECK: 2 artists")   # the unnumbered one, flagged
    hits["Link"][0]["title"] = "Link (3)"
    [row] = discogs.artist_images(dc, sorted(lib.glob("*.flac")), **kw)
    assert row["id"] is None and row["status"] == "not found" and "2 artists" in row["how"]
    [row] = discogs.artist_images(dc, sorted(lib.glob("*.flac")), picks={"Link": 21}, **kw)
    assert (row["id"], row["how"]) == (21, "pick")


def test_combined_credit_uses_first_artist_and_various_is_skipped(lib, tmp_path):
    make_flac(lib / "Oklou, Casey MQ - Lurk.flac", "Oklou, Casey MQ", "Lurk", ALBUMARTIST="Various Artists")
    dc = FakeArtists([], {5: _art(5, "Oklou")}, name_hits={"Oklou": [{"id": 5, "title": "Oklou"}]})
    rows = discogs.artist_images(dc, sorted(lib.glob("*.flac")), folder=tmp_path / "img",
                                 record=tmp_path / "rec.json")
    assert [(r["name"], r["id"]) for r in rows] == [("Oklou, Casey MQ", 5)]


def test_existing_picture_kept_unless_forced_and_record_reused(lib, tmp_path):
    make_flac(lib / "Link - Arcadian.flac", "Link", "Arcadian", DISCOGS_RELEASE_ID="101")
    img = tmp_path / "img"
    img.mkdir()
    (img / "Link.jpg").write_bytes(b"mine")
    kw = dict(folder=img, record=tmp_path / "rec.json")
    dc = FakeArtists([VD_IDS], {22: _art(22, "Link (2)"), 23: _art(23, "Nope", img=False)})
    [row] = discogs.artist_images(dc, sorted(lib.glob("*.flac")), apply=True, **kw)
    assert row["status"] == "kept" and (img / "Link.jpg").read_bytes() == b"mine"
    [row] = discogs.artist_images(dc, sorted(lib.glob("*.flac")), apply=True, force=True, **kw)
    assert row["status"] == "written" and (img / "Link.jpg").read_bytes() == b"img:https://img/a22"
    # the record answers the second run: no release lookup needed
    dc.releases = {}
    [row] = discogs.artist_images(dc, sorted(lib.glob("*.flac")), **kw)
    assert row["id"] == 22 and row["how"] == "release 101"


def test_short_title_is_searched_too():
    assert discogs._short_title("Chime (Edit) - Remastered") == "Chime"
    assert discogs._short_title("The Shot! [Dub Copy]") == "The Shot!"


def test_no_discogs_picture_falls_back_to_album_cover(lib, tmp_path):
    f = make_flac(lib / "Nobody - Song.flac", "Nobody", "Song")
    a = FLAC(f)
    from mutagen.flac import Picture
    pic = Picture()
    pic.type, pic.mime, pic.data = 3, "image/jpeg", b"album-art"
    a.add_picture(pic)
    a.save()
    dc = FakeArtists([], {})
    kw = dict(folder=tmp_path / "img", record=tmp_path / "rec.json")
    [row] = discogs.artist_images(dc, [f], **kw)
    assert row["status"] == "not found, album cover would be written" and not (tmp_path / "img").exists()
    [row] = discogs.artist_images(dc, [f], apply=True, **kw)
    assert (tmp_path / "img" / "Nobody.jpg").read_bytes() == b"album-art"
