import re
from pathlib import Path
from mutagen.flac import FLAC


def parse_filename(path: str) -> tuple[str, str]:
    stem = Path(path).stem
    match = re.match(r"^(.+?)\s*-\s*(.+)$", stem)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return "", stem


def write_tags(path: str, analysis: dict, artist: str = "", title: str = ""):
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
    }
