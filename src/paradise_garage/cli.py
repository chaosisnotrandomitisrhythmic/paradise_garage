import sys
import json
from pathlib import Path

from .analyze import analyze_track
from .loudness import measure as measure_loudness
from .tag import parse_filename, write_tags, read_tags
from .catalog import load_catalog, save_catalog, add_track, search_catalog


SOURCES = ("spotify", "vinyl", "soundcloud", "bandcamp", "cd", "own", "other")


def cmd_ingest(paths: list[str], playlist: str = None, source: str = None,
               discogs: int = None, position: str = None):
    """Analyse + tag files into the catalog. `source` says where the audio came
    from; `discogs`/`position` tag a vinyl rip from its release (album, label,
    catalogue number, side position, cover)."""
    catalog = load_catalog()
    playlists = [playlist] if playlist else None
    for p in paths:
        path = Path(p).resolve()
        if not path.exists():
            print(f"  SKIP  {p} (not found)")
            continue

        print(f"  ANALYZING  {path.name}")
        analysis = analyze_track(str(path))
        analysis.update(measure_loudness(str(path)))
        artist, title = parse_filename(str(path))

        print(f"    BPM: {analysis['bpm']}")
        print(f"    Key: {analysis['key']} {analysis['mode']} ({analysis['camelot']})")
        print(f"    Energy: {analysis['energy']}")
        if analysis.get("lufs") is not None:
            print(f"    Loudness: {analysis['lufs']} LUFS (true peak {analysis.get('true_peak_dbtp')} dBTP)")
        print(f"    Duration: {analysis['duration_sec']}s")

        write_tags(str(path), analysis, artist=artist, title=title, playlists=playlists)
        print(f"  TAGGED  {path.name}" + (f"  [+ playlist: {playlist}]" if playlist else ""))
        if source:
            set_source([path], source)
        if discogs:
            from .discogs import Client, tag_file
            _, changed = tag_file(Client(), path, discogs, position)
            print(f"    + Discogs {discogs} {position}: {', '.join(changed)}")

        catalog = add_track(catalog, str(path), analysis, artist, title, playlists=playlists)

    save_catalog(catalog)
    print(f"\n  Catalog: {len(catalog['tracks'])} tracks")


def set_source(paths: list[Path], source: str) -> None:
    from mutagen.flac import FLAC

    for p in paths:
        audio = FLAC(p)
        audio["source"] = source
        audio.save()


def cmd_ingest_args(args: list[str]):
    """pg ingest <file.flac ...> [--playlist NAME] [--source vinyl] [--discogs ID --pos A2]"""
    opts, files, i = {}, [], 0
    while i < len(args):
        if args[i] in ("--playlist", "--source", "--discogs", "--pos") and i + 1 < len(args):
            opts[args[i][2:]] = args[i + 1]
            i += 1
        else:
            files.append(args[i])
        i += 1
    if opts.get("source") and opts["source"] not in SOURCES:
        print(f"  --source must be one of: {', '.join(SOURCES)}")
        return
    if opts.get("discogs") and (not opts.get("pos") or len(files) != 1):
        print("  --discogs tags one rip: pg ingest rip.flac --source vinyl --discogs <release-id> --pos A2")
        return
    cmd_ingest(files, playlist=opts.get("playlist"), source=opts.get("source"),
               discogs=int(opts["discogs"]) if opts.get("discogs") else None, position=opts.get("pos"))


def cmd_source(args: list[str]):
    """pg source <spotify|vinyl|soundcloud|…> <file.flac ...>: where the audio came from.
    pg source --picks: the reviewed ones in metadata/library-picks.json."""
    if args == ["--picks"]:
        from .split import FLAC_DIR

        picks = load_picks().get("source", {})
        for name, src in picks.items():
            set_source([FLAC_DIR / name], src)
            print(f"  source={src}  {name}")
        return
    if len(args) < 2 or args[0] not in SOURCES:
        print(f"  Usage: pg source <{'|'.join(SOURCES)}> <file.flac ...>")
        return
    files = [Path(a) for a in args[1:]]
    missing = [f for f in files if not f.exists()]
    if missing:
        print("  Not found: " + ", ".join(map(str, missing)))
        return
    set_source(files, args[0])
    print(f"  source={args[0]} on {len(files)} file(s)")


