import json
from pathlib import Path
from datetime import datetime

CATALOG_PATH = Path(__file__).parent.parent.parent / "metadata" / "catalog.json"


def load_catalog() -> dict:
    if CATALOG_PATH.exists():
        return json.loads(CATALOG_PATH.read_text())
    return {"tracks": {}, "updated": ""}


def save_catalog(catalog: dict):
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    catalog["updated"] = datetime.now().isoformat()
    CATALOG_PATH.write_text(json.dumps(catalog, indent=2, ensure_ascii=False))


def add_track(catalog: dict, filepath: str, analysis: dict, artist: str, title: str) -> dict:
    key = Path(filepath).name
    catalog["tracks"][key] = {
        "artist": artist,
        "title": title,
        "filename": key,
        "path": str(filepath),
        "bpm": analysis["bpm"],
        "key": f"{analysis['key']} {analysis['mode']}",
        "camelot": analysis["camelot"],
        "energy": analysis["energy"],
        "duration_sec": analysis["duration_sec"],
        "added": datetime.now().isoformat(),
    }
    return catalog


def search_catalog(catalog: dict, query: str = "", bpm_range: tuple = None, camelot: str = None) -> list:
    results = []
    for track in catalog["tracks"].values():
        if query and query.lower() not in f"{track['artist']} {track['title']}".lower():
            continue
        if bpm_range:
            bpm = float(track["bpm"])
            if not (bpm_range[0] <= bpm <= bpm_range[1]):
                continue
        if camelot and track["camelot"] != camelot:
            continue
        results.append(track)
    return results
