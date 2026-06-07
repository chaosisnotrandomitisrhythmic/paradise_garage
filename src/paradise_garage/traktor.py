"""Write tracks + grid-snapped hot cues into Traktor's collection.nml.

Proven approach (from the May 2026 manual workflow): if Traktor has already
analyzed the track, read its TEMPO BPM + AutoGrid anchor from the NML and snap
librosa structural cues to that grid. If the track isn't in the collection yet,
create a fresh ENTRY using our own analysis (BPM + first-beat anchor).

Editing is targeted string surgery (minimal diff) + minidom validation, never a
full-tree rewrite. Traktor MUST be closed (it overwrites the NML on quit), and we
back up before writing.
"""

import re
import shutil
import subprocess
import time
from pathlib import Path
from xml.dom import minidom
from xml.sax.saxutils import escape

from . import structure


def _attr(s) -> str:
    """Escape a value for a double-quoted XML attribute (&, <, >, ")."""
    return escape(str(s), {'"': "&quot;"})

COLLECTION = Path.home() / "Documents" / "Native Instruments" / "Traktor 4.5.0" / "collection.nml"

# our note names (sharp + flat) -> pitch class; minor adds 12  (Traktor MUSICAL_KEY VALUE 0-23)
_PC = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5,
       "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


def musical_key_value(key: str, mode: str):
    pc = _PC.get(key)
    if pc is None:
        return None
    return pc + (12 if mode == "minor" else 0)


def colon_dir(dir_path: Path) -> str:
    parts = [p for p in str(dir_path).strip("/").split("/") if p]
    return "/:" + "".join(f"{p}/:" for p in parts)


def traktor_running() -> bool:
    # Traktor Pro 4's process is NOT named plain 'Traktor' — `pgrep -x Traktor`
    # is a false negative (it let writes through while Traktor was open, and the
    # quit-rewrite wiped them — caught 2026-06-06). Match the bundle path too.
    return (
        subprocess.run(["pgrep", "-x", "Traktor"], capture_output=True).returncode == 0
        or subprocess.run(["pgrep", "-f", "Traktor Pro"], capture_output=True).returncode == 0
    )


def _find_entry(text: str, filename: str):
    """Return (start, end) span of the <ENTRY>…</ENTRY> for FILE=filename, or None."""
    marker = f'FILE="{_attr(filename)}"'  # NML stores attrs entity-escaped (e.g. " → &quot;)
    i = text.find(marker)
    if i == -1:
        return None
    start = text.rfind("<ENTRY ", 0, i)
    end = text.find("</ENTRY>", i)
    if start == -1 or end == -1:
        return None
    return start, end + len("</ENTRY>")


def _read_grid(entry: str):
    """(bpm, anchor_ms) from an analyzed entry, or None if no grid yet."""
    bpm_m = re.search(r'<TEMPO BPM="([\d.]+)"', entry)
    anchor_m = re.search(r'NAME="AutoGrid"[^>]*?START="([\d.]+)"', entry)
    if not bpm_m or not anchor_m:
        return None
    return float(bpm_m.group(1)), float(anchor_m.group(1))


def _snap_ms(t_ms: float, anchor_ms: float, bpm: float) -> float:
    bar = 4 * 60000.0 / bpm
    n = round((t_ms - anchor_ms) / bar)
    return max(0.0, anchor_ms + n * bar)


def _cue_xml(name: str, start_ms: float, slot: int) -> str:
    return (f'\n<CUE_V2 NAME="{name}" DISPL_ORDER="0" TYPE="0" START="{start_ms:.6f}" '
            f'LEN="0.000000" REPEATS="-1" HOTCUE="{slot}"></CUE_V2>')


def _strip_hotcues(entry: str) -> str:
    # remove existing TYPE="0" hot cues (single-line); keep AutoGrid (TYPE="4")
    return re.sub(r'\n?<CUE_V2 [^>]*TYPE="0"[^>]*></CUE_V2>', "", entry)


def _cues_for(flac_path: str, bpm: float, anchor_ms: float, st: dict | None = None):
    """Snap structural cues to the grid, sorted chronologically, colliding ones dropped.
    Returns (cues, structure_result). Pass `st` to avoid recomputing the analysis."""
    if st is None:
        st = structure.analyze_structure(flac_path, bpm=bpm)
    bar = 4 * 60000.0 / bpm
    out = []
    seen = []
    for label, t_sec in sorted(st["cues"], key=lambda c: c[1]):
        start = _snap_ms(t_sec * 1000.0, anchor_ms, bpm)
        if any(abs(start - s) < bar / 2 for s in seen):  # heuristics can coincide
            continue
        seen.append(start)
        out.append([label, start, len(out)])  # slot = sequential index
    return out, st


