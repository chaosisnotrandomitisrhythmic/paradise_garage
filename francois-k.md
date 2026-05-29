---
layout: default
title: François K
---

# François K

**François Kevorkian** — "François K" — is the bridge between the Paradise Garage's golden age and the way this project actually plays. Born in France in 1954, he moved to New York in 1975, started as a *drummer* (playing live percussion next to pioneering DJ Walter Gibbons at Galaxy 21), and became the most important remixer of the New York dance era. Where [Larry Levan](inspiration#paradise-garage) held the Garage, François K built the records that played there — and then spent the next forty years carrying the lineage forward.

He matters here for two reasons: he's a node in the **Garage lineage** (the records, the rooms, the people), and his **live-dub rig and library system** are a near-exact blueprint for the build on the [Equipment](equipment) page.

## The Garage lineage — Arthur Russell, Levan, and the remix

The thread that ties François K to Larry Levan and the Paradise Garage runs straight through **Arthur Russell** — the avant-garde cellist/composer whose sprawling, "unreleasable" downtown sessions became dancefloor classics only after remixers reshaped the raw tapes.

| Record | Alias | What happened | Credit |
|--------|-------|---------------|--------|
| **"Go Bang #5"** (1982) | Dinosaur L | The album mix of "Go Bang!" (from *24→24 Music*, 1981) was too complex for the floor. Will Socolov & Russell handed the multitrack — "an absolute, utter and total mess," per François K — to Kevorkian, who recut it on borrowed time at Right Track into a dubbed-out floor weapon. A defining proto-house remix and a Garage staple. | **François K remix** |
| **"Is It All Over My Face?"** (1980) | Loose Joints | The original (Male Vocal) by Russell + Steve D'Acquisto was a mess; the **Female Vocal** mix — built around a vocal salvaged from that session, cut on stolen studio time — became one of the most important records of the era and a Levan anthem. | **Larry Levan** mix — **François K uncredited co-mixer** |

So the two New York titans were doing the *same job* — translating Russell's avant-garde tapes into records a DJ could play — and on "Is It All Over My Face?" they were literally in the room together. That record and "Go Bang #5" were both core Paradise Garage cuts: the point where Levan's Garage and François K's remix craft overlap.

François K also ran the remix board at **Prelude Records** (D Train's "You're the One for Me," Sharon Redd) — the in-house architect of the dub-influenced 12" remix.

**After Levan.** When Larry Levan died in 1992, François K became one of the principal keepers of the flame. In **1996 he co-founded [Body & Soul](https://en.wikipedia.org/wiki/Body_%26_Soul_(club_night))** with **Danny Krivit** and **Joaquín "Joe" Claussell** — the Sunday party widely seen as the spiritual successor to the Garage and David Mancuso's Loft. He runs the **Wave Music** label and the long-running **Deep Space** night (dub / deep house / techno).

> **Credit caveat:** Russell's discography has many competing mix credits and reissue versions. The two above are verified — "Go Bang #5" = François K remix; "Is It All Over My Face?" Female Vocal = Larry Levan with François K as uncredited co-mixer — but cross-check any other Russell credits against [Discogs](https://www.discogs.com/) before treating them as fact.

## His live rig — the blueprint for this build

Researched Apr 2026 as a reference setup. The striking thing: it maps almost 1:1 onto the [A Guy Called Gerald live-jam rig](inspiration#a-guy-called-gerald--live-jam-ethos-apr-18-pivot) this desk is built around — *building* sound in real time, not chaining finished tracks.

- **Mixer:** Allen & Heath **Xone:92** (the rotary-flavoured ancestor of our [Xone:96](equipment))
- **Software:** **Traktor**, driven by **Native Instruments Kontrol D2 + F1**
- **External FX:** Pioneer **EFX-1000**, Yamaha **SPX990** — hardware effects in a send/return loop, the live-dub heart of the set
- **No jogwheels.** He doesn't beatmatch records — he runs **Stems**, remixing tracks live by muting, filtering, and dubbing the parts. Pure live re-arrangement, not transitions.

This is the same architecture as our planned rig (Reason on two laptops + Kaossilator Pro+ + [Xone:96](equipment)): a colored mixer, hardware/live FX, and source material treated as raw parts to rebuild on the fly — not a setlist.

## His library system — the ancestor of `pg`

The other reason François K belongs in this project: he's been solving the **library problem** since before it had a name.

**1994:** he built a **custom relational database** on a micro-laptop to catalog his DAT tapes and CDs — searchable metadata for a working DJ's crate, decades before Rekordbox or Lexicon.

**His media evolution:**

```
vinyl → DAT → custom-burned CDs → hard drives → Stems → AI stem separation
```

Each step is the same instinct: keep the music portable, searchable, and re-playable as the format churns underneath it. Our [`pg` CLI](https://github.com/chaosisnotrandomitisrhythmic/paradise_garage) — `pg ingest` writing BPM/key/energy tags, `pg search` querying by Camelot key and tempo — is the modern, scriptable version of exactly what François K hand-rolled in 1994.

## Key links

| Resource | Link |
|----------|------|
| Body & Soul (club night) | [Wikipedia](https://en.wikipedia.org/wiki/Body_%26_Soul_(club_night)) |
| Arthur Russell | [Wikipedia](https://en.wikipedia.org/wiki/Arthur_Russell_(musician)) |
| Dinosaur L — "Go Bang #5" reissue context | [FACT](https://www.factmag.com/2016/04/07/arthur-russell-go-bang-5-reissue-walter-gibbons-remix/) |
| Loose Joints — "Is It All Over My Face?" | [Discogs](https://www.discogs.com/master/8301-Loose-Joints-Is-It-All-Over-My-Face) |
| Allen & Heath Xone:92 | [allen-heath.com](https://www.allen-heath.com/) |
