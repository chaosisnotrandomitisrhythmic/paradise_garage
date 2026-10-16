"""Fill album, release date, label and cover art from Spotify into library FLACs.

`pg record` writes artist/title plus analysis tags only, so every player (Navidrome,
Mixxx, Traktor) shows "[Unknown Album]" and no artwork. This finds each file's
Spotify track and adds what is missing. It only ever *adds* the fields below and
the front cover; artist, title, BPM, key, COMMENT, PLAYLIST, GROUPING, ReplayGain
and Traktor's TRAKTOR4 blob are never touched (mutagen rewrites only the keys set).

Files on a record Andreas owns (`owned` tag, from `pg discogs pull`) keep their
Discogs album, label and cover; they only gain the Spotify link. A file with no
`source` tag is marked `source=spotify` (rips arrive via `pg ingest --source`).

Which Spotify track, best source first:
  tag       a SPOTIFY_URI already on the file (earlier run, or `pg record`)
  cache     metadata/spotify-matches.json from an earlier --apply
  harvest   a `pg harvest` tracklist (~/.cache/paradise_garage/harvested)
  playlist  --playlist URL: the exact versions that were recorded
  manual    --uri spotify:track:… for one file (fix a wrong pick, with --force)
  search    Spotify search, accepted only on an artist + title match within
            DURATION_TOL seconds; a looser title match is reported, never written
"""

import json
import re
import unicodedata
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from mutagen.flac import FLAC, Picture

FIELDS = ("album", "albumartist", "date", "tracknumber", "discnumber", "isrc", "label", "spotify_uri")
MATCHES_PATH = Path(__file__).parent.parent.parent / "metadata" / "spotify-matches.json"
COVER_CACHE = Path.home() / ".cache" / "paradise_garage" / "covers"
DURATION_TOL = 5.0
FRONT_COVER = 3
_ALBUM_RANK = {"album": 0, "single": 1, "compilation": 2}