def cmd_record(args: list[str]):
    from .record import record_missing, record_playlist

    url = None
    keep_master = False
    trim_silence = False
    limit = None
    start = 1
    skip_existing = False
    dry_run = False
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--keep-master":
            keep_master = True
        elif a == "--trim":
            trim_silence = True
        elif a in ("--skip-existing", "--resume"):
            skip_existing = True
        elif a == "--dry-run":
            dry_run = True
        elif a == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1])
            i += 1
        elif a == "--start" and i + 1 < len(args):
            start = int(args[i + 1])
            i += 1
        elif not a.startswith("--"):
            url = a
        i += 1

    if not url:
        print("  Usage: pg record <playlist-url | liked> [--skip-existing] [--dry-run]")
        print("                   [--start N] [--limit N] [--keep-master] [--trim]")
        return

    if url.strip().lower() in ("liked", "liked-songs", "liked songs") and not skip_existing:
        print("  'liked' records the saved-tracks library — use it with --skip-existing")
        print("  (per-track mode; the library has no playlist context to play through).")
        return

    from .harvest import is_harvest_ref

    if is_harvest_ref(url) and not skip_existing:
        print("  A harvested tracklist has no Spotify playlist to play through —")
        print("  use it with --skip-existing (per-track mode, resumable).")
        return

    # --skip-existing / --resume: record only the tracks not already in the library
    # (per-track, saved as each finishes → safe to interrupt and re-run).
    if skip_existing:
        record_missing(url, dry_run=dry_run, limit=limit)
        return

    name, files = record_playlist(
        url,
        keep_master=keep_master,
        trim_silence=trim_silence,
        limit=limit,
        start=start,
    )
    if files:
        print(f"\n  Ingesting {len(files)} captured tracks…")
        cmd_ingest(files, playlist=name)


def cmd_harvest(args: list[str]):
    """Scrape an algorithmic playlist (Radio / Mix) the Web API refuses to resolve."""
    from .harvest import harvest, load_harvest

    url = None
    name = None
    max_rounds = 400
    port = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--name" and i + 1 < len(args):
            name = args[i + 1]
            i += 1
        elif a == "--max-rounds" and i + 1 < len(args):
            max_rounds = int(args[i + 1])
            i += 1
        elif a == "--port" and i + 1 < len(args):
            port = int(args[i + 1])
            i += 1
        elif a == "--remote":
            port = 9223
        elif not a.startswith("--"):
            url = a
        i += 1

    if not url:
        print("  Usage: pg harvest <playlist-url> [--name NAME] [--remote] [--port N]")
        print("                    [--max-rounds N]")
        print()
        print("  Default: your everyday Chrome — needs 'Allow remote debugging' at")
        print("  chrome://inspect/#remote-debugging (and a Chrome relaunch to take effect).")
        print("  --remote: a dedicated 'CDP Chrome' on port 9223 (fastcdp-setup), which")
        print("  has its own profile and no approval prompt. This is the mini's path.")
        return

    print(f"  Harvesting {url}")
    path = harvest(url, name=name, max_rounds=max_rounds, port=port)
    playlist_name, tracks = load_harvest(str(path))
    total = sum(t.duration_sec for t in tracks)
    print(f"\n  {playlist_name}: {len(tracks)} tracks, {total / 3600:.1f}h")
    print(f"  {path}")
    print(f"\n  Next: pg record harvest:{path.stem} --skip-existing --dry-run")
    print("  ⚠️  Loading the web player made Chrome a Spotify Connect device.")
    print("      Check Spotify desktop is on 'This Computer' before recording.")