def _build_entry(flac_path: str, analysis: dict, vol: str, anchor_ms: float, cues: list) -> str:
    """Create a fresh ENTRY from our own analysis (track not yet in Traktor)."""
    p = Path(flac_path)
    artist, _, title = p.stem.partition(" - ")
    bpm = float(analysis["bpm"])
    mk = musical_key_value(analysis["key"], analysis["mode"])
    dur = analysis["duration_sec"]
    size_kb = p.stat().st_size // 1024
    tm = time.localtime()
    today = f"{tm.tm_year}/{tm.tm_mon}/{tm.tm_mday}"

    cue_xml = "".join(_cue_xml(n, s, slot) for n, s, slot in cues)
    mk_xml = f'\n<MUSICAL_KEY VALUE="{mk}"></MUSICAL_KEY>' if mk is not None else ""

    return (
        f'<ENTRY MODIFIED_DATE="{today}" MODIFIED_TIME="0" TITLE="{_attr(title)}" ARTIST="{_attr(artist)}">'
        f'<LOCATION DIR="{_attr(colon_dir(p.parent))}" FILE="{_attr(p.name)}" VOLUME="{vol}" VOLUMEID="{vol}"></LOCATION>\n'  # vol comes from the NML text = already escaped
        f'<MODIFICATION_INFO AUTHOR_TYPE="user"></MODIFICATION_INFO>\n'
        f'<INFO COMMENT="Camelot: {analysis["camelot"]} | Energy: {analysis["energy"]}" '
        f'KEY="{analysis["key"]} {analysis["mode"]}" PLAYTIME="{int(dur)}" '
        f'PLAYTIME_FLOAT="{dur:.6f}" IMPORT_DATE="{today}" FLAGS="12" FILESIZE="{size_kb}"></INFO>\n'
        f'<TEMPO BPM="{bpm:.6f}" BPM_QUALITY="100.000000"></TEMPO>{mk_xml}\n'
        f'<CUE_V2 NAME="AutoGrid" DISPL_ORDER="0" TYPE="4" START="{anchor_ms:.6f}" '
        f'LEN="0.000000" REPEATS="-1" HOTCUE="-1"><GRID BPM="{bpm:.6f}"></GRID>\n</CUE_V2>'
        f'{cue_xml}\n</ENTRY>\n'
    )


PG_FOLDER = "Paradise Garage"


def _playlist_node(name: str, keys: list[str]) -> str:
    """One browser playlist (NODE TYPE=PLAYLIST) with PRIMARYKEY rows."""
    import uuid

    uid = uuid.uuid5(uuid.NAMESPACE_URL, f"paradise-garage/{name}").hex
    entries = "".join(
        f'\n<ENTRY><PRIMARYKEY TYPE="TRACK" KEY="{k}"></PRIMARYKEY></ENTRY>' for k in keys
    )
    return (
        f'<NODE TYPE="PLAYLIST" NAME="{_attr(name)}">'
        f'<PLAYLIST ENTRIES="{len(keys)}" TYPE="LIST" UUID="{uid}">{entries}\n</PLAYLIST></NODE>'
    )


