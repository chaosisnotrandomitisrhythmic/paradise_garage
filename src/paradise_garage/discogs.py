"""Discogs: the records Andreas owns, as the source of truth for their tags.

Two kinds of tracks live in the library:
  owned     on a release in his Discogs collection. Album, label, catalogue
            number, year, side position and cover come from *that* release,
            overwriting whatever Spotify said (`pg discogs pull`).
  the rest  Spotify data via `pg enrich`, filling only missing fields.

The sync both ways:
  pull   collection -> library: tag the files that are on an owned release and
         list the release tracks still missing (record from Spotify, or rip)
  push   library/purchases -> collection: add a release, one y/n per record

Auth is a personal access token (Discogs Settings -> Developers) in
DISCOGS_TOKEN, injected by `op run` like the Spotify keys. Discogs allows 60
authenticated requests a minute; release JSON is cached so reruns are cheap.
"""

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from mutagen.flac import FLAC

from .enrich import FRONT_COVER, _bare_title, _first, fold, write

API = "https://api.discogs.com"
USER_AGENT = "paradise_garage/0.1 +https://github.com/chaosisnotrandomitisrhythmic/paradise_garage"
CACHE = Path.home() / ".cache" / "paradise_garage" / "discogs"
VINYL_RIPS = Path(__file__).parent.parent.parent / "metadata" / "vinyl-rips.md"
ARTIST_IMAGES = Path.home() / "Music" / "ArtistImages"     # Navidrome ArtistImageFolder
ARTIST_RECORD = Path(__file__).parent.parent.parent / "metadata" / "artist-images.json"
DURATION_TOL = 15.0   # vinyl timings on Discogs are rough; beyond this it is another version
OWNED_FIELDS = ("album", "albumartist", "date", "label", "catalognumber", "media",
                "tracknumber", "discogs_position", "discogs_release_id", "owned")


def clean_name(name: str) -> str:
    """'Link (2)' -> 'Link': Discogs numbers artists and labels that share a name."""
    return re.sub(r"\s+\(\d+\)$", "", name or "").strip()


def join_artists(artists: list[dict]) -> str:
    out = ""
    for a in artists or []:
        out += clean_name(a.get("anv") or a.get("name", ""))
        join = (a.get("join") or "").strip()
        out += f" {join} " if join and join != "," else ", "
    return out.rstrip(", ").strip()


def parse_duration(s: str) -> float | None:
    """'6:36' -> 396.0, '1:02:03' -> 3723.0, '' -> None."""
    if not s or not re.fullmatch(r"\d+(:\d{1,2}){1,2}", s.strip()):
        return None
    secs = 0
    for part in s.strip().split(":"):
        secs = secs * 60 + int(part)
    return float(secs)