def cmd_capture(args: list[str]):
    """Capture a single browser-sourced track (e.g. SoundCloud) into the library.

    Usage:
      pg capture "Artist" "Title" --duration MM:SS [--browser-prefix com.google.Chrome]
                 [--playlist SoundCloud] [--pad SECONDS] [--no-trim]
      pg capture --arm-test [--browser-prefix com.google.Chrome]   (readiness check, no audio)
    """
    from .record import arm_test, parse_duration, record_manual

    browser_prefix = "com.google.Chrome"
    playlist = "SoundCloud"
    source = "soundcloud"
    duration = None
    pad = 8.0
    trim_silence = True
    do_arm_test = False
    positionals: list[str] = []

    i = 0
    while i < len(args):
        a = args[i]
        if a == "--arm-test":
            do_arm_test = True
        elif a == "--no-trim":
            trim_silence = False
        elif a == "--duration" and i + 1 < len(args):
            duration = parse_duration(args[i + 1])
            i += 1
        elif a == "--pad" and i + 1 < len(args):
            pad = float(args[i + 1])
            i += 1
        elif a == "--browser-prefix" and i + 1 < len(args):
            browser_prefix = args[i + 1]
            i += 1
        elif a == "--playlist" and i + 1 < len(args):
            playlist = args[i + 1]
            i += 1
        elif a == "--source" and i + 1 < len(args):
            source = args[i + 1]
            i += 1
        elif not a.startswith("--"):
            positionals.append(a)
        i += 1

    if do_arm_test:
        print(f"\n  Arm test — tapping '{browser_prefix}' for ~3s (no audio needed)…")
        r = arm_test(browser_prefix)
        if r["attached"]:
            dur = f"{r['wav_dur']:.1f}s" if r["wav_dur"] is not None else "header-only/silent"
            print(f"  ✓ READY — tap attached to {browser_prefix} and wrote "
                  f"{r['bytes']} bytes ({dur} WAV). Deleted test file.")
        else:
            print(f"  ✗ NOT READY — {r['error'] or 'tap did not produce a WAV.'}")
            print("    If Chrome has not played audio this session it won't appear in")
            print("    Core Audio's process list — play ~1s of anything in Chrome, then retry.")
        return

    if len(positionals) < 2 or duration is None:
        print('  Usage: pg capture "Artist" "Title" --duration MM:SS '
              "[--browser-prefix com.google.Chrome] [--playlist NAME] [--pad SECONDS] [--no-trim]")
        print("         pg capture --arm-test   (readiness check)")
        return

    artist, title = positionals[0], positionals[1]
    record_manual(
        artist, title, duration,
        browser_prefix=browser_prefix, playlist=playlist, pad=pad, trim_silence=trim_silence,
        source=source,
    )


