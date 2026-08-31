"""Harvest an algorithmic Spotify playlist (Radio / personal Mix) into a local tracklist.

Playlist ids starting `37i9dQZF1E4…` are first-party-only: the Web API 404s them
for third-party apps even with a valid user token, so `pg record <radio-url>`
cannot resolve them. The open.spotify.com page *does* render the full tracklist,
but it is a virtualized list — programmatic `scrollTop` is ignored and the rows
stay pinned at the initial window, which is why hand-scraping it was never worth
the trouble.

So we drive a real Chrome over the DevTools Protocol and dispatch genuine
`Input.dispatchMouseEvent` wheel events, which the page cannot distinguish from
the user's own trackpad. Between scrolls we harvest whatever rows are currently
mounted, keyed by `aria-rowindex` so recycled rows still land in the right slot.

Only *ids* come out of the DOM. Artist, title and exact `duration_ms` then come
from the Web API's `/v1/tracks`, which is not restricted — the restriction is on
reading the *playlist*, not the tracks in it. That keeps the scrape robust to UI
copy changes and gives `pg record` the sample-accurate durations its boundary
detection and split windows depend on.

The result is written to ~/.cache/paradise_garage/harvested/<slug>.json and is
consumed by `pg record harvest:<slug>`, so everything downstream — the playlist
Vorbis tag, --skip-existing, the Traktor crate — behaves as if it were an
ordinary playlist.

⚠️ Run this as a discrete step, never during a recording run: loading the web
player registers the browser as a Spotify Connect device, which is the exact
condition that wedges the AppleScript tap. The harvester closes its own tab and
never presses play, but check that Spotify desktop is still the active device
before you record.
"""

import asyncio
import json
import re
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

from .spotify import CACHE_PATH, Track, _client

HARVEST_DIR = CACHE_PATH.parent / "harvested"

# Rows currently mounted in the virtualized list, as [aria-rowindex, track id].
# `aria-rowindex` is 1-based and counts the header, so track N has rowindex N+1.
_ROWS_JS = """
JSON.stringify(Array.from(document.querySelectorAll('div[role="row"]')).map(r => {
  const a = r.querySelector('a[href*="/track/"]');
  if (!a) return null;
  const m = (a.getAttribute('href') || '').match(/\\/track\\/([A-Za-z0-9]+)/);
  if (!m) return null;
  const idx = parseInt(r.getAttribute('aria-rowindex') || '0', 10);
  return [idx, m[1]];
}).filter(Boolean))
"""

# Must be scoped to the main region: the first h1 in the document is the
# sidebar's "Your Library", which is how the first harvest got named.
_TITLE_JS = """
(() => {
  const m = document.querySelector('main h1, [role="main"] h1');
  if (m && m.textContent.trim()) return m.textContent.trim();
  return (document.title || '').replace(/\\s*[|·]\\s*Spotify.*$/i, '').trim();
})()
"""

# Best-effort "N songs" for a coverage warning; Spotify localises and restyles
# this constantly, so a miss is not an error.
_COUNT_JS = """
(() => {
  const m = (document.body.innerText || '').match(/([\\d.,\\u202f\\u00a0]+)\\s+(songs?|canciones|Titel)/i);
  return m ? m[1].replace(/[^\\d]/g, '') : '';
})()
"""


def slugify(name: str) -> str:
    """Filesystem-safe slug for a harvest cache filename."""
    s = unicodedata.normalize("NFKD", name)
    s = s.encode("ascii", "ignore").decode("ascii").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "harvest"


def harvest_path(slug: str) -> Path:
    return HARVEST_DIR / f"{slug}.json"


def is_harvest_ref(ref: str) -> bool:
    """True for `harvest:<slug>` or a path to a harvest JSON file."""
    s = ref.strip()
    if s.lower().startswith("harvest:"):
        return True
    return s.endswith(".json") and Path(s).expanduser().is_file()


def _resolve_ref(ref: str) -> Path:
    s = ref.strip()
    if s.lower().startswith("harvest:"):
        return harvest_path(s.split(":", 1)[1].strip())
    return Path(s).expanduser()


def load_harvest(ref: str) -> tuple[str, list[Track]]:
    """Load a harvested tracklist as (playlist_name, ordered tracks)."""
    path = _resolve_ref(ref)
    if not path.is_file():
        raise FileNotFoundError(
            f"No harvest at {path}. Run: pg harvest <playlist-url>"
        )
    data = json.loads(path.read_text())
    tracks = [
        Track(
            artist=t["artist"],
            title=t["title"],
            duration_ms=int(t["duration_ms"]),
            uri=t["uri"],
            isrc=t.get("isrc", ""),
        )
        for t in data["tracks"]
    ]
    return data["name"], tracks


def merge_rows(
    rows: list[tuple[int, str]], by_index: dict[int, str], fallback: list[str]
) -> int:
    """Fold one round of harvested rows into the accumulators; return the running total.

    Virtualization recycles row elements, so the same DOM node holds a different
    track after each scroll. `aria-rowindex` is the list's true position, which
    is what keeps the tracklist in playlist order rather than scroll order. The
    first sighting of an index wins — a recycled row mid-repaint can briefly
    carry a stale index. `fallback` covers a page that renders no rowindex at
    all, where append-order is the best available signal.
    """
    for idx, tid in rows:
        if idx > 0:
            by_index.setdefault(idx, tid)
        elif tid not in fallback:
            fallback.append(tid)
    return len(by_index) or len(fallback)


