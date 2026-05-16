---
layout: default
title: Traktor + Kaossilator integration
---

# Traktor + Kaossilator integration

How the Korg Kaossilator Pro+ slots into the Xone:96 + Traktor DVS rig. Written for the **single-laptop starting config** (one laptop running Traktor with timecode vinyl on both Technics). The two-laptop Reason endstate lives in [Equipment](equipment#channel-layout).

> **Why this page exists:** the canonical [equipment](equipment) channel layout assumes two laptops (CH3+CH4 for Reason) with the Kaossilator on CH5. With one laptop, CH4 becomes free and the Kaossilator gets a proper main channel — better EQ, filter, and crossfader options.

## Signal flow (single-laptop config)

```
[TT1 phono] ──► [Xone:96 CH1]
[TT2 phono] ──► [Xone:96 CH2]
[Laptop USB-A] ──► [Xone:96 CH3]  (Traktor + DVS)
[Kaossilator Pro+ line out L/R] ──► [Xone:96 CH4 line input]

[Laptop USB-MIDI] ──► [Kaossilator MIDI IN]  (optional, see "MIDI clock sync")
```

### Channel allocation

| Channel | Source | Input | Role |
|---------|--------|-------|------|
| CH1 | Technics SL-1210 MK7 #1 | Phono | DVS deck A (Traktor timecode) |
| CH2 | Technics SL-1210 MK7 #2 | Phono | DVS deck B (Traktor timecode) |
| CH3 | Laptop (Traktor) | USB-A | Cue/headphone out, master through Xone |
| CH4 | **Kaossilator Pro+** | Line | Live phrase synth + 4-bank looper |

**Why CH4 over Return 1:** the returns lack 3-band EQ, channel filter, and crossfader assign. Putting the Kaossilator on a main channel turns it into a playable instrument rather than a fixed-level FX bus.

## MIDI clock sync

Two paths, pick based on tonight's appetite for cable wrangling.

### Path A — Tap tempo only (no extra hardware)

- Hit **TAP** on the Kaossilator in time with the playing track
- Close enough for short loops over a vinyl mix
- Drifts on longer phrases — fine for 4–8 bar interjections
- **Use tonight** if it's your first session and DVS calibration is already a lot to absorb

### Path B — Tight MIDI clock sync (one extra cable)

- USB→5-pin DIN MIDI cable (~€15, e.g. Roland UM-ONE or any generic — Thomann sells these)
- Plug: laptop USB → MIDI cable → Kaossilator **MIDI IN**
- Traktor → **Preferences → MIDI Clock → Send Clock** → select your USB-MIDI device
- Kaossilator → MIDI mode = **External Sync**
- Verify: hit play in Traktor, Kaossilator's BPM display follows the deck
- The Xone:96's MIDI port is mostly for controlling the mixer itself, not clock distribution — go direct from laptop, skip the mixer's MIDI

**Don't pile MIDI sync on top of first-night DVS setup.** Get DVS feeling solid first, add MIDI clock another evening.

## The killer feature: scale lock

The Kaossilator's scale-lock mode constrains the XY pad to only musically correct notes for a given key. Combined with Traktor's key-aware library:

1. Glance at the current track's Camelot key in Traktor (your `pg ingest` already analyzes this — same metadata)
2. Set the Kaossilator scale to match. E.g., track is **8A (Am)** → Kaossilator scale = A minor
3. Now every XY-pad touch is musically correct — no wrong notes

This is what elevates the Kaossilator from a toy to a playable melodic instrument mid-set.

## Three integration patterns

### 1. Pre-drop builder

8 bars before the next track's drop:

- Record a kick + hat pattern in **Bank A**
- Overdub a synth arp in **Bank B** over it
- At the drop point: mute the Kaossilator channel for 1 bar of silence
- Cut to the next track with the Kaossilator loop still riding underneath

A Jon Hopkins–style "your build, not the producer's."

### 2. Instrumental bridge between vinyl tracks

Use the Kaossilator as a transition rather than as a layer:

- Fade out both turntable channels
- Bring up a pre-recorded Kaossilator loop in a compatible Camelot key
  (outgoing 8A → loop in 8A, 9A, or 7A)
- 8-bar "your turn" interlude before mixing in the next record
- Makes the set feel composed rather than just sequenced

### 3. Live percussion layer

A "fourth deck" that's always available:

- At the start of the night, record a 16th-note shaker or rim-shot pattern in **Bank C**
- Leave it muted on the channel
- Drop it in during droney/sparse tracks for extra movement
- No new musical content — just rhythmic density on demand

## Tonight's pre-flight checklist

Minimum viable session, in order:

- [ ] Native Access installed → Traktor Pro 4 installed
- [ ] Xone:96 detected by macOS (System Settings → Sound → Output)
- [ ] Traktor → Preferences → Audio Setup → device = Xone:96
- [ ] Traktor → Preferences → Mix Recorder → input from Xone:96 USB ch 11/12 (master capture)
- [ ] Phono cables: TT1 → CH1 phono, TT2 → CH2 phono
- [ ] Drop one Neon Pink timecode vinyl on each turntable
- [ ] Traktor → Preferences → Timecode Setup → calibrate decks A + B
- [ ] **DVS works standalone** — confirm before adding anything else
- [ ] Kaossilator line out (L/R) → CH4 line input
- [ ] Kaossilator volume up, play a phrase, confirm signal on CH4 meter
- [ ] *(Later)* MIDI clock sync if Path B above

## Scaling up to two laptops

When the second laptop joins (Reason on USB-B):

- CH3 → Laptop A (Traktor)
- CH4 → Laptop B (Reason)
- CH5 → Kaossilator Pro+ *(its canonical home — see [Equipment](equipment#channel-layout))*
- CH6 → guest / drum machine / aux

The single-laptop config is a starting position, not a permanent compromise.