def cmd_traktor(args: list[str]):
    from .traktor import apply

    dry_run = "--dry-run" in args
    paths = [a for a in args if not a.startswith("--")]

    # --playlists: sync catalog playlist tags into a 'Paradise Garage' browser
    # folder (one Traktor playlist per source playlist). No file args needed.
    if "--playlists" in args:
        from .traktor import sync_playlists

        catalog = load_catalog()
        playlist_map: dict[str, list] = {}
        for info in catalog["tracks"].values():
            p = Path(info["path"])
            if not p.exists():
                continue
            for name in info.get("playlists", []):
                playlist_map.setdefault(name, []).append(p)
        if not playlist_map:
            print("  No playlist tags in the catalog yet.")
            return
        try:
            report = sync_playlists(playlist_map, dry_run=dry_run)
        except RuntimeError as e:
            print(f"  ERROR: {e}")
            return
        print(f"  Folder 'Paradise Garage' {report['action']}:")
        for name, n in report["playlists"].items():
            print(f"    {name}  ({n} tracks)")
        if report["pending"]:
            print(f"  ! {len(report['pending'])} track(s) not in the collection yet — "
                  f"run `pg traktor <flacs>` first, then re-run --playlists:")
            for f in report["pending"]:
                print(f"    - {f}")
        print("\n  (dry run — nothing written)" if dry_run
              else "\n  collection.nml updated (backup made).")
        return

    if not paths:
        print("  Usage: pg traktor <file.flac> [file2.flac ...] [--dry-run] | pg traktor --playlists")
        print("  Note: import the track into Traktor and run Analyze (Async) FIRST — pg snaps")
        print("        cues to Traktor's own grid and skips tracks it hasn't analyzed yet.")
        return
    try:
        report = apply(paths, dry_run=dry_run)
    except RuntimeError as e:
        print(f"  ERROR: {e}")
        return

    for r in report:
        if r["action"] == "skipped":
            print(f"  SKIP   {r['file']} — {r['reason']}")
        else:
            cues = ", ".join(f"{n}@{t}s" for n, t in r.get("cues", []))
            print(f"  {r['action'].upper():7} {r['file']}  [{cues}]")
    print("\n  (dry run — nothing written)" if dry_run else "\n  collection.nml updated (backup made). Relaunch Traktor to see cues.")


def cmd_mixxx(args: list[str]):
    from .mixxx import DB, apply

    dry_run = "--dry-run" in args
    no_playlists = "--no-playlists" in args
    db = DB
    if "--db" in args:
        db = Path(args[args.index("--db") + 1])
    paths = [a for a in args if not a.startswith("--") and Path(a) != db]
    if len(paths) != 1:
        print("  Usage: pg mixxx <collection.nml> [--dry-run] [--no-playlists] [--db PATH]")
        print("  Note: let Mixxx scan ~/Music/Library FIRST and quit it — pg only fills in")
        print("        grid, key and cues on tracks Mixxx already has (matched by file name).")
        return
    try:
        r = apply(Path(paths[0]), db=db, dry_run=dry_run, playlists=not no_playlists)
    except RuntimeError as e:
        print(f"  ERROR: {e}")
        return

    print(f"  updated {len(r['updated'])} track(s) "
          f"({sum(u['cues'] for u in r['updated'])} cues)")
    for label, key in [("not in Mixxx yet (scan first, or not synced)", "not_in_mixxx"),
                       ("ambiguous file name (several Mixxx tracks)", "ambiguous"),
                       ("no sample rate yet (let Mixxx finish scanning)", "no_samplerate"),
                       ("no Traktor grid (Mixxx will analyze)", "no_grid"),
                       ("several grid markers, first one used (check by ear)", "multi_grid")]:
        if r[key]:
            print(f"  ! {len(r[key])} {label}:")
            for f in r[key][:15]:
                print(f"      {f}")
            if len(r[key]) > 15:
                print(f"      ... and {len(r[key]) - 15} more")
    for f, cues in r["skipped_cues"].items():
        print(f"  ~ {f}: skipped {', '.join(cues)}")
    for name, pl in r["playlists"].items():
        miss = f", {pl['missing']} missing" if pl["missing"] else ""
        print(f"  playlist {name}  ({pl['tracks']} tracks{miss})")
    print("\n  (dry run — nothing written)" if dry_run
          else f"\n  mixxxdb.sqlite updated (backup: {r['backup']}).")


def cmd_search(args: list[str]):
    catalog = load_catalog()
    query = ""
    bpm_range = None
    camelot = None
    playlist = None

    i = 0
    while i < len(args):
        if args[i] == "--bpm" and i + 1 < len(args):
            lo, hi = args[i + 1].split("-")
            bpm_range = (float(lo), float(hi))
            i += 2
        elif args[i] == "--camelot" and i + 1 < len(args):
            camelot = args[i + 1]
            i += 2
        elif args[i] == "--playlist" and i + 1 < len(args):
            playlist = args[i + 1]
            i += 2
        else:
            query = args[i]
            i += 1

    results = search_catalog(
        catalog, query=query, bpm_range=bpm_range, camelot=camelot, playlist=playlist
    )
    if not results:
        print("  No tracks found.")
        return

    for t in results:
        print(f"  {t['artist']} - {t['title']}")
        print(f"    BPM: {t['bpm']} | Key: {t['key']} ({t['camelot']}) | Energy: {t['energy']}")
        if t.get("playlists"):
            print(f"    Playlists: {', '.join(t['playlists'])}")
        print()