def sync_playlists(
    playlist_map: dict[str, list[Path]], collection: Path = COLLECTION, dry_run: bool = False
) -> dict:
    """Create/replace a 'Paradise Garage' browser folder with one playlist per
    source playlist tag. Only tracks already present in the collection are
    referenced (no dangling refs); the rest are reported as pending."""
    if traktor_running():
        raise RuntimeError("Traktor is running — quit it first (it overwrites collection.nml on exit).")
    if not collection.exists():
        raise RuntimeError(f"collection.nml not found at {collection}")

    text = collection.read_text(encoding="utf-8")
    vol_m = re.search(r'VOLUME="([^"]+)"', text)
    vol = vol_m.group(1) if vol_m else "Macintosh HD"

    nodes, report = [], {"playlists": {}, "pending": []}
    for name, paths in sorted(playlist_map.items()):
        keys = []
        for p in paths:
            if _find_entry(text, p.name) is None:   # not in collection yet → no dangling ref
                report["pending"].append(p.name)
                continue
            # vol comes from the NML text = already escaped; escape only the path part
            keys.append(f"{vol}{_attr(colon_dir(p.parent) + p.name)}")
        nodes.append(_playlist_node(name, keys))
        report["playlists"][name] = len(keys)

    folder = (
        f'<NODE TYPE="FOLDER" NAME="{_attr(PG_FOLDER)}"><SUBNODES COUNT="{len(nodes)}">\n'
        + "\n".join(nodes)
        + "\n</SUBNODES></NODE>"
    )

    marker = f'<NODE TYPE="FOLDER" NAME="{_attr(PG_FOLDER)}">'
    i = text.find(marker)
    if i != -1:
        # replace the existing folder (ends at the first </SUBNODES></NODE> after it —
        # it only ever contains PLAYLIST nodes, which close with </PLAYLIST></NODE>)
        end = text.find("</SUBNODES></NODE>", i)
        if end == -1:
            raise RuntimeError("malformed Paradise Garage folder node in NML")
        text = text[:i] + folder + text[end + len("</SUBNODES></NODE>"):]
        report["action"] = "replaced"
    else:
        # append as the last child of $ROOT and bump its SUBNODES count
        root_m = re.search(r'(<NODE TYPE="FOLDER" NAME="\$ROOT"><SUBNODES COUNT=")(\d+)(")', text)
        if not root_m:
            raise RuntimeError("could not find $ROOT playlist folder in NML")
        text = text[:root_m.start(2)] + str(int(root_m.group(2)) + 1) + text[root_m.end(2):]
        # last </SUBNODES> before </PLAYLISTS> closes $ROOT's child list
        pl_close = text.find("</PLAYLISTS>")
        close = text.rfind("</SUBNODES>", 0, pl_close) if pl_close != -1 else -1
        if close == -1:
            raise RuntimeError("could not find $ROOT closing tags in NML")
        text = text[:close] + folder + text[close:]
        report["action"] = "created"

    minidom.parseString(text)  # validate before writing

    if not dry_run:
        backup = collection.with_suffix(f".nml.bak-{time.strftime('%Y%m%d_%H%M%S')}")
        shutil.copy2(collection, backup)
        collection.write_text(text, encoding="utf-8")
    return report


def apply(flac_paths: list[str], collection: Path = COLLECTION, dry_run: bool = False) -> list[dict]:
    """Add/update Traktor entries with grid-snapped cues. Returns a per-track report."""
    if traktor_running():
        raise RuntimeError("Traktor is running — quit it first (it overwrites collection.nml on exit).")
    if not collection.exists():
        raise RuntimeError(f"collection.nml not found at {collection}")

    text = collection.read_text(encoding="utf-8")
    vol_m = re.search(r'VOLUME="([^"]+)"', text)
    vol = vol_m.group(1) if vol_m else "Macintosh HD"

    report = []
    for fp in flac_paths:
        p = Path(fp)
        span = _find_entry(text, p.name)
        if span:
            entry = text[span[0]:span[1]]
            grid = _read_grid(entry)
            if grid:
                bpm, anchor = grid
                cues, _ = _cues_for(fp, bpm, anchor)
                new_entry = _strip_hotcues(entry)
                cue_xml = "".join(_cue_xml(n, s, slot) for n, s, slot in cues)
                new_entry = new_entry.replace("</ENTRY>", cue_xml + "\n</ENTRY>")
                text = text[:span[0]] + new_entry + text[span[1]:]
                report.append({"file": p.name, "action": "updated", "grid_bpm": bpm,
                               "cues": [(n, round(s / 1000, 2)) for n, s, _ in cues]})
            else:
                report.append({"file": p.name, "action": "skipped", "reason": "entry has no grid yet (analyze in Traktor first)"})
        else:
            from .analyze import analyze_track
            analysis = analyze_track(fp)
            bpm = float(analysis["bpm"])
            st = structure.analyze_structure(fp, bpm=bpm)  # one analysis call
            anchor_ms = st.get("first_beat_sec", 0.0) * 1000.0
            cues, _ = _cues_for(fp, bpm, anchor_ms, st=st)
            entry = _build_entry(fp, analysis, vol, anchor_ms, cues)
            # insert after the COLLECTION open tag and bump ENTRIES count
            text = re.sub(r'(<COLLECTION ENTRIES=")(\d+)(">)',
                          lambda m: f"{m.group(1)}{int(m.group(2)) + 1}{m.group(3)}{entry}", text, count=1)
            report.append({"file": p.name, "action": "created",
                           "cues": [(n, round(s / 1000, 2)) for n, s, _ in cues]})

    # validate before writing
    minidom.parseString(text)

    if dry_run:
        return report

    backup = collection.with_suffix(f".nml.bak-{time.strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(collection, backup)
    collection.write_text(text, encoding="utf-8")
    return report
