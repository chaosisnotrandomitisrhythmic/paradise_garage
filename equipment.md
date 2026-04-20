---
layout: default
title: Equipment
---

# Equipment

> **Strategy shift (Apr 18):** CDJs dropped. After watching a *A Guy Called Gerald* live-jam video, the build pivoted from Pioneer-standard "prep + play" toward a live, creative rig — Reason on two laptops as the primary sound engine, turntables for vinyl source, a Korg Kaossilator Pro+ as the live phrase-synth / loop instrument, and Traktor only as a fallback for pure DJ gigs. Full context on the [Inspiration](inspiration) page.

## Turntables (x2) — Technics SL-1200MK7

| Spec | Value |
|------|-------|
| Price | ~€960 each / **Subtotal: €1,920** |
| Dimensions | 453 x 353 x 169 mm (W x D x H) |
| Weight | 9.6 kg |
| Drive | Direct drive, coreless motor |

The industry standard. Dual role: play vinyl, **and** act as a sound source that feeds the live rig — the vinyl signal can be sampled into the Kaossilator Pro+'s loop banks or into Reason for further mangling.

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

## Live phrase synth & looper — Korg Kaossilator Pro+

| Spec | Value |
|------|-------|
| Owner | Andreas (already owns) |
| Role | Touch-pad phrase synthesizer + 4-bank loop recorder |
| Signal | Line out → dedicated mixer channel strip (CH5); line/mic in for sampling incoming audio |
| Sync | MIDI clock slave (locks loops to Reason's master tempo) |
| Dimensions | ~246 × 198 × 47 mm (verify against Korg spec sheet before desk build) |

Centerpiece of the live rig now that the CDJs are gone. Distinct from a Kaoss Pad — the Kaossilator Pro+ **generates** phrases rather than processing a source: 200+ built-in sounds (leads, basses, drums, SFX) played on the touchpad with scale/key constraints, then captured into any of **4 loop banks (A/B/C/D)** that can be layered live. The gate arpeggiator gives each touch a rhythmic feel without touching a DAW.

It also has a line/mic input, so it can sample and loop audio from the mixer (via a send) or from the turntables directly — but in the default rig it lives on its own channel strip as a **sound source**, not in an FX send/return loop. That frees Send 1/Return A for future hardware FX.

Why it fits the Gerald-style rig:

- Performs like an instrument — scales, keys, tap tempo, gate arp — not like a playback deck
- 4 loop banks = four parallel musical layers you can build, mute, and re-trigger on the fly
- MIDI sync keeps it locked to Reason's tempo so the loops stay in time with whatever the laptops are doing
- Self-contained: phrase + loop + FX, no laptop required

## Mixer (x1) — Allen & Heath Xone:96

| Spec | Value |
|------|-------|
| Price | ~€1,870 |
| Dimensions | 336 x 410 x 109 mm (W x D x H) |
| Weight | 7 kg |
| Channels | 6+2 |
| Signal path | Fully analog |
| Soundcard | 32-bit, 24-channel USB (dual ports) |

The sound-quality winner, and now the hub of everything — it's what makes the Reason + turntables + Kaossilator architecture work. Dual HPF/LPF filters per channel, deep sub-bass, 3D soundstage, no harshness. Rated by reviewers above the Pioneer DJM-V10 and DJM-A9 on sound quality (filter character, analog summing).

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
| 9/10 | Send 1 (free — available for hardware FX loop or feeding Kaossilator input) |
| 11/12 | Master L/R mix (used for session recording) |

**What this enables in the new rig:**

1. **Two-laptop live Reason** — USB1 for laptop A, USB2 for laptop B. Each sends 6 stereo pairs into mixer channels that behave exactly like hardware sources. Both mixed on the analog summing bus.
2. **DVS on demand** — timecode vinyl on the Technics can still drive Traktor or Serato through the same sound card if a gig calls for a "normal" DJ set.
3. **Record every session** — master bus on USB channels 11/12, straight into Ableton/Logic via USB.
4. **Software FX send/return via USB** — route audio out to Ableton/Reason for processing (reverb, granular, etc.), return through the mixer. Runs independently of any hardware send/return loop.

**Limitations:** no mic preamps, no Hi-Z instrument inputs, no phantom power. Not a tracking interface — but for DJ + live-Reason use it's exactly right.

### Send/Return & External FX Integration

The Xone:96 has **2 stereo sends + 4 stereo returns** on the rear panel, plus a dedicated master insert.

**Kaossilator sampling path (optional):** any channel → Send 1 → Kaossilator Pro+ line in → sample into loop bank → Kaossilator line out appears on its own channel strip. Use this when you want to grab a phrase from the turntables or a Reason laptop into the Kaossilator's loop banks rather than playing it back straight.

**Software FX loop:** USB → Reason/Ableton FX rack → back via USB. Lives on its own send/return pair, independent of any hardware routing.

**Future hardware FX:** Send 2 / Return B is free for adding a proper FX box (Kaoss Pad, Eventide H9, pedals) later if the rig wants one.

## Channel Layout

The Xone:96 has 6 stereo input channels. Each of the 2 USB ports can feed up to 6 stereo pairs into the mixer, but in practice one USB → one channel strip is the cleanest mapping for a two-laptop Reason rig (Reason does its own internal summing before hitting the mixer).

| Channel | Source | Input Type |
|---------|--------|-----------|
| CH1 | Technics L | Phono |
| CH2 | Technics R | Phono |
| CH3 | Laptop A — Reason (USB port 1, stereo mixdown from Reason) | Line (USB) |
| CH4 | Laptop B — Reason (USB port 2, stereo mixdown from Reason) | Line (USB) |
| CH5 | Korg Kaossilator Pro+ | Line |
| CH6 | Aux / guest deck / drum machine | Line |
| Return A | Free — future hardware FX | Stereo return |
| Return B | Software FX via USB (Reason/Ableton FX rack) | Stereo return |

**Scaling up:** if a track calls for multi-timbral routing (e.g., Reason's drums on one channel, synths on another, bass on a third), the same laptop's USB port can feed additional channel strips — up to 6 stereo pairs per port. Start with the stereo mixdown; add per-bus routing when a song demands it.

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