def cmd_enrich(args: list[str]):
    """Album, date, label and cover art from Spotify (fills missing fields only)."""
    from .enrich import enrich
    from .spotify import _app_client
    from .split import FLAC_DIR

    apply_ = "--apply" in args
    playlists, uris, files, i = [], [], [], 0
    while i < len(args):
        if args[i] in ("--playlist", "--uri") and i + 1 < len(args):
            (playlists if args[i] == "--playlist" else uris).append(args[i + 1])
            i += 1
        elif not args[i].startswith("--"):
            files.append(Path(args[i]))
        i += 1
    if "--all" in args:
        files = sorted(FLAC_DIR.glob("*.flac"))
    if not files:
        print("  Usage: pg enrich <file.flac ...|--all> [--playlist URL]... [--apply] [--force] [--no-cover]")
        print("         pg enrich <file.flac> --uri spotify:track:… --apply --force   (fix one pick)")
        print("  Dry run unless --apply. Only adds album/date/label/ISRC/cover; never")
        print("  touches artist, title, analysis, playlist or Traktor tags.")
        return
    if uris and len(files) != 1:
        print("  --uri fixes one file at a time: pg enrich <file.flac> --uri spotify:track:… --apply --force")
        return
    override = dict(load_picks().get("spotify", {}))   # reviewed picks win over search
    if uris:
        override[files[0].name] = uris[0]
    try:
        sp = _app_client()
    except RuntimeError as e:
        print(f"  ERROR: {e}")
        return

    matches = enrich(files, sp, apply=apply_, force="--force" in args,
                     cover="--no-cover" not in args, playlist_urls=playlists,
                     override=override)
    found = [m for m in matches if m.uri]
    by_source = {}
    for m in found:
        by_source[m.source] = by_source.get(m.source, 0) + 1
    print(f"  {len(found)}/{len(matches)} matched  "
          + "  ".join(f"{k}: {v}" for k, v in sorted(by_source.items())))
    verb = "updated" if apply_ else "would update"
    changed = [m for m in found if m.changed]
    print(f"  {verb} {len(changed)} file(s)\n")
    for m in changed:
        alb = m.meta.get("album", "")
        comp = "  ⚠ compilation" if m.meta.get("album_type") == "compilation" else ""
        print(f"    {m.path.name}\n      → {alb} ({m.meta.get('date', '')[:4]}){comp} "
              f"[{m.source}] +{','.join(m.changed)}")
    misses = [m for m in matches if not m.uri]
    if misses:
        print(f"\n  ! {len(misses)} not matched (nothing written):")
        for m in misses:
            print(f"    {m.path.name}  — {m.note}")
    print("\n  (dry run — nothing written; add --apply)" if not apply_
          else "\n  Rescan in Navidrome / re-import metadata in Mixxx to see it.")


PICKS_PATH = Path(__file__).parent.parent.parent / "metadata" / "library-picks.json"


def load_picks(path: Path = PICKS_PATH) -> dict:
    """Hand-reviewed picks (metadata/library-picks.json; reasons in library-decisions.md)."""
    return json.loads(path.read_text()) if path.exists() else {}