class Client:
    """Thin urllib client. `opener` is swappable so tests never touch the network."""

    def __init__(self, token: str | None = None, cache: Path = CACHE):
        self.token = token or os.environ.get("DISCOGS_TOKEN", "")
        if not self.token:
            raise RuntimeError("DISCOGS_TOKEN not set (run under `op run` with the Discogs token).")
        self.cache = cache
        self._user = None

    def _request(self, method: str, path: str, params: dict | None = None) -> tuple[int, bytes]:
        url = path if path.startswith("http") else API + path
        if params:
            url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v not in (None, "")})
        req = urllib.request.Request(url, method=method, headers={
            "Authorization": f"Discogs token={self.token}", "User-Agent": USER_AGENT})
        for attempt in range(5):
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    if r.headers.get("X-Discogs-Ratelimit-Remaining") == "0":
                        time.sleep(60)
                    return r.status, r.read()
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < 4:
                    time.sleep(10 * (attempt + 1))
                    continue
                raise
        raise RuntimeError(f"Discogs kept rate-limiting {url}")

    def get(self, path: str, **params) -> dict:
        return json.loads(self._request("GET", path, params)[1])

    def username(self) -> str:
        if self._user is None:
            self._user = self.get("/oauth/identity")["username"]
        return self._user

    def collection(self) -> list[dict]:
        """Every release in the collection (folder 0 = All), as basic_information dicts."""
        out, page = [], 1
        while True:
            d = self.get(f"/users/{self.username()}/collection/folders/0/releases",
                         per_page=100, page=page, sort="added", sort_order="asc")
            out += [r["basic_information"] for r in d.get("releases", [])]
            if page >= (d.get("pagination") or {}).get("pages", 1):
                return out
            page += 1

    def in_collection(self, release_id: int) -> bool:
        d = self.get(f"/users/{self.username()}/collection/releases/{release_id}")
        return bool(d.get("releases"))

    def release(self, release_id: int) -> dict:
        cached = self.cache / "releases" / f"{release_id}.json"
        if cached.exists():
            return json.loads(cached.read_text())
        d = self.get(f"/releases/{release_id}")
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_text(json.dumps(d))
        return d

    def search(self, query: str = "", **params) -> list[dict]:
        return self.get("/database/search", q=query, type="release", per_page=10, **params).get("results", [])

    def add_to_collection(self, release_id: int) -> None:
        self._request("POST", f"/users/{self.username()}/collection/folders/1/releases/{release_id}")

    def artist(self, artist_id: int) -> dict:
        cached = self.cache / "artists" / f"{artist_id}.json"
        if cached.exists():
            return json.loads(cached.read_text())
        d = self.get(f"/artists/{artist_id}")
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_text(json.dumps(d))
        return d

    def image(self, url: str) -> bytes:
        return self._request("GET", url)[1]

    def cover(self, rel: dict) -> bytes | None:
        images = rel.get("images") or []
        img = next((i for i in images if i.get("type") == "primary"), images[0] if images else None)
        if not img or not img.get("uri"):
            return None
        cached = self.cache / "covers" / f"{rel['id']}.jpg"
        if not cached.exists():
            cached.parent.mkdir(parents=True, exist_ok=True)
            cached.write_bytes(self._request("GET", img["uri"])[1])
        return cached.read_bytes()


# ---- a release, flattened ----------------------------------------------------

@dataclass
class RelTrack:
    position: str
    number: int          # 1-based order on the release (tracknumber)
    artist: str
    title: str
    duration: float | None


def tracks(rel: dict) -> list[RelTrack]:
    """Playable tracks in order; headings dropped, index tracks expanded."""
    rel_artist = join_artists(rel.get("artists"))
    flat = []
    for t in rel.get("tracklist") or []:
        kind = t.get("type_", "track")
        if kind == "index":
            flat += [dict(s, artists=s.get("artists") or t.get("artists")) for s in t.get("sub_tracks") or []]
        elif kind == "track":
            flat.append(t)
    out = []
    for i, t in enumerate(flat, 1):
        artist = join_artists(t.get("artists")) or rel_artist
        out.append(RelTrack(t.get("position", ""), i, artist, t.get("title", ""), parse_duration(t.get("duration", ""))))
    return out


def release_meta(rel: dict) -> dict:
    labels = rel.get("labels") or [{}]
    released = (rel.get("released") or "").replace("-00", "")
    artist = join_artists(rel.get("artists"))
    fmt = ((rel.get("formats") or [{}])[0].get("name") or "")
    return {
        "album": rel.get("title", ""),
        "albumartist": "Various Artists" if fold(artist) == "various" else artist,
        "date": released or str(rel.get("year") or ""),
        "label": clean_name(labels[0].get("name", "")),
        "catalognumber": labels[0].get("catno", "") if labels[0].get("catno", "").lower() != "none" else "",
        "media": fmt,
        "discogs_release_id": str(rel.get("id", "")),
        "owned": fmt.lower(),
    }


def describe(rel: dict) -> str:
    m = release_meta(rel)
    return f'{m["albumartist"]} – {m["album"]} ({m["label"]} {m["catalognumber"]}, {m["date"][:4]}, {m["media"]})'


# ---- matching release tracks to library files --------------------------------

@dataclass
class Placement:
    release: dict
    track: RelTrack
    path: Path | None = None
    note: str = ""                       # why not placed / what to review
    changed: list = field(default_factory=list)


def _artist_names(artist: str) -> set[str]:
    """'Luli E Lucina' -> {luli, lucina}: duos are often filed under one name."""
    parts = re.split(r",|&| feat\.? | ft\.? | vs\.? | and | e | y ", artist, flags=re.I)
    return {fold(a) for a in parts if a.strip()}


def _t(title: str) -> str:
    """Title key: '&' == 'and', '∞' == 'infinity'."""
    return fold(title.replace("&", " and ").replace("∞", "infinity"))


