import sys
import json
from pathlib import Path

from .analyze import analyze_track
from .tag import parse_filename, write_tags, read_tags
from .catalog import load_catalog, save_catalog, add_track, search_catalog


def cmd_ingest(paths: list[str]):
    catalog = load_catalog()
    for p in paths:
        path = Path(p).resolve()
        if not path.exists():
            print(f"  SKIP  {p} (not found)")
            continue

        print(f"  ANALYZING  {path.name}")
        analysis = analyze_track(str(path))
        artist, title = parse_filename(str(path))

        print(f"    BPM: {analysis['bpm']}")
        print(f"    Key: {analysis['key']} {analysis['mode']} ({analysis['camelot']})")
        print(f"    Energy: {analysis['energy']}")
        print(f"    Duration: {analysis['duration_sec']}s")

        write_tags(str(path), analysis, artist=artist, title=title)
        print(f"  TAGGED  {path.name}")

        catalog = add_track(catalog, str(path), analysis, artist, title)

    save_catalog(catalog)
    print(f"\n  Catalog: {len(catalog['tracks'])} tracks")


def cmd_search(args: list[str]):
    catalog = load_catalog()
    query = ""
    bpm_range = None
    camelot = None

    i = 0
    while i < len(args):
        if args[i] == "--bpm" and i + 1 < len(args):
            lo, hi = args[i + 1].split("-")
            bpm_range = (float(lo), float(hi))
            i += 2
        elif args[i] == "--camelot" and i + 1 < len(args):
            camelot = args[i + 1]
            i += 2
        else:
            query = args[i]
            i += 1

    results = search_catalog(catalog, query=query, bpm_range=bpm_range, camelot=camelot)
    if not results:
        print("  No tracks found.")
        return

    for t in results:
        print(f"  {t['artist']} - {t['title']}")
        print(f"    BPM: {t['bpm']} | Key: {t['key']} ({t['camelot']}) | Energy: {t['energy']}")
        print()


def cmd_list():
    catalog = load_catalog()
    if not catalog["tracks"]:
        print("  Library is empty.")
        return

    for t in catalog["tracks"].values():
        print(f"  {t['artist']} - {t['title']}  [{t['bpm']} BPM | {t['camelot']} | {t['energy']}]")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  pg ingest <file.flac> [file2.flac ...]")
        print("  pg ingest-all")
        print("  pg search [query] [--bpm 120-130] [--camelot 8A]")
        print("  pg list")
        print("  pg info <file.flac>")
        return

    cmd = sys.argv[1]

    if cmd == "ingest":
        cmd_ingest(sys.argv[2:])
    elif cmd == "ingest-all":
        flac_dir = Path(__file__).parent.parent.parent / "flac"
        files = sorted(flac_dir.glob("*.flac"))
        if not files:
            print("  No FLAC files in flac/")
            return
        cmd_ingest([str(f) for f in files])
    elif cmd == "search":
        cmd_search(sys.argv[2:])
    elif cmd == "list":
        cmd_list()
    elif cmd == "info":
        for p in sys.argv[2:]:
            tags = read_tags(p)
            print(json.dumps(tags, indent=2))
    else:
        print(f"Unknown command: {cmd}")