def cmd_discogs(args: list[str]):
    """The records Andreas owns, synced both ways with his Discogs collection."""
    from . import discogs
    from .split import FLAC_DIR

    sub, rest = (args[0], args[1:]) if args else ("", [])
    if sub not in ("pull", "push", "find", "tag", "picks", "artist-images"):
        print("  Usage: pg discogs pull [--apply] [--no-cover]   (collection -> library tags + missing tracks)")
        print('         pg discogs find "Virtual Dreams MFM050"   (search releases, pick an id)')
        print("         pg discogs push <release-id> ...          (add to your collection, y/n each)")
        print("         pg discogs tag <file.flac> <release-id> [--pos A2] [--apply]   (album from a release you don't own)")
        print("         pg discogs picks [--apply]   (the reviewed picks in metadata/library-picks.json)")
        print("         pg discogs artist-images [--apply] [--force]   (a picture per artist for Navidrome)")
        return
    try:
        client = discogs.Client()
    except RuntimeError as e:
        print(f"  ERROR: {e}")
        return
    apply_ = "--apply" in rest
    words = [a for a in rest if not a.startswith("--")]

    if sub == "find":
        for r in client.search(" ".join(words)):
            print(f"  {r['id']:>9}  {r.get('title', '')}  [{', '.join(r.get('label', [])[:1])} "
                  f"{r.get('catno', '')}, {r.get('year', '?')}, {', '.join(r.get('format', [])[:3])}]")
        return

    if sub == "push":
        for rid in words:
            rel = client.release(int(rid))
            if client.in_collection(int(rid)):
                print(f"  = already in your collection: {discogs.describe(rel)}")
                continue
            if input(f"  Add {discogs.describe(rel)} to your Discogs collection? [y/N] ").strip().lower() == "y":
                client.add_to_collection(int(rid))
                print("    added")
            else:
                print("    skipped")
        return

    if sub == "tag":
        pos = rest[rest.index("--pos") + 1] if "--pos" in rest else None
        words = [w for w in words if w != pos]
        if len(words) != 2:
            print("  Usage: pg discogs tag <file.flac> <release-id> [--pos A2] [--apply]")
            return
        rt, changed = discogs.tag_file(client, Path(words[0]), int(words[1]), pos, owned=False, apply=apply_)
        print(f"  {Path(words[0]).name} = {rt.position} {rt.artist} – {rt.title}")
        print(f"  {'updated' if apply_ else 'would update'}: {', '.join(changed) or 'nothing'}")
        return

    if sub == "picks":
        for name, pick in load_picks().get("discogs", {}).items():
            rt, changed = discogs.tag_file(client, FLAC_DIR / name, int(pick["release"]), pick.get("pos"),
                                           owned=False, apply=apply_)
            print(f"  {name}\n    → {discogs.describe(client.release(int(pick['release'])))} {rt.position}"
                  f"   {'updated' if apply_ else 'would update'}: {','.join(changed) or 'nothing'}")
        print("  (dry run — nothing written; add --apply)" if not apply_ else "")
        return

    if sub == "artist-images":
        rows = discogs.artist_images(client, sorted(FLAC_DIR.glob("*.flac")), apply=apply_,
                                     force="--force" in rest, picks=load_picks().get("artists", {}))
        for r in rows:
            who = f"{r['discogs_name']} [{r['id']}]" if r["id"] else ""
            print(f"  {r['status']:<20} {r['name']}" + (f"  → {who}, {r['how']}" if who else f"  ({r['how']})"))
        counts = {}
        for r in rows:
            counts[r["status"]] = counts.get(r["status"], 0) + 1
        print("\n  " + ", ".join(f"{n} {s}" for s, n in sorted(counts.items())) + f"  → {discogs.ARTIST_IMAGES}")
        print("  (dry run — nothing written; add --apply)" if not apply_ else "")
        return

    # pull
    placements = discogs.pull(client, sorted(FLAC_DIR.glob("*.flac")), apply=apply_,
                              cover="--no-cover" not in rest)
    sp = None
    try:
        from .spotify import _app_client
        sp = _app_client()
    except RuntimeError:
        print("  (no Spotify keys: missing tracks are listed without a Spotify check)")
    rels, missing_rip = {}, []
    for pl in placements:
        rels.setdefault(pl.release["id"], []).append(pl)
    placed = sum(1 for pl in placements if pl.path)
    print(f"  {len(rels)} release(s) in your collection, {placed}/{len(placements)} tracks in the library\n")
    verb = "updated" if apply_ else "would update"
    for rid, pls in rels.items():
        print(f"  {discogs.describe(pls[0].release)}  [discogs {rid}]")
        for pl in pls:
            t = f"{pl.track.position:>4} {pl.track.artist} – {pl.track.title}"
            if pl.path:
                print(f"    ✓ {t}" + (f"   {verb}: {','.join(pl.changed)}" if pl.changed else "")
                      + (f"   ({pl.note})" if pl.note else ""))
                continue
            uri = discogs.on_spotify(sp, pl.track) if sp else ""
            if uri:
                print(f"    · {t}   missing — on Spotify, record it ({uri})" + (f"   [{pl.note}]" if pl.note else ""))
            else:
                print(f"    · {t}   missing — not on Spotify, rip it" + (f"   [{pl.note}]" if pl.note else ""))
                if sp:
                    missing_rip.append(pl)
        print()
    if apply_ and missing_rip:
        n = discogs.add_vinyl_rips(missing_rip)
        print(f"  {n} new line(s) in metadata/vinyl-rips.md")
    print("  (dry run — nothing written; add --apply)" if not apply_
          else "  Rescan in Navidrome / re-import metadata in Mixxx to see it.")