def _bare(title: str) -> str:
    return _bare_title(title.replace("&", " and ").replace("∞", "infinity"))


def library_index(paths: list[Path]) -> list[tuple[Path, set[str], str, str, float]]:
    out = []
    for p in paths:
        a = FLAC(p)
        artist, title = _first(a, "artist"), _first(a, "title")
        out.append((p, _artist_names(artist), _t(title), _bare(title), a.info.length))
    return out


def place(rt: RelTrack, lib) -> tuple[Path | None, str]:
    """(file, note) for one release track. Exact title before bare title; an
    artist must overlap; length is checked only when Discogs gives one."""
    want = _artist_names(rt.artist)
    by_artist = [e for e in lib if e[1] & want]
    for level, cands in (("exact", [e for e in by_artist if e[2] == _t(rt.title)]),
                         ("bare", [e for e in by_artist if e[3] == _bare(rt.title)])):
        if rt.duration:
            near = [e for e in cands if abs(e[4] - rt.duration) <= DURATION_TOL]
            if cands and not near:
                e = min(cands, key=lambda e: abs(e[4] - rt.duration))
                return None, f"length differs: {e[0].name} ({e[4] - rt.duration:+.0f}s) — another version?"
            cands = near
        if len(cands) == 1:
            return cands[0][0], "" if level == "exact" else f"title differs: {cands[0][0].name}"
        if len(cands) > 1:
            return None, "several files fit: " + "; ".join(e[0].name for e in cands[:3])
    return None, ""


def plan_owned(audio, meta: dict, rt: RelTrack, cover: bool) -> tuple[dict, list[str]]:
    values = dict(meta, tracknumber=str(rt.number), discogs_position=rt.position)
    changes = [f for f in OWNED_FIELDS if values.get(f) and _first(audio, f) != values[f]]
    if cover and _first(audio, "discogs_release_id") != values["discogs_release_id"]:
        changes.append("cover")
    elif cover and not any(p.type == FRONT_COVER for p in audio.pictures):
        changes.append("cover")
    return values, changes


def pull(client: Client, paths: list[Path], *, apply: bool = False, cover: bool = True,
         releases: list[dict] | None = None) -> list[Placement]:
    """Match every collection release track to the library; with apply, write the
    release's tags (overwriting Spotify's) and cover onto each placed file."""
    lib = library_index(paths)
    out, taken = [], {}
    for basic in releases if releases is not None else client.collection():
        rel = client.release(basic["id"])
        meta = release_meta(rel)
        art = None
        for rt in tracks(rel):
            pl = Placement(rel, rt)
            pl.path, pl.note = place(rt, lib)
            if pl.path and pl.path in taken:
                pl.note = f"already placed on {taken[pl.path]}"
                pl.path = None
            if pl.path:
                taken[pl.path] = describe(rel)
                values, pl.changed = plan_owned(FLAC(pl.path), meta, rt, cover)
                if apply and pl.changed:
                    if "cover" in pl.changed and art is None:
                        art = client.cover(rel) or b""
                    write(pl.path, values, pl.changed, art or None)
            out.append(pl)
    return out


def tag_file(client: Client, path: Path, release_id: int, position: str | None = None,
             cover: bool = True, owned: bool = True, apply: bool = True) -> tuple[RelTrack, list[str]]:
    """Tag one file straight from a release: a vinyl rip (`pg ingest --discogs ID
    --pos A2`, owned) or a better album for a Spotify rip (`pg discogs tag`, not
    owned: no `owned`/`media`). Without a position the track is found by title."""
    rel = client.release(release_id)
    rts = tracks(rel)
    if position:
        rt = next((t for t in rts if t.position.upper() == position.upper()), None)
    else:
        rt = next((t for t in rts if place(t, library_index([path]))[0]), None)
    if rt is None:
        raise ValueError(f"{'no position ' + position if position else 'no track like ' + path.name} on "
                         f"{describe(rel)}: " + ", ".join(f"{t.position} {t.title}" for t in rts))
    meta = release_meta(rel)
    if not owned:
        meta["owned"] = meta["media"] = ""
    values, changes = plan_owned(FLAC(path), meta, rt, cover)
    if not _first(FLAC(path), "artist"):
        values["artist"], values["title"] = rt.artist, rt.title
        changes += ["artist", "title"]
    if apply and changes:
        write(path, values, changes, client.cover(rel) if "cover" in changes else None)
    return rt, changes


