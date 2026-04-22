---
layout: default
title: Desk Design
---

# Desk Design

> **Update (Apr 18):** CDJs dropped from the build (see the [strategy shift](equipment)). Desk now has two laptops running Reason at the central positions, and the Korg Kaossilator Pro+ takes a dedicated spot next to the mixer. Total width lands around ~1.9–2.2m depending on layout. The rest of the design (height-adjustable base, isolation, modularity) is unchanged.
>
> **Update (Apr 21–22):** Acoustic isolation plan locked in a modular first-pass build — Sylomer pads + gym-weight ballast under a simple table made from Ola's existing rack/side cards. Concrete slab paused (revisit in summer). **Friday Apr 24 is build day**; Thursday afternoon call to align.

## Equipment Dimensions

| Unit | W × D × H (mm) | Weight | Notes |
|------|----------------|--------|-------|
| Technics SL-1200MK7 | 453 × 353 × 169 | 9.6 kg | From Technics spec sheet |
| Allen & Heath Xone:96 | 336 × 410 × 109 | 7 kg | From A&H spec sheet |
| Korg Kaossilator Pro+ | ~246 × 198 × 47 | ~1.1 kg | **Verify against Korg spec sheet before desk build** |
| Laptop (13–14") | ~315 × 220 × 20 | ~1.5 kg | Generic estimate — depends on actual model |

## Layout

**Flat layout** — Kaossilator flat next to the mixer (default):

```
┌───────────┐ ┌─────────┐ ┌────────┐ ┌──────┐ ┌─────────┐ ┌───────────┐
│ Technics L│ │ Laptop A│ │ Mixer  │ │Kaoss.│ │ Laptop B│ │ Technics R│
│  453mm    │ │ (Reason)│ │ 336mm  │ │246mm │ │ (Reason)│ │  453mm    │
│  × 353mm  │ │  ~315mm │ │ × 410mm│ │×198mm│ │  ~315mm │ │  × 353mm  │
│  h: 169mm │ │         │ │ h:109mm│ │h:47mm│ │         │ │  h: 169mm │
└───────────┘ └─────────┘ └────────┘ └──────┘ └─────────┘ └───────────┘
```

Total width (flat): 453 + 315 + 336 + 246 + 315 + 453 = **2,118mm** of units + 5 × 30mm gaps = **~2,268mm** overall.

**Front-shelf layout** — Kaossilator on a shallow shelf in front of the mixer, laptops flanking the mixer directly:

```
┌───────────┐ ┌─────────┐ ┌────────┐ ┌─────────┐ ┌───────────┐
│ Technics L│ │ Laptop A│ │ Mixer  │ │ Laptop B│ │ Technics R│
│           │ │         │ │ ╔════╗ │ │         │ │           │
│           │ │         │ │ ║Kaos║ │ │         │ │           │
└───────────┘ └─────────┘ └────────┘ └─────────┘ └───────────┘
```

Total width (front-shelf): 453 + 315 + 336 + 315 + 453 = **1,872mm** of units + 4 × 30mm gaps = **~1,992mm** overall.

Front-shelf is tighter (~275mm narrower) and closer to the Paradise Garage booth footprint; flat gives the Kaossilator more elbow room for two-hand pad play.

## Key Measurements

| Measurement | Value |
|-------------|-------|
| Total width — flat layout | **~2,268mm** (≈ 2.27m) |
| Total width — front-shelf layout | **~1,992mm** (≈ 2.0m) |
| Depth (equipment only) | 453mm (Technics is the deepest) |
| Depth with cable space | ~500–550mm |
| Height difference | Turntables 169mm vs mixer/laptop ~109mm — same ~60mm delta as before |

> **Note:** Turntables are ~60mm taller than the mixer/laptops. Same options apply as in the CDJ design: recess the turntables into the surface, or raise the central row on a platform. The Kaossilator at only ~47mm tall fits comfortably on the mixer plane.

## Equipment Positioning

### Recommended: Turntables outside, laptops inside, mixer + Kaossilator central

```
┌─────────┐ ┌────────┐ ┌─────────┐ ┌────────┐ ┌─────────┐
│Technics │ │Laptop A│ │ Mixer + │ │Laptop B│ │Technics │
│(outside)│ │(inside)│ │ Kaoss.  │ │(inside)│ │(outside)│
└─────────┘ └────────┘ └─────────┘ └────────┘ └─────────┘
```

Carries over from the CDJ layout:

- **Isolation:** turntables furthest from mixer vibration and central workspace — needle-skip risk minimized
- **Short USB runs:** laptops next to the Xone:96 keep the two dual-USB cables tidy
- **Ergonomics:** hands naturally rest on whichever source is closest to the mixer; the Kaossilator sits within arm's reach of both

New consideration with the Reason rig:

- **Screen angle matters.** Unlike CDJs, laptop screens are part of the performance surface. Plan for ~15° tilt toward the DJ (laptop stands or a sloped shelf), with enough height that the screen doesn't occlude the mixer.

### Kaossilator placement options

1. **Flat, next to the mixer** — best two-hand pad play, full access to loop bank buttons (A/B/C/D), adds ~246mm to total width
2. **Front shelf / sloped lip in front of the mixer** — tighter footprint, works if the Kaossilator's height (~47mm) allows the shelf to sit just below the mixer's front edge
3. **Right of laptop B on the lip** — asymmetric, keeps mixer centered

Flat is the default for the initial build; revisit after playing the rig for a few sessions.

### Spacing

Leave **40–50mm between the turntable and whatever's next to it** — enough air gap for vibration isolation, close enough to reach both without shifting stance.

## Design Considerations

### Acoustic Isolation (Apr 21–22 plan)

Turntable isolation is still the core problem: bass from the speakers feeding back through the deck causes needle skip and rumble. The plan evolved from "build a heavy concrete slab on isolation pads" to a **modular, dismantlable first pass** — test the principle before committing to a 160kg slab.

**Current approach — simple table on Sylomer + weight ballast:**

1. **Platform:** a simple table built from Ola's existing side cards / rack units, sized to carry the rig.
2. **Decoupling layer:** [Tacos Sylomer](https://rodavigo.net/es/p/taco-sylomer-tipo-sr450-formato-100x100x37-mm-carga-maxima-350-kg-frecuencia-propia-8-hz-pvp-por-taco-ref-amc-707348/816707348) (Getzner SR-series) pads under the table legs / rack feet.
3. **Ballast:** 4 × 25kg gym weights bolted/placed on the platform to load the pads into their operating range.

**Why it has to be heavy** — the Sylomer pads only isolate correctly under the load they're rated for. Underload them and they act stiff (no isolation). Our target: ~200kg total (equipment + ballast) across 4 pads.

**Pad rating — the 8Hz vs 12Hz decision:**

| Rating | Isolates down to | Status |
|--------|-----------------|--------|
| 8Hz (SR450, 100×100×37mm) | Sub-30Hz (lower bound of the room) | **Dropped.** Needs ~850kg total to function; the 80×80×37mm form factor isn't stocked in Spain |
| **12Hz** | **~42Hz** (comfortably below the speakers' low end) | **Chosen.** Works at ~200kg load, within ±20% tolerance of the pad's rating |

**Ordered:** the primary set of 4 × 100×100×25mm SR450 pads + an additional 8 × 25kg variants to allow 3 pads under each rack unit for better weight distribution if the 4-pad layout feels unstable.

**Speakers:** stay stacked in a fixed central listening position. Since the listening sweet spot is fixed (sitting *or* standing doesn't change it much), no wheels needed on the main platform.

**Turntable-specific isolation (on top of the platform):**

- Rubber isolation feet under each turntable
- ~40–50mm air gap between each turntable and its neighbor
- If needle-skip persists after the platform build, add a dedicated turntable shelf (heavy MDF/stone on sorbothane) and re-test

**Paused: the concrete slab.** The original plan was 8 × 20kg bags of fine premix concrete + iron reinforcement mesh, ~160kg total (70cm × 250cm × ~9.5cm thick), poured into one or two molds (two 80kg slabs is a two-man job; one 160kg slab is a 3–4 man job). It's still a good idea — the natural mass couples well with the pads, and the room resonance stays intact — but it's deferred. Revisit once the modular rig is running and we know what's missing.

**Alternative speaker-only isolation — noted, not chosen.** Putting 20kg weights on Sylomer pads *under the speaker stands* would isolate the speakers from the floor directly. We're not doing this because it breaks the room-coupling that gives the low end its natural character — but it's a fallback if the platform approach under-delivers.

### Ergonomics

| Position | Desk Height |
|----------|-------------|
| Standing | 90–100cm |
| Seated (stool) | 70–75cm |

### Cable Routing

Cable counts with the Reason + Kaossilator rig:

- Each turntable: 1x RCA pair + 1x ground + 1x power (≈ 3 cables × 2 decks = 6)
- Each laptop: 1x USB-C → Xone:96 USB + 1x power (≈ 2 cables × 2 laptops = 4)
- Kaossilator Pro+: 1x RCA pair (line out to mixer CH5) + 1x power + optional MIDI in from Reason or USB (≈ 2–3 cables)
- Mixer: 1x XLR master out + 1x power (≈ 2 cables)

Roughly **~14–15 cables** at full deployment. Compared to the CDJ design: 2x USB replaces the CDJ RCA pairs, the Kaossilator adds only a single channel pair. Route channels cleanly; consider a cable dropbox at the rear.

### Ventilation

No CDJs means less heat — just mixer + two laptops + Kaossilator (which runs cool). Laptops need airflow under them (cooling stands or ventilated riser). Leave at least 50mm clearance behind units.

### Materials

- **Recommended:** MDF or plywood, 18mm+ thickness
- **Avoid:** Glass (resonance), thin metal (vibration), particle board (weak)
- **Finish:** Consider acoustic dampening material on inner surfaces

### Total Weight

Reason-rig version: 2x 9.6kg (Technics) + 7kg (mixer) + 2x ~1.5kg (laptops) + ~1.1kg (Kaossilator) = **~30kg**, down from ~37kg with CDJs. Still build sturdy — the turntables dominate anyway.

---

## Design Evolution

### Apr 12 (Ola's Proposal) — still in scope

- **Motorized sit/stand base** on Ola's rack carts — Wallapop frame to be sourced
- **Modularity** — all gear lifts off the surface, no flush-mounting, quick-release cable management
- **Dual-use workspace** — acrylic/plastic cover panel when in "Ola's workspace" mode
- **Power filtering** — Ola contributing a rack power-supply filter, lives in the cart base

### Apr 18 — Reason pivot, desk implications

- CDJ footprint removed → desk shortens by ~350mm, or stays the same width and gains breathing room for the Kaossilator and screen real estate
- Two laptop positions need tilt/stand provisions (sloped shelf or laptop risers built in)
- 2x USB-C runs added between laptops and mixer — keep short
- Kaossilator Pro+ needs either a flat slot next to the mixer (~246mm wide) or a front-shelf cut-out
- **Vinyl-as-MIDI-controller** (Ola's Apr 12 idea): open question in light of the pivot. With Reason + Kaossilator already providing the live creative layer, is this still the highest-leverage use of turntable data, or has the motivation shifted? Worth a short conversation with Ola before the desk build locks in — the idea may still be worth chasing for a different reason now.

### Apr 21–22 — Acoustic isolation pivot

- Concrete slab paused (too much work for an unvalidated design). Revisit in summer.
- Modular platform on Sylomer + gym-weight ballast chosen as the proof-of-concept — cheap, dismantlable, resellable.
- Sylomer pads ordered. 12Hz rating (not 8Hz) → isolation down to 42Hz, realistic at ~200kg load.
- Thursday Apr 23 afternoon: call to align on final table design.
- Friday Apr 24: build day. Ola does the morning parts run; Andreas in the studio afternoon.

### Next Steps

- [ ] **Thursday Apr 23 afternoon:** call to finalize table design and purchase list
- [ ] **Friday Apr 24:** build the modular platform (Ola: morning parts run; Andreas: studio afternoon)
- [ ] Acquire 4 × 25kg gym weights for ballast (Wallapop — resellable later)
- [ ] Verify Sylomer load window once rig is assembled; order extra pads if layout shifts to 3-per-rack-unit
- [ ] Ola reviews new layout against Apr 18 drawings — does the shorter desk or the "same width, more breathing room" version win?
- [ ] Decide Kaossilator placement: flat next to mixer vs. front-shelf cut-out
- [ ] Verify Kaossilator Pro+ dimensions against Korg spec sheet (value in the table above is from memory, confirm before final cut)
- [ ] Spec laptop stands / tilt (maker-built vs off-the-shelf)
- [ ] Re-source secondhand motorized desk frame (Wallapop) at the new width
- [ ] Update quick-release cable plan for 2x USB-C + Kaossilator channel pair + optional MIDI
- [ ] Decide with Ola whether vinyl-as-MIDI-controller research continues given the pivot
