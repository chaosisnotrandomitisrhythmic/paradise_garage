---
layout: default
title: Equipment
---

# Equipment

> **Strategy shift (Apr 18):** CDJs dropped. After watching a *A Guy Called Gerald* live-jam video, the build pivoted from Pioneer-standard "prep + play" toward a live, creative rig — Reason on two laptops as the primary sound engine, turntables for vinyl source, Korg Kaoss Pad as the live FX/sampling surface, and Traktor only as a fallback for pure DJ gigs. Full context on the [Inspiration](inspiration) page.

## Turntables (x2) — Technics SL-1200MK7

| Spec | Value |
|------|-------|
| Price | ~€960 each / **Subtotal: €1,920** |
| Dimensions | 453 x 353 x 169 mm (W x D x H) |
| Weight | 9.6 kg |
| Drive | Direct drive, coreless motor |

The industry standard. Dual role: play vinyl, **and** act as the source of sounds that get captured, looped, and mangled live through the Kaoss Pad and Reason.

## Sound engine — Reason (2x laptops)

| Spec | Value |
|------|-------|
| Vendor | Reason Studios (Stockholm, Sweden) |
| Role | Primary sound-design and performance engine |
| License | TBD — perpetual vs. Reason+ subscription |
| Per-laptop I/O | 8+ channels out via Xone:96 USB |

Reason replaces the CDJ-3000s. Two laptops, **intentionally unsynced**, each running an independent Reason session — the drift between them is the performance surface, woven by hand. Each laptop routes 8+ audio channels out through the Xone:96's dual USB sound card, so individual racks/synths/drum machines can be mixed on the mixer's analog bus the same way external hardware would be.

Why Reason:

- **Rack metaphor** — synths, samplers, drum machines wired up like physical gear. Rewards live jamming over arrangement.
- **Creative range** — huge sound bank + loop building + live manipulation, far beyond what a CDJ offers
- **Portable studio** — the whole rig fits in two laptop bags
- **One-machine ethos** — produce sounds on the fly, no pre-made tracks, transitions feel like weather rather than mixing

## Live FX / sampling — Korg Kaoss Pad

| Spec | Value |
|------|-------|
| Owner | Andreas (already owns) |
| Role | Touch-surface FX + live sampler |
| Signal | Stereo send/return into Xone:96 (Send 1 → Return A) |

Centerpiece of the live rig now that the CDJs are gone. Grabs audio from any mixer channel via send, captures loops on the fly, then pitch-shifts / stutters / gates / filters them via the touchpad. The built-in sampler is what lets it act as a performance instrument, not just an FX box — you layer captured phrases over whatever's playing without ever touching a laptop.

Independent of the USB FX loop going to Reason, so Kaoss Pad and software FX run in parallel on two separate send/returns.

## Mixer (x1) — Allen & Heath Xone:96

| Spec | Value |
|------|-------|
| Price | ~€1,870 |
| Dimensions | 336 x 410 x 109 mm (W x D x H) |
| Weight | 7 kg |
| Channels | 6+2 |
| Signal path | Fully analog |
| Soundcard | 32-bit, 24-channel USB (dual ports) |

The sound-quality winner, and now the hub of everything — it's what makes the Reason + turntables + Kaoss Pad architecture work. Dual HPF/LPF filters per channel, deep sub-bass, 3D soundstage, no harshness. Beats Pioneer DJM-V10 and DJM-A9 in blind listening tests.

### Why Xone:96 over Pioneer?

- **Analog signal path** — no digital conversion in the mix bus
- **Filters** — universally rated as the best in any DJ mixer, smooth resonance
- **Sound** — "liberated, cinematic 3D spatiality" vs Pioneer's "compressed upper-mids"
- **6+2 channels** — enough for turntables + two Reason laptops + guest/aux
- **Price** — €1,870 vs €3,300 for the DJM-V10

### Built-in Dual Sound Card (Audio Interface)

The Xone:96 has a **dual 32-bit/96kHz USB sound card** — two independent audio interfaces built into the mixer. No external interface needed, and it is exactly what makes two-laptop Reason work without a hub.

| Spec | Value |
|------|-------|
| USB ports | 2 (independent, rear panel) |
| Channels per USB | 12 in + 12 out (6 stereo pairs each way) |
| Total I/O | 24 channels across both ports |
| Bit depth | 32-bit |
| Sample rate | Up to 96 kHz |
| macOS driver | Class-compliant (plug and play) |

**USB Channel Routing:**

| USB Channels | Source |
|---|---|
| 1–8 | Stereo input channels (line/phono, follows rear panel switch) |
| 9/10 | Send 1 (Kaoss Pad loop) |
| 11/12 | Master L/R mix (used for session recording) |

**What this enables in the new rig:**

