"""Tests for the --skip-existing identity match in `pg record`.

macOS hands back filenames in decomposed Unicode (NFD) while Spotify titles are
composed (NFC). The match key has to treat both as the same track, or every
accented title is recorded again on a resumed run.
"""

import unicodedata

from paradise_garage.record import _match_key
from paradise_garage.spotify import track_filename
from paradise_garage.tag import parse_filename


def test_nfd_filename_matches_nfc_spotify_title():
    artist, title = "Os Mulheres Negras", "Só Quero Um Xodó"
    on_disk = unicodedata.normalize("NFD", track_filename(artist, title))
    a, t = parse_filename(on_disk)
    assert _match_key(a, t) == _match_key(artist, unicodedata.normalize("NFC", title))


def test_slash_in_title_still_matches_its_filename():
    artist, title = "Nando Carneiro", "G.R.E.S. Luxo Artesanal / O Camponês"
    a, t = parse_filename(unicodedata.normalize("NFD", track_filename(artist, title)))
    assert _match_key(a, t) == _match_key(artist, title)


def test_accent_folding_keeps_distinct_titles_distinct():
    assert _match_key("Marco Bosco", "Madeira I (Chuva)") != _match_key(
        "Marco Bosco", "Madeira II (Mãe Terra)"
    )
