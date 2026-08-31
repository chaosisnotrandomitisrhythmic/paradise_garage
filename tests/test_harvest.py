"""Tests for `pg harvest` — the virtualized-list bookkeeping and the cache round-trip.

The scroll loop itself needs a real Chrome, so what is covered here is the part
that actually gets the tracklist right: folding recycled rows back into playlist
order. Everything else in scrape_ids is I/O.
"""

import json

import pytest

from paradise_garage import harvest


def test_merge_rows_orders_by_rowindex_not_scroll_order():
    """Rows arrive in scroll order; the tracklist must come out in playlist order."""
    by_index, fallback = {}, []
    # Third scroll window seen first, then the first — as happens when a harvest
    # resumes mid-list or the page restores a scroll position.
    harvest.merge_rows([(8, "c"), (9, "d")], by_index, fallback)
    harvest.merge_rows([(2, "a"), (3, "b")], by_index, fallback)
    assert harvest.ordered_ids(by_index, fallback) == ["a", "b", "c", "d"]


def test_merge_rows_dedupes_recycled_rows():
    """Overlapping scroll windows re-report the same index; count must not inflate."""
    by_index, fallback = {}, []
    assert harvest.merge_rows([(2, "a"), (3, "b")], by_index, fallback) == 2
    assert harvest.merge_rows([(3, "b"), (4, "c")], by_index, fallback) == 3
    assert harvest.ordered_ids(by_index, fallback) == ["a", "b", "c"]


def test_merge_rows_first_sighting_wins():
    """A recycled row mid-repaint can carry a stale index; don't overwrite."""
    by_index, fallback = {}, []
    harvest.merge_rows([(2, "real")], by_index, fallback)
    harvest.merge_rows([(2, "stale")], by_index, fallback)
    assert harvest.ordered_ids(by_index, fallback) == ["real"]


def test_merge_rows_falls_back_to_append_order_without_rowindex():
    """A page with no aria-rowindex still yields a list, in DOM order."""
    by_index, fallback = {}, []
    harvest.merge_rows([(0, "a"), (0, "b")], by_index, fallback)
    harvest.merge_rows([(0, "b"), (0, "c")], by_index, fallback)
    assert harvest.ordered_ids(by_index, fallback) == ["a", "b", "c"]


def test_slugify():
    assert harvest.slugify("Officer John Radio") == "officer-john-radio"
    assert harvest.slugify("Dirty Talk @ the Paradise Garage!") == "dirty-talk-the-paradise-garage"
    assert harvest.slugify("Café Tacvba Mix") == "cafe-tacvba-mix"
    assert harvest.slugify("!!!") == "harvest"


def test_is_harvest_ref_distinguishes_from_playlist_urls():
    assert harvest.is_harvest_ref("harvest:officer-john-radio")
    assert not harvest.is_harvest_ref("https://open.spotify.com/playlist/37i9dQZF1E4vq1cso24MIt")
    assert not harvest.is_harvest_ref("liked")
    # A .json path that does not exist is not a harvest ref.
    assert not harvest.is_harvest_ref("/nope/missing.json")


def test_load_harvest_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(harvest, "HARVEST_DIR", tmp_path)
    path = tmp_path / "officer-john-radio.json"
    path.write_text(
        json.dumps(
            {
                "name": "Officer John Radio",
                "source_url": "https://open.spotify.com/playlist/37i9dQZF1E4vq1cso24MIt",
                "tracks": [
                    {
                        "artist": "Officer John",
                        "title": "Pass",
                        "duration_ms": 384000,
                        "uri": "spotify:track:abc",
                        "isrc": "X",
                    }
                ],
            }
        )
    )
    name, tracks = harvest.load_harvest("harvest:officer-john-radio")
    assert name == "Officer John Radio"
    assert len(tracks) == 1
    assert tracks[0].artist == "Officer John"
    assert tracks[0].duration_sec == 384.0


def test_load_harvest_missing_points_at_the_fix(tmp_path, monkeypatch):
    monkeypatch.setattr(harvest, "HARVEST_DIR", tmp_path)
    with pytest.raises(FileNotFoundError, match="pg harvest"):
        harvest.load_harvest("harvest:never-scraped")


def test_get_playlist_tracks_routes_harvest_refs(tmp_path, monkeypatch):
    """The harvest ref must reach load_harvest without touching the Web API."""
    from paradise_garage import spotify

    monkeypatch.setattr(harvest, "HARVEST_DIR", tmp_path)
    monkeypatch.setattr(
        spotify, "_client", lambda: pytest.fail("harvest ref must not hit the Web API")
    )
    (tmp_path / "radio.json").write_text(
        json.dumps(
            {
                "name": "Radio",
                "tracks": [
                    {"artist": "A", "title": "T", "duration_ms": 1000, "uri": "spotify:track:x"}
                ],
            }
        )
    )
    name, tracks = spotify.get_playlist_tracks("harvest:radio")
    assert (name, len(tracks)) == ("Radio", 1)