def cmd_cues(args: list[str]):
    from .cues import DB, fmt_time, propose, write

    dry_run = "--dry-run" in args
    db = DB
    if "--db" in args:
        db = Path(args[args.index("--db") + 1])
    names = [a for a in args if not a.startswith("--") and Path(a) != db]
    if len(names) != 1:
        print("  Usage: pg cues <mixxx-playlist-name> [--dry-run] [--db PATH]")
        print("  Note: proposes IN / MIX IN / BREAK / MIX OUT as hot cues 1-4 on every track of the")
        print("        playlist, snapped to the Mixxx grid. Replaces hot cues 1-4 and the main cue;")
        print("        leaves slots 5+ alone. Quit Mixxx before writing (dry run works while it runs).")
        return

    def show(r):
        cues = "  ".join(f"{c['label']}@{fmt_time(c['sec'])}" for c in r["cues"]) or f"- {r.get('reason', 'no cues')}"
        print(f"  {r['pos']:2d}  {r['artist']} - {r['title']}  [{cues}]", flush=True)

    proposals = propose(names[0], db=db, progress=show)
    if not proposals:
        print(f"  No Mixxx playlist matching '{names[0]}'.")
        return
    try:
        rep = write(proposals, db=db, dry_run=dry_run)
    except RuntimeError as e:
        print(f"  ERROR: {e}")
        return
    print(f"\n  {rep['written']} track(s), {rep['cues']} cues" + (" (dry run — nothing written)" if dry_run
          else f" written to mixxxdb.sqlite (backup: {rep['backup']}). Restart Mixxx to see them."))