def fold(s: str) -> str:
    """Lowercase, accents folded, only a-z0-9: 'Bené' == 'Bene', 'X (Mix)' == 'X - Mix'."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", s.lower())


def key(artist: str, title: str) -> str:
    return fold(artist.split(",")[0]) + "|" + fold(title)


def _bare_title(title: str) -> str:
    """Title without a version suffix: 'X (Original Mix)', 'X - 2011 Remaster' -> 'X'."""
    return fold(re.split(r"\s+-\s+|\s*[\(\[]", title, maxsplit=1)[0])


@dataclass
class Match:
    path: Path
    artist: str
    title: str
    uri: str = ""
    source: str = ""          # tag | cache | harvest | playlist | search
    note: str = ""            # why unmatched, or the near misses for review
    meta: dict = field(default_factory=dict)
    changed: list = field(default_factory=list)


def _first(audio, name: str) -> str:
    v = audio.get(name)
    return v[0] if v else ""


# ---- finding the Spotify track ----------------------------------------------

def harvest_index(harvest_dir: Path) -> dict[str, str]:
    idx = {}
    for p in sorted(harvest_dir.glob("*.json")):
        for t in json.loads(p.read_text()).get("tracks", []):
            if t.get("uri", "").startswith("spotify:track:"):
                idx[key(t["artist"], t["title"])] = t["uri"]
    return idx


def playlist_index(urls: list[str]) -> dict[str, str]:
    from .spotify import get_playlist_tracks

    idx = {}
    for url in urls:
        _, tracks = get_playlist_tracks(url)
        for t in tracks:
            idx[key(t.artist, t.title)] = t.uri
    return idx


def _album_order(tr: dict) -> tuple:
    alb = tr.get("album") or {}
    return (_ALBUM_RANK.get(alb.get("album_type", ""), 3), alb.get("release_date") or "9999")


def search(sp, artist: str, title: str, duration: float) -> tuple[str, str]:
    """(uri, note). uri is empty unless one result matches artist, title and length."""
    first = artist.split(",")[0].strip()
    q = f'track:"{title}" artist:"{first}"'
    items = (sp.search(q=q, type="track", limit=10).get("tracks") or {}).get("items") or []
    if not items:  # quotes are strict about punctuation; retry loosely
        items = (sp.search(q=f"{first} {title}", type="track", limit=10).get("tracks") or {}).get("items") or []

    def artist_ok(tr):
        return fold(first) in {fold(a.get("name", "")) for a in tr.get("artists", [])}

    exact, loose = [], []
    for tr in items:
        if not tr.get("uri", "").startswith("spotify:track:") or not artist_ok(tr):
            continue
        dt = abs(tr["duration_ms"] / 1000.0 - duration)
        if fold(tr["name"]) == fold(title) and dt <= DURATION_TOL:
            exact.append(tr)
        elif _bare_title(tr["name"]) == _bare_title(title):
            loose.append(f'{tr["name"]} [{(tr.get("album") or {}).get("name", "?")}, {dt:+.0f}s]')
    if exact:
        return sorted(exact, key=_album_order)[0]["uri"], ""
    if loose:
        return "", "near: " + "; ".join(loose[:3])
    return "", "no Spotify result"


def resolve(paths: list[Path], sp=None, *, harvest: dict | None = None,
            playlists: dict | None = None, cache: dict | None = None,
            override: dict | None = None) -> list[Match]:
    harvest, playlists, cache, override = harvest or {}, playlists or {}, cache or {}, override or {}
    out = []
    for p in paths:
        audio = FLAC(p)
        m = Match(path=p, artist=_first(audio, "artist"), title=_first(audio, "title"))
        k = key(m.artist, m.title)
        if p.name in override:
            m.uri, m.source = override[p.name], "manual"
        elif _first(audio, "spotify_uri"):
            m.uri, m.source = _first(audio, "spotify_uri"), "tag"
        elif cache.get(p.name, {}).get("uri"):
            m.uri, m.source = cache[p.name]["uri"], "cache"
        elif k in harvest:
            m.uri, m.source = harvest[k], "harvest"
        elif k in playlists:
            m.uri, m.source = playlists[k], "playlist"
        elif sp is not None and m.artist and m.title:
            m.uri, m.note = search(sp, m.artist, m.title, audio.info.length)
            m.source = "search" if m.uri else ""
        else:
            m.note = "no artist/title tag" if not (m.artist and m.title) else "not searched"
        out.append(m)
    return out


# ---- metadata from Spotify ---------------------------------------------------

def fetch_meta(sp, uris: list[str]) -> dict[str, dict]:
    """uri -> the tag values to write, plus cover_url / cover_id for the artwork."""
    uris = list(dict.fromkeys(u for u in uris if u))
    tracks = {}
    for i in range(0, len(uris), 50):
        for tr in sp.tracks(uris[i:i + 50]).get("tracks", []):
            if tr:
                tracks[tr["uri"]] = tr
    album_ids = list(dict.fromkeys(tr["album"]["id"] for tr in tracks.values() if tr.get("album")))
    albums = {}
    for i in range(0, len(album_ids), 20):
        for a in sp.albums(album_ids[i:i + 20]).get("albums", []):
            if a:
                albums[a["id"]] = a

    meta = {}
    for uri, tr in tracks.items():
        alb = albums.get(tr["album"]["id"], tr["album"])
        images = sorted(alb.get("images") or [], key=lambda im: im.get("width") or 0, reverse=True)
        meta[uri] = {
            "album": alb.get("name", ""),
            "albumartist": ", ".join(a["name"] for a in alb.get("artists", []) if a.get("name")),
            "date": alb.get("release_date", ""),
            "tracknumber": str(tr.get("track_number") or ""),
            "discnumber": str(tr.get("disc_number") or ""),
            "isrc": (tr.get("external_ids") or {}).get("isrc", ""),
            "label": alb.get("label", ""),
            "spotify_uri": uri,
            "cover_url": images[0]["url"] if images else "",
            "cover_size": (images[0].get("width") or 0) if images else 0,
            "cover_id": alb.get("id", ""),
            "album_type": alb.get("album_type", ""),
        }
    return meta


def cover_bytes(meta: dict) -> bytes | None:
    if not meta.get("cover_url"):
        return None
    COVER_CACHE.mkdir(parents=True, exist_ok=True)
    cached = COVER_CACHE / f"{meta['cover_id'] or fold(meta['album'])}.jpg"
    if not cached.exists():
        with urllib.request.urlopen(meta["cover_url"], timeout=30) as r:
            cached.write_bytes(r.read())
    return cached.read_bytes()


# ---- writing -----------------------------------------------------------------

def plan_changes(audio, meta: dict, force: bool = False, cover: bool = True) -> list[str]:
    """Fields (and 'cover') this file would gain. Existing values stay unless force.
    A file on an owned record (`pg discogs pull`) keeps its Discogs album data and
    cover; it only gains the Spotify link. Files without a `source` are marked
    spotify: everything else arrives through `pg ingest --source`."""
    owned = bool(_first(audio, "owned"))
    fields = ("isrc", "spotify_uri") if owned else FIELDS
    changes = [f for f in fields if meta.get(f) and (force or not _first(audio, f))]
    if not _first(audio, "source"):
        changes.append("source")
    has_front = any(p.type == FRONT_COVER for p in audio.pictures)
    if cover and not owned and meta.get("cover_url") and (force or not has_front):
        changes.append("cover")
    return changes


def write(path: Path, meta: dict, changes: list[str], art: bytes | None) -> None:
    audio = FLAC(path)
    for f in changes:
        if f == "source":
            audio["source"] = meta.get("source", "spotify")
        elif f != "cover":
            audio[f] = meta[f]
    if "cover" in changes and art:
        keep = [p for p in audio.pictures if p.type != FRONT_COVER]
        audio.clear_pictures()
        for p in keep:
            audio.add_picture(p)
        pic = Picture()
        pic.type, pic.mime, pic.desc = FRONT_COVER, "image/jpeg", "Front cover"
        pic.width = pic.height = meta.get("cover_size") or 0
        pic.depth = 24
        pic.data = art
        audio.add_picture(pic)
    audio.save()


def load_matches(path: Path = MATCHES_PATH) -> dict:
    return json.loads(path.read_text()).get("tracks", {}) if path.exists() else {}


def save_matches(matches: list[Match], path: Path = MATCHES_PATH) -> None:
    data = load_matches(path)
    for m in matches:
        if m.uri:
            data[m.path.name] = {"uri": m.uri, "album": m.meta.get("album", ""), "source": m.source}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"tracks": dict(sorted(data.items())),
                                "updated": datetime.now().isoformat(timespec="seconds")},
                               indent=1, ensure_ascii=False) + "\n")


def enrich(paths: list[Path], sp, *, apply: bool = False, force: bool = False, cover: bool = True,
           harvest_dir: Path | None = None, playlist_urls: list[str] | None = None,
           matches_path: Path = MATCHES_PATH, fetch_cover=cover_bytes,
           override: dict | None = None) -> list[Match]:
    from .harvest import HARVEST_DIR

    matches = resolve(
        paths, sp,
        harvest=harvest_index(harvest_dir or HARVEST_DIR),
        playlists=playlist_index(playlist_urls) if playlist_urls else {},
        cache=load_matches(matches_path),
        override=override,
    )
    meta = fetch_meta(sp, [m.uri for m in matches]) if sp is not None else {}
    for m in matches:
        if not m.uri:
            continue
        m.meta = meta.get(m.uri, {})
        if not m.meta:
            m.note, m.uri, m.source = f"Spotify has no track {m.uri}", "", ""
            continue
        m.changed = plan_changes(FLAC(m.path), m.meta, force=force, cover=cover)
        if apply and m.changed:
            write(m.path, m.meta, m.changed, fetch_cover(m.meta) if "cover" in m.changed else None)
    if apply:
        save_matches(matches, matches_path)
    return matches


def apply_known(path: str | Path, uri: str) -> None:
    """Recording-time hook: the track's URI is known, so tag it straight away.
    Never raises: a Spotify hiccup must not stop a recording run."""
    try:
        from .spotify import _app_client

        sp = _app_client()
        meta = fetch_meta(sp, [uri]).get(uri)
        if not meta:
            print(f"    ! enrich: Spotify has no track {uri}")
            return
        p = Path(path)
        changes = plan_changes(FLAC(p), meta)
        if changes:
            write(p, meta, changes, cover_bytes(meta) if "cover" in changes else None)
            print(f"    + album: {meta['album']} ({meta['date'][:4]})")
    except Exception as e:  # noqa: BLE001
        print(f"    ! enrich skipped ({e.__class__.__name__}: {e})")
