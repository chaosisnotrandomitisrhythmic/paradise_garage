"""Read a Spotify playlist's ordered tracklist via the Web API.

Auth reuses the same env creds + redirect URI as the spoti-tidal tool
(SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET). Only playlist-read scope is
needed here. The OAuth token is cached under ~/.cache/paradise_garage so the
browser consent happens once.
"""

import os
import re
from dataclasses import dataclass
from pathlib import Path

CACHE_PATH = Path.home() / ".cache" / "paradise_garage" / "spotify-token.json"
REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:47281/callback")
SCOPE = "playlist-read-private playlist-read-collaborative user-library-read"


@dataclass
class Track:
    artist: str
    title: str
    duration_ms: int
    uri: str          # spotify:track:...  (matches `id of current track` in AppleScript)
    isrc: str = ""

    @property
    def duration_sec(self) -> float:
        return self.duration_ms / 1000.0


def _client():
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth

    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError(
            "SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET not set in the environment "
            "(they load from 1Password via op inject in ~/.zshrc)."
        )

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    auth = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_path=str(CACHE_PATH),
        open_browser=True,
    )
    return spotipy.Spotify(auth_manager=auth)


def parse_playlist_id(url_or_uri: str) -> str:
    """Accept a playlist URL, spotify:playlist: URI, or bare id."""
    s = url_or_uri.strip()
    m = re.search(r"playlist[/:]([A-Za-z0-9]+)", s)
    if m:
        return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9]+", s):
        return s
    raise ValueError(f"Could not parse a playlist id from: {url_or_uri!r}")


def get_liked_tracks() -> tuple[str, list[Track]]:
    """Return ('Liked Songs', saved-library tracks, newest first). Needs the
    user-library-read scope (delete the token cache to re-consent if missing)."""
    sp = _client()
    tracks: list[Track] = []
    results = sp.current_user_saved_tracks(limit=50)
    while results:
        for item in results["items"]:
            tr = item.get("track")
            if not tr or tr.get("is_local") or not tr.get("uri"):
                continue
            if not tr["uri"].startswith("spotify:track:"):
                continue
            artist = ", ".join(a["name"] for a in tr.get("artists", []) if a.get("name"))
            tracks.append(
                Track(
                    artist=artist or "Unknown",
                    title=tr["name"],
                    duration_ms=int(tr["duration_ms"]),
                    uri=tr["uri"],
                    isrc=(tr.get("external_ids") or {}).get("isrc", ""),
                )
            )
        results = sp.next(results) if results.get("next") else None
    return "Liked Songs", tracks


def get_playlist_tracks(url_or_uri: str) -> tuple[str, list[Track]]:
    """Return (playlist_name, ordered list of Track), skipping local/unavailable
    items. The sentinel 'liked' reads the saved-tracks library instead."""
    if url_or_uri.strip().lower() in ("liked", "liked-songs", "liked songs"):
        return get_liked_tracks()
    sp = _client()
    pid = parse_playlist_id(url_or_uri)
    name = sp.playlist(pid, fields="name").get("name", pid)

    tracks: list[Track] = []
    results = sp.playlist_items(
        pid,
        fields="items(track(name,uri,duration_ms,is_local,artists(name),external_ids(isrc))),next",
        additional_types=("track",),
    )
    while results:
        for item in results["items"]:
            tr = item.get("track")
            if not tr or tr.get("is_local") or not tr.get("uri"):
                continue
            if not tr["uri"].startswith("spotify:track:"):
                continue  # episodes/podcasts
            artist = ", ".join(a["name"] for a in tr.get("artists", []) if a.get("name"))
            tracks.append(
                Track(
                    artist=artist or "Unknown",
                    title=tr["name"],
                    duration_ms=int(tr["duration_ms"]),
                    uri=tr["uri"],
                    isrc=(tr.get("external_ids") or {}).get("isrc", ""),
                )
            )
        results = sp.next(results) if results.get("next") else None

    return name, tracks


def track_filename(artist: str, title: str) -> str:
    """Build an `Artist - Title.flac` name that round-trips through tag.parse_filename.

    parse_filename splits on the FIRST ' - ', so a bare ' - ' inside the title
    would be mis-parsed. Collapse it into parens (your existing convention:
    ESG "Moody - Spaced Out" -> "ESG - Moody (Spaced Out).flac"). Also strip
    filesystem-illegal characters.
    """
    t = title
    if " - " in t:
        first, rest = t.split(" - ", 1)
        t = f"{first.strip()} ({rest.strip()})"
    name = f"{artist} - {t}"
    # '/' and ':' are filesystem-unsafe; map to '_' (NOT '-', which the parser
    # treats as a separator and would mis-split e.g. "AC/DC" -> "AC" / "DC ...").
    name = name.replace("/", "_").replace(":", "_").strip()
    return f"{name}.flac"