# ---- what is still missing digitally ------------------------------------------

def on_spotify(sp, rt: RelTrack) -> str:
    """A Spotify URI for this release track, or ''. Title and artist must match;
    length only when Discogs has one."""
    first = rt.artist.split(",")[0].strip()
    q = f'track:"{rt.title}" artist:"{first}"'
    items = (sp.search(q=q, type="track", limit=10).get("tracks") or {}).get("items") or []
    for tr in items:
        if fold(first) not in {fold(a.get("name", "")) for a in tr.get("artists", [])}:
            continue
        if fold(tr["name"]) != fold(rt.title) and _bare_title(tr["name"]) != _bare_title(rt.title):
            continue
        if rt.duration and abs(tr["duration_ms"] / 1000 - rt.duration) > DURATION_TOL:
            continue
        return tr["uri"]
    return ""


def add_vinyl_rips(missing: list[Placement], path: Path = VINYL_RIPS) -> int:
    """Append not-on-Spotify release tracks to the rip list; skips ones already there."""
    text = path.read_text() if path.exists() else "# To rip from vinyl\n"
    known = fold(text)
    added, blocks = 0, {}
    for pl in missing:
        line = f"- [ ] {pl.track.position} {pl.track.artist} – {pl.track.title}"
        if pl.track.duration:
            line += f" ({int(pl.track.duration // 60)}:{int(pl.track.duration % 60):02d})"
        line += ": not on Spotify"
        if fold(f"{pl.track.artist}{pl.track.title}") in known:
            continue
        blocks.setdefault(describe(pl.release), []).append(line)
        added += 1
    if added:
        text = text.rstrip("\n") + "\n"
        for head, lines in blocks.items():
            text += f"\n### {head}\n\nFrom `pg discogs pull`.\n\n" + "\n".join(lines) + "\n"
        path.write_text(text)
    return added


# ---- artist pictures for Navidrome ---------------------------------------------

def _primary_image(images: list[dict] | None) -> str:
    images = images or []
    img = next((i for i in images if i.get("type") == "primary"), images[0] if images else None)
    return (img or {}).get("uri", "")


def _first_artist(name: str) -> str:
    """'Oklou, Casey MQ' -> 'Oklou': a combined credit gets its first artist's picture."""
    return re.split(r",|&| feat\.? | ft\.? | vs\.? | x ", name, maxsplit=1, flags=re.I)[0].strip()


def _ids_on(rel: dict) -> dict[str, int]:
    """fold(name) -> Discogs artist id, for every artist credited on a release."""
    out = {}
    for a in (rel.get("artists") or []) + [a for t in rel.get("tracklist") or [] for a in t.get("artists") or []]:
        if a.get("id"):
            for n in (a.get("name", ""), a.get("anv", "")):
                if n:
                    out.setdefault(fold(clean_name(n)), a["id"])
    return out


def library_artists(paths: list[Path]) -> dict[str, dict]:
    """Every artist / albumartist name in the library -> a title and release ids to look it up by."""
    out: dict[str, dict] = {}
    for p in paths:
        a = FLAC(p)
        rid = _first(a, "discogs_release_id")
        for field_ in ("artist", "albumartist"):
            name = _first(a, field_)
            if not name or fold(name) in ("variousartists", "various"):
                continue
            e = out.setdefault(name, {"titles": [], "releases": [], "files": []})
            if field_ == "artist":
                e["titles"].append(_first(a, "title"))
            e["files"].append(p)
            if rid and rid not in e["releases"]:
                e["releases"].append(rid)
    return out


def _search(client: Client, **params) -> list[dict]:
    """Database search, cached on disk: artist lookups rerun without re-asking Discogs."""
    cache = getattr(client, "cache", None)
    cached = cache / "searches" / (urllib.parse.urlencode(sorted(params.items())).replace("/", "_")[:200] + ".json") \
        if cache else None
    if cached and cached.exists():
        return json.loads(cached.read_text())
    res = client.get("/database/search", **params).get("results", [])
    if cached:
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_text(json.dumps(res))
    return res


def _short_title(title: str) -> str:
    """'Chime (Edit) - Remastered' -> 'Chime': what Discogs lists on the original."""
    return re.split(r"\s+[\(\[]|\s+-\s+", title, maxsplit=1)[0].strip()