1. **Two-laptop live Reason** — USB1 for laptop A, USB2 for laptop B. Each sends 6 stereo pairs into mixer channels that behave exactly like hardware sources. Both mixed on the analog summing bus.
2. **DVS on demand** — timecode vinyl on the Technics can still drive Traktor or Serato through the same sound card if a gig calls for a "normal" DJ set.
3. **Record every session** — master bus on USB channels 11/12, straight into Ableton/Logic via USB.
4. **Software FX send/return via USB** — route audio out to Ableton/Reason for processing (reverb, granular, etc.), return through the mixer. Runs independently of the hardware Kaoss Pad loop.

**Limitations:** no mic preamps, no Hi-Z instrument inputs, no phantom power. Not a tracking interface — but for DJ + live-Reason use it's exactly right.

### Send/Return & External FX Integration

The Xone:96 has **2 stereo sends + 4 stereo returns** on the rear panel, plus a dedicated master insert.

**Kaoss Pad loop:** any channel → Send 1 → Kaoss Pad in → Kaoss Pad out → Return A. The return has its own fader and EQ, so the effect blends in and out of the mix independently of the source channel.

**Software FX loop:** USB → Reason/Ableton FX rack → back via USB. Runs on the second send/return path, totally independent of the hardware Kaoss Pad.

Two independent FX chains running at the same time is a big part of why this mixer was chosen.

## Channel Layout

| Channel | Source | Input Type |
|---------|--------|-----------|
| CH1 | Technics L | Phono |
| CH2 | Technics R | Phono |
| CH3 | Laptop A — Reason (USB1) | Line (USB) |
| CH4 | Laptop B — Reason (USB2) | Line (USB) |
| CH5 | Guest deck / drum machine | Line |
| CH6 | Aux / free | Line |
| Return A | Korg Kaoss Pad | Stereo return |
| Return B | Software FX (Reason/Ableton) | Stereo return |

## DJ software (for the fallback case)

When the gig calls for a pure DJ set rather than a live jam:

| Tool | Role |
|------|-------|
| **Traktor Pro** | Primary DJ software — runs on one of the laptops, uses DVS through the Xone:96 |
| **Rekordbox** | Legacy library (track prep, cue points, tags) |
| **[Lexicon](https://lexicondj.com/)** | Library sync: Rekordbox ↔ Traktor (bidirectional, preserves cues/grids/tags) |

Open question: **do we keep Rekordbox as the canonical library and sync out to Traktor, or switch the library home to Traktor?** Worth an afternoon of experimenting with Lexicon before committing either way.

## Accessories

| Item | Est. Price |
|------|-----------|
| 2x Cartridges (Ortofon Concorde MkII Mix) | ~€200 |
| 1x Headphones (Sennheiser HD 25) | ~€130 |
| Cables (RCA, XLR master out, USB) | ~€100–150 |

## Design Principles (Apr 18 revision)

The original design principles assumed the Pioneer club-standard path. With the Reason pivot they update to:

1. **Live over playback** — the rig is optimized for building sound in real time, not for chaining finished tracks. A Guy Called Gerald's "becoming the track" ethos over Larry Levan's "play the room."
2. **Portable studio** — everything still fits in a car for forest raves and B2B sets; two laptop bags are easier to move than two CDJs anyway.
3. **Standard signal path** — turntables + Xone:96 are still the bits clubs recognize and can provide as backline. The Reason laptops are what you bring. The mixer is still the industry standard.
4. **Resale / reuse** — Technics and Xone:96 hold value; Reason licenses and laptops are assets regardless of whether the desk happens.
5. **Room to grow** — 6+2 mixer channels, two FX send/returns, and two independent USB sound cards leave room for guest laptops, drum machines, and modular gear.

## Software & Production Tools

| Tool | Owner | Notes |
|------|-------|-------|
| **Reason** | TBD | Primary creative engine in the new rig |
| Arturia Pigments | Andreas | Shareable on 5 machines — usable inside Reason via Rack Extensions/VST |
| Arturia V Collection (full bundle) | Ola | All Arturia synths |
| Sononym | Both exploring | AI-powered sample search engine (free 30-day trial) |
| Traktor Pro | TBD | Fallback DJ software |
| Rekordbox | Andreas | Legacy library — Lexicon sync keeps it aligned with Traktor |
| Lexicon | TBD | Rekordbox ↔ Traktor library sync |

## Purchase Blocker

Equipment purchase is still **blocked by SL (Sociedad Limitada) setup** — all gear through the business for IVA deductibility. Next step: consult Sergio (gestor). See [CHA-190](https://linear.app/chaos-is-rhythmic/issue/CHA-190/tax-restructure-autonomo-sl-with-multiple-activities).

The smaller gear bill (no CDJs) softens the blocker somewhat — the hardware that's left is Technics + Xone:96 + accessories, about half the original capital outlay.

## Where to Buy (Madrid)

- [Madrid HiFi](https://www.madridhifi.com/) — carries Allen & Heath and Technics
- [DJMania](https://djmania.es/)
- [Thomann España](https://www.thomann.es/) — often best online prices
- [ProfesionalDJ](https://www.profesionaldj.es/) — financing available
