import re
from pathlib import Path
from mutagen.flac import FLAC

from .loudness import replaygain_fields


def parse_filename(path: str) -> tuple[str, str]:
    # Split on the FIRST spaced ' - ' (the track_filename contract). The dash
    # must have whitespace on both sides — a bare hyphen is part of the name
    # (e.g. 'K-Lone - slk' is artist 'K-Lone', not artist 'K').
    stem = Path(path).stem
    match = re.match(r"^(.+?)\s+-\s+(.+)$", stem)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return "", stem


def write_tags(
    path: str,
    analysis: dict,
    artist: str = "",
    title: str = "",
    playlists: list[str] | None = None,
):
    audio = FLAC(path)

    if artist:
        audio["artist"] = artist
    if title:
        audio["title"] = title

    audio["bpm"] = str(analysis["bpm"])
    audio["initialkey"] = f"{analysis['key']} {analysis['mode']}"
    audio["comment"] = f"Camelot: {analysis['camelot']} | Energy: {analysis['energy']}"

    # Rekordbox reads these Vorbis comment fields
    audio["camelot"] = analysis["camelot"]
    audio["energy"] = analysis["energy"]

    # Loudness: store ReplayGain (for play-time leveling) + raw LUFS. The audio
    # itself is left at native level — we never normalize the file.
    if analysis.get("lufs") is not None:
        audio["lufs"] = str(analysis["lufs"])
        for k, v in replaygain_fields(analysis["lufs"], analysis.get("true_peak_dbtp")).items():
            audio[k] = v

    # Playlist provenance as a MULTI-VALUE tag — a track can belong to many
    # playlists (virtual crates, no folder duplication). Union with what's
    # already on the file so re-ingesting from another playlist accumulates.
    if playlists:
        merged = sorted({*audio.get("playlist", []), *playlists})
        audio["playlist"] = merged
        # mirror into GROUPING so rekordbox/Traktor show it in a column
        audio["grouping"] = "; ".join(merged)

    audio.save()


def read_tags(path: str) -> dict:
    audio = FLAC(path)
    return {
        "artist": audio.get("artist", [""])[0],
        "title": audio.get("title", [""])[0],
        "bpm": audio.get("bpm", [""])[0],
        "key": audio.get("initialkey", [""])[0],
        "camelot": audio.get("camelot", [""])[0],
        "energy": audio.get("energy", [""])[0],
        "lufs": audio.get("lufs", [""])[0],
        "replaygain_track_gain": audio.get("replaygain_track_gain", [""])[0],
        "playlists": list(audio.get("playlist", [])),
    }