def ordered_ids(by_index: dict[int, str], fallback: list[str]) -> list[str]:
    """Harvested ids in playlist order."""
    return [by_index[k] for k in sorted(by_index)] if by_index else list(fallback)


def hydrate(ids: list[str]) -> list[Track]:
    """Turn ordered track ids into Tracks via the Web API (50 per request).

    Unavailable ids come back as null and are dropped, matching how
    get_playlist_tracks skips local/unplayable items.
    """
    sp = _client()
    out: list[Track] = []
    for i in range(0, len(ids), 50):
        batch = ids[i : i + 50]
        for tr in sp.tracks(batch).get("tracks", []):
            if not tr or not tr.get("uri", "").startswith("spotify:track:"):
                continue
            artist = ", ".join(a["name"] for a in tr.get("artists", []) if a.get("name"))
            out.append(
                Track(
                    artist=artist or "Unknown",
                    title=tr["name"],
                    duration_ms=int(tr["duration_ms"]),
                    uri=tr["uri"],
                    isrc=(tr.get("external_ids") or {}).get("isrc", ""),
                )
            )
    return out


async def scrape_ids(
    url: str,
    *,
    port: int | None = None,
    delta: int = 900,
    settle: float = 0.45,
    idle_rounds: int = 4,
    max_rounds: int = 400,
    verbose: bool = True,
) -> tuple[str, list[str], str]:
    """Wheel-scroll the playlist page, returning (page_title, ordered ids, count_text).

    With `port`, attach to a dedicated debug Chrome (the `fastcdp-setup` "CDP
    Chrome" launcher, default 9223) instead of your everyday browser. That is
    what the mini uses: a separate profile, no per-connection approval prompt,
    and nothing disturbed in the browser you are actually using.

    Stops once `idle_rounds` consecutive scrolls surface no new track, which is
    both the bottom of the list and the failure mode of a list that never
    virtualized in the first place.
    """
    from fastcdp import CDP, Page

    cdp = await CDP.remote(port=port) if port else None
    # Page.new(cdp=…) does not own the connection, so we close it ourselves.
    page = await (Page.new(cdp=cdp) if cdp else Page.new())
    try:
        await page.goto(url, wait="load")
        # The row grid mounts after the initial paint.
        await page.wait_for("document.querySelectorAll('div[role=\"row\"]').length > 1", timeout=30)

        title = await page.eval(_TITLE_JS)
        count_text = await page.eval(_COUNT_JS)
        w = await page.eval("window.innerWidth")
        h = await page.eval("window.innerHeight")
        x, y = int(w) // 2, int(h) // 2

        by_index: dict[int, str] = {}
        fallback: list[str] = []  # used only if aria-rowindex is absent
        idle = 0
        for rnd in range(max_rounds):
            before = merge_rows(json.loads(await page.eval(_ROWS_JS)), by_index, fallback)

            await page.input.dispatchMouseEvent(
                type="mouseWheel", x=x, y=y, deltaX=0, deltaY=delta
            )
            await asyncio.sleep(settle)

            after = merge_rows(json.loads(await page.eval(_ROWS_JS)), by_index, fallback)
            idle = idle + 1 if after == before else 0
            if verbose and rnd % 5 == 0:
                print(f"  scroll {rnd:>3}  tracks {after}")
            if idle >= idle_rounds:
                break

        return title, ordered_ids(by_index, fallback), count_text
    finally:
        # Leave no Spotify Connect device behind.
        await page.close()
        if cdp:
            await cdp.close()


def harvest(url: str, *, name: str | None = None, verbose: bool = True, **kwargs) -> Path:
    """Scrape `url`, hydrate via the Web API, and cache the tracklist. Returns its path."""
    title, ids, count_text = asyncio.run(scrape_ids(url, verbose=verbose, **kwargs))
    if not ids:
        raise RuntimeError(
            f"No tracks found at {url}. Is Chrome signed in to Spotify, and is "
            "this actually a playlist page?"
        )

    expected = int(count_text) if count_text.isdigit() else None
    if expected and len(ids) < expected:
        print(
            f"  ⚠️  page says {expected} songs, harvested {len(ids)} — "
            "re-run, or raise --max-rounds"
        )

    tracks = hydrate(ids)
    playlist_name = name or title or "Harvested"
    slug = slugify(playlist_name)
    path = harvest_path(slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "name": playlist_name,
                "source_url": url,
                "harvested_at": datetime.now(UTC).isoformat(timespec="seconds"),
                "scraped_ids": len(ids),
                "tracks": [
                    {
                        "artist": t.artist,
                        "title": t.title,
                        "duration_ms": t.duration_ms,
                        "uri": t.uri,
                        "isrc": t.isrc,
                    }
                    for t in tracks
                ],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    if len(tracks) < len(ids):
        print(f"  {len(ids) - len(tracks)} track(s) unavailable in your market — dropped")
    return path