def cmd_grid(args: list[str]):
    from .grid import DB, measure, write

    dry_run = "--dry-run" in args
    do_write = "--write" in args
    db = DB
    if "--db" in args:
        db = Path(args[args.index("--db") + 1])
    words = [a for a in args if not a.startswith("--") and Path(a) != db]
    ids = [int(w) for w in words if w.isdigit()]
    names = [w for w in words if not w.isdigit()]
    if len(names) + (1 if ids else 0) != 1:
        print("  Usage: pg grid <mixxx-playlist-name> | <track-id ...>  [--write] [--dry-run] [--db PATH]")
        print("  Note: measures exact BPM and kick phase per track and compares with the Mixxx grid.")
        print("        --write replaces the grids that are off (BPM locked afterwards). Quit Mixxx first.")
        return

    def show(r):
        if "bpm_err" not in r:
            print(f"  {r['id']:4d}  {r['artist']} - {r['title']}  - {r['reason']}", flush=True)
            return
        flag = "??  " if r["uncertain"] else "OFF " if r["off"] else "ok  "
        err = "no grid" if r["anchor_err_beats"] is None else f"anchor {r['anchor_err_beats']:.2f} beats off"
        print(f"  {flag} {r['artist']} - {r['title']}  stored {r['bpm_db'] if 'bpm_db' in r else r['bpm']:.3f}"
              f"  measured {r['bpm']:.3f} ({r['bpm_err']:+.3f})  {err}  conf {r['concentration']:.2f}"
              f"  drift {r['drift_beats']:.2f}", flush=True)

    results = measure(names[0] if names else None, ids, db=db, progress=show)
    if not results:
        print("  Nothing matched.")
        return
    n_off = sum(1 for r in results if r.get("off") and not r.get("uncertain"))
    n_unc = sum(1 for r in results if r.get("uncertain"))
    print(f"\n  {n_off} of {len(results)} grid(s) off and fixable; {n_unc} too uncertain to touch (??: live drums or tempo drift).")
    if do_write or dry_run:
        try:
            rep = write(results, db=db, dry_run=dry_run)
        except RuntimeError as e:
            print(f"  ERROR: {e}")
            return
        print(f"  {len(rep['written'])} grid(s) " + ("would be rewritten (dry run)." if dry_run
              else f"rewritten and BPM-locked (backup: {rep.get('backup')}). Restart Mixxx to see them."))


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
        print("  pg record <playlist-url> [--skip-existing] [--start N] [--limit N] [--keep-master]")
        print("  pg harvest <playlist-url> [--name NAME]   (Radio/Mix ids the Web API 404s)")
        print('  pg capture "Artist" "Title" --duration MM:SS   (browser-sourced single track, e.g. SoundCloud)')
        print("  pg traktor <file.flac> [...] [--dry-run]   (grid-snapped cues; analyze in Traktor first)")
        print("  pg mixxx <collection.nml> [--dry-run]   (Traktor grid/key/cues/playlists into Mixxx)")
        print("  pg enrich <file.flac ...|--all> [--apply]   (album, date, cover art from Spotify)")
        print("  pg discogs pull|push|find|tag ...   (your records on Discogs <-> the library)")
        print("  pg source <spotify|vinyl|soundcloud|...> <file.flac ...>")
        print("  pg cues <mixxx-playlist> [--dry-run]   (IN/MIX IN/BREAK/MIX OUT hot cues 1-4 into Mixxx)")
        print("  pg grid <mixxx-playlist>|<id...> [--write]   (check/repair beat grids from the kick drum)")
        print("  pg ingest <file.flac ...> [--playlist NAME] [--source vinyl] [--discogs ID --pos A2]")
        print("  pg ingest-all")
        print("  pg search [query] [--bpm 120-130] [--camelot 8A] [--playlist NAME]")
        print("  pg list")
        print("  pg info <file.flac>")
        return

    cmd = sys.argv[1]

    if cmd == "record":
        cmd_record(sys.argv[2:])
    elif cmd == "harvest":
        cmd_harvest(sys.argv[2:])
    elif cmd == "capture":
        cmd_capture(sys.argv[2:])
    elif cmd == "traktor":
        cmd_traktor(sys.argv[2:])
    elif cmd == "mixxx":
        cmd_mixxx(sys.argv[2:])
    elif cmd == "enrich":
        cmd_enrich(sys.argv[2:])
    elif cmd == "discogs":
        cmd_discogs(sys.argv[2:])
    elif cmd == "source":
        cmd_source(sys.argv[2:])
    elif cmd == "cues":
        cmd_cues(sys.argv[2:])
    elif cmd == "grid":
        cmd_grid(sys.argv[2:])
    elif cmd == "ingest":
        cmd_ingest_args(sys.argv[2:])
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