def find_artist(client: Client, name: str, info: dict) -> tuple[int | None, str]:
    """(Discogs artist id, how it was found). Most certain first: the file's own
    release, then a release search by artist + track (full title, then short),
    then a name search: one exact hit, or else the one without a ' (n)' suffix,
    flagged for review. Tried for the full name, then its first artist."""
    names = [name] + ([_first_artist(name)] if _first_artist(name) != name else [])
    for n in names:
        for rid in info.get("releases", []):
            if (i := _ids_on(client.release(int(rid))).get(fold(n))):
                return i, f"release {rid}"
    for n in names:
        titles = info.get("titles", [])[:3]
        for title in dict.fromkeys(titles + [_short_title(t) for t in titles]):
            for hit in _search(client, type="release", artist=n, track=title, per_page=3)[:1]:
                if (i := _ids_on(client.release(hit["id"])).get(fold(n))):
                    return i, f"track search ({title} on release {hit['id']})"
    for n in names:
        hits = [h for h in _search(client, type="artist", q=n, per_page=10)
                if fold(clean_name(h.get("title", ""))) == fold(n)]
        if len(hits) == 1:
            return hits[0]["id"], "name search"
        plain = [h for h in hits if clean_name(h.get("title", "")) == h.get("title", "")]
        if len(plain) == 1:
            return plain[0]["id"], f"CHECK: {len(hits)} artists called {n}, took the unnumbered one"
        if hits:
            return None, f"{len(hits)} artists called {n}: pick one in library-picks.json → artists"
    return None, "not found"


def _album_cover(paths: list[Path]) -> bytes | None:
    """The front cover of the artist's first file that has one."""
    for p in paths:
        for pic in FLAC(p).pictures:
            if pic.type == FRONT_COVER:
                return pic.data
    return None


def image_path(name: str, folder: Path = ARTIST_IMAGES) -> Path:
    return folder / (name.replace("/", "_") + ".jpg")


def artist_images(client: Client, paths: list[Path], *, apply: bool = False, force: bool = False,
                  picks: dict | None = None, folder: Path = ARTIST_IMAGES,
                  record: Path = ARTIST_RECORD) -> list[dict]:
    """One Discogs picture per library artist, saved as <folder>/<artist name>.jpg
    for Navidrome's ArtistImageFolder. Lookups are kept in `record`, so reruns
    only search for new artists; a pick (name -> artist id) always wins."""
    picks = picks or {}
    known = json.loads(record.read_text()) if record.exists() else {}
    rows = []
    for name, info in sorted(library_artists(paths).items(), key=lambda kv: fold(kv[0])):
        row = {"name": name, "id": None, "how": "", "image": "", "status": ""}
        if name in picks:
            row["id"], row["how"] = int(picks[name]), "pick"
        elif known.get(name, {}).get("id"):
            row["id"], row["how"] = known[name]["id"], known[name]["how"]
        else:
            row["id"], row["how"] = find_artist(client, name, info)
        if row["id"]:
            art = client.artist(row["id"])
            row["discogs_name"] = art.get("name", "")
            row["image"] = _primary_image(art.get("images"))
        target = image_path(name, folder)
        if not row["image"]:
            # no Discogs picture: the cover of one of the artist's albums stands in
            cover = _album_cover(info.get("files", []))
            row["status"] = ("not found" if not row["id"] else "no image on Discogs") + (
                ", album cover" if cover else "")
            if cover and (force or not target.exists()):
                row["status"] += " written" if apply else " would be written"
                if apply:
                    folder.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(cover)
            elif cover:
                row["status"] += " kept"
        elif target.exists() and not force:
            row["status"] = "kept"
        else:
            row["status"] = "written" if apply else "would write"
            if apply:
                folder.mkdir(parents=True, exist_ok=True)
                target.write_bytes(client.image(row["image"]))
        if "/" in name:
            row["status"] += " (name has '/': Navidrome will not find the file)"
        rows.append(row)
        if row["id"]:
            known[name] = {k: row[k] for k in ("id", "how")} | {"discogs_name": row.get("discogs_name", "")}
    if apply:
        record.write_text(json.dumps(dict(sorted(known.items())), indent=1, ensure_ascii=False) + "\n")
    return rows
