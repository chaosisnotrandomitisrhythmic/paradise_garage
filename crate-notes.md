---
layout: default
title: Paradise Garage — Crate Notes
---

# Paradise Garage — Crate Notes

Per-track context for the captured FLAC library — the prose companion to the
machine-readable `metadata/catalog.json`. Where the catalog holds BPM / key /
energy / loudness, this holds the *why*: who made it, where it came from, and
how the record's own structure informed the Traktor cue points (IN / MIX IN /
BREAK / MIX OUT) set by `pg traktor`.

External research is folded into each entry so the cues aren't just librosa's
RMS picks in a vacuum — they're checked against how the track is actually built.

---

## Juk Juk — *When I Feel*

**Source:** SoundCloud capture · **Crate:** SoundCloud
**Release:** *Wars / When I Feel*, Nommos **NOM003**, Dec 2012 — vinyl-only 12″ (45 RPM), AA-side
**Analysis:** 129.2 BPM · A minor (**8A**) · mid energy · −16.2 LUFS (true peak −0.0 dBTP) · 5:31

Juk Juk is **Caleb Waterman**, a London producer who surfaced in the early-2010s
UK post-dubstep / bass wave (covered by *Dazed* at the time). *When I Feel* is
the AA-side of the third release on his own vinyl-only label, **Nommos**, paired
with the Four Tet-leaning A-side *Wars*.

In RA's review (Matt Unicomb, Jan 2013) it's the housier and stronger of the
two: *"Unashamedly emotional, 'When I Feel' is minimal and punchy, with a looped
vocal as its only constant."* The arrangement deliberately **"ignores any
accepted structural guidelines"** — most distinctively, *"the kick drum drops out
numerous times, without so much as slightly disrupting the hypnotic effects of
the bass, melody and vocal combination."* An after-hours house burner built on a
single hypnotic vocal loop rather than verse/chorus scaffolding.

**How that shaped the cues:**

| Cue | Pad | Time | Rationale |
|-----|-----|------|-----------|
| IN | 1 | 0:31 | Long minimal intro before the groove proper — bass entry |
| MIX IN | 2 | 0:33 | Full groove locks ~1 bar later; the clean blend-in point |
| BREAK | 3 | 3:37 | The **deepest** of the record's "numerous" kick-drops — the one worth a hot cue |
| MIX OUT | 4 | 4:27 | ~32 bars of outro runway before the 5:31 end |

The constant looped vocal is the mixing gift here: because it never leaves, every
one of those kick-drops is a usable in/out point, and blends stay coherent even
across the breakdowns. The **BREAK** cue marks the biggest drop, but treat the
whole back half as drop-mix territory rather than relying on a single switch.

*Sources: [RA review](https://ra.co/reviews/12138) · [Discogs — Wars / When I Feel](https://www.discogs.com/release/4053326-Juk-Juk-Wars-When-I-Feel) · [Dazed — Juk Juk](https://www.dazeddigital.com/music/article/14664/1/juk-juk)*

---

## Bagarre — *Lemonsweet (Disco-Version)*

**Source:** SoundCloud capture (re-up by dee_seejay / MATLO44 — uploader, not artist) · **Crate:** SoundCloud
**Release:** Italo-disco; the "Disco-Version" 12″ cut. Cataloged early-1980s (~1982, Italian label Sauvage Musique); cover pressing reads *Estereo MC 2164*.
**Analysis:** 136.0 BPM · F# major (**2B**) · low energy · −22.7 LUFS (true peak −7.3 dBTP) · 6:20

A cult Italo-disco record, sung by **Ann O'Rack**, that's become a sought "disco
diggers" cut. The song is, per the SoundCloud blurb and lyric readings, *"about
doing LSD and losing oneself at Studio 54"* — a thinly veiled acid metaphor where
the woman collapses into a repeated incantation of **"54"**. That chant is the
track's hook and its strongest mix anchor. (The capture is from a SoundCloud re-up;
the on-screen uploader MATLO44 / dee_seejay is the digger, **not** the artist —
tagged here as Bagarre.)

It's a vintage, dynamic master — hence the quiet, un-brickwalled level
(−22.7 LUFS, peaks −7 dBTP); ReplayGain handles playback leveling, the dynamics
are intact. Energy reads "low" because the classifier is RMS-based and this is a
genuinely quiet recording, not a low-intensity track.

**How that shaped the cues:**

| Cue | Pad | Time | Rationale |
|-----|-----|------|-----------|
| IN | 1 | 0:10 | Short intro before the four-on-the-floor groove enters |
| MIX IN | 2 | 0:12 | Groove locks ~1 bar later — clean blend-in |
| BREAK | 3 | 2:26 | Deepest dip — the breakdown where the "54" acid-chant build sits |
| MIX OUT | 4 | 5:19 | ~30 bars of outro runway before the 6:20 end |

Steady disco kick = forgiving blends throughout. The **"54" chant breakdown**
(near the BREAK cue) is the moment to mix on or out of — it's the track's identity.

> **Verify in Traktor:** BPM read **136** — fast for disco. Could be the edit is
> genuinely uptempo or a librosa over-read. Re-confirm the grid by ear when the
> entry loads; if the beats don't line up, re-analyze in Traktor and re-run
> `pg traktor` to re-snap the cues.

*Sources: [Discogs — Lemonsweet (master)](https://www.discogs.com/master/154927-Bagarre-Lemonsweet) · [Discogs — Lemonsweet (Disco Version)](https://www.discogs.com/release/845052-Bagarre-Lemonsweet-Disco-Version) · [RateYourMusic — Bagarre](https://rateyourmusic.com/artist/bagarre)*
