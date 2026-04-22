---
layout: default
title: Desk Design
---

# Desk Design

> **Update (Apr 18):** CDJs dropped from the build (see the [strategy shift](equipment)). Desk now has two laptops running Reason at the central positions, and the Korg Kaossilator Pro+ takes a dedicated spot next to the mixer. Total width lands around ~1.9–2.2m depending on layout. The rest of the design (height-adjustable base, isolation, modularity) is unchanged.
>
> **Update (Apr 22 afternoon):** Build plan simplified further. Skipping the concrete-molding step entirely for the proof-of-concept — the ballast is **dry concrete bags dropped straight into the side cards**, not gym weights and not molded blocks. Leroy Merlin order placed for delivery **Friday Apr 24 (build day)**: 2× phenolic boards (21mm) + 4× 25kg Hormigón Seco H25 bags. ~€150 materials + €50 express delivery. Invoiced under Andreas's autónomo (VAT deductible). Details in the section below.

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

**Current approach — simple table on Sylomer + concrete-bag ballast:**

1. **Platform:** Ola's existing side cards with tops and wheels removed, used as legs. A 21mm phenolic board cut to size becomes the new top surface. Center support added for stiffness if the span calls for it.
2. **Decoupling layer:** [Tacos Sylomer](https://rodavigo.net/es/p/taco-sylomer-tipo-sr450-formato-100x100x37-mm-carga-maxima-350-kg-frecuencia-propia-8-hz-pvp-por-taco-ref-amc-707348/816707348) (Getzner SR-series) pads lifted under the side-card legs once they arrive.
3. **Ballast:** 2× 25kg bags of dry-mix concrete (Hormigón Seco H25) **dropped straight into the side cards**. No molding step for the PoC. 2 more bags ordered as spare stock for later handle-equipped weight molds (see "future upgrades" below).

**Why it has to be heavy** — the Sylomer pads only isolate correctly under the load they're rated for. Underload them and they act stiff (no isolation). Target: ~200kg total on the 4 pads, inside the 12Hz pad's ±20% window.

**Mass budget (Ola, Apr 22):**

| Component | Weight (kg) |
|-----------|------------:|
| Table top, 21mm phenolic | 18 |
| Rack boards ×2 | 9 |
| Carts (10kg each) ×2 | 10 |
| Andy's gear | 3 |
| Power cord / block | 5 |
| Ola's gear (stays on the desk) | 4 |
| Keyboard drawer | 100 |
| **Subtotal** | **149** |
| Ideal target | 200 |
| **Additional ballast needed** | **51** |

→ **Two concrete bags (50kg) lands us on target.** The other two bags in the order are held back as stock for later. Numbers are Ola's spreadsheet estimates; we'll weigh-in on build day and add bags if anything comes in lighter than expected.

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

**Order (Leroy Merlin, placed Apr 22 ~16:16, delivery Fri Apr 24):**

| Item | Qty | Notes |
|------|-----|-------|
| Phenolic board, 21mm (Albramat), ~2.5×1.2m | 2 | Cut to size on build day — straight cuts only. Leftover wood kept for later concrete-weight molds. |
| Hormigón Seco H25, 25kg bag | 4 | 2 as active ballast + 2 as spare stock. €2.55 each incl. VAT. |
| Screws | existing | Ola has these. |
| **Materials subtotal** | | **~€151** |
| Express delivery (viernes 24 abril) | 1 | €49.90 — the boards (2.5×1.2m) don't fit in a car, so pickup was ruled out. |
| **Order total** | | **~€201** |

Placed on Andreas's Leroy Merlin account (credentials shared via 1Password), invoiced under Andreas's autónomo (NIE Y2266100Q, domicilio fiscal Calle la Esperanza 10 3D 28012 Madrid) for IVA deductibility. Paid with Andreas's saved card (designated via 1Password share).

**Paused: the concrete slab.** The original plan was 8 × 20kg bags of fine premix concrete + iron reinforcement mesh, ~160kg total (70cm × 250cm × ~9.5cm thick), poured into one or two molds (two 80kg slabs is a two-man job; one 160kg slab is a 3–4 man job). It's still a good idea — the natural mass couples well with the pads, and the room resonance stays intact — but it's deferred. Revisit once the modular rig is running and we know what's missing.

**Alternative speaker-only isolation — noted, not chosen.** Putting 20kg weights on Sylomer pads *under the speaker stands* would isolate the speakers from the floor directly. We're not doing this because it breaks the room-coupling that gives the low end its natural character — but it's a fallback if the platform approach under-delivers.

**Desk height trade-off.** With the side cards fixing the base height, the desk ends up **a couple of cm lower than Andreas's original target**. Adjustable later (taller feet / raised surface / re-stack) — not a PoC blocker.

**Future upgrades (if the PoC works):**

- **Mold handle-equipped concrete weights** from leftover phenolic wood + the spare concrete bags. Ola's plan: square blocks with a handle each, portable enough to also slide under the speaker stands as an alternative isolation test. Starts to look intentionally industrial.
- **Extra Sylomer pads** if the 4-pad layout feels unstable — Ola ordered 8 × 25kg variants alongside the primary set so we can go to 3 pads under each rack unit without re-ordering.

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

- **Apr 21:** concrete slab paused (too much work for an unvalidated design). Modular Sylomer platform chosen for the PoC. Sylomer pads ordered — 12Hz rating (not 8Hz), isolation down to 42Hz at realistic ~200kg load.
- **Apr 22 morning:** Andreas + Ola aligned on gym weights as ballast. Call scheduled for Thursday.
- **Apr 22 afternoon:** build plan simplified again. Use Ola's existing side cards as legs (tops + wheels off), add a 21mm phenolic top cut to size, drop concrete bags directly into the side cards as ballast (no molding). Ola's mass budget arrived at **149kg already on the table → only 2 bags of ballast needed** to hit the 200kg target. Car pickup ruled out (boards are 2.5×1.2m, won't fit). Leroy Merlin order placed on Andreas's account (~16:16) for Fri Apr 24 express delivery: 2× phenolic boards + 4× concrete bags (2 active, 2 spare), ~€201 all in. Invoice under Andreas's autónomo (NIE Y2266100Q), paid with Andreas's saved card.
- **Friday Apr 24:** build day. Ola in the studio in the morning; Andreas joins in the afternoon. Sylomer pads may or may not arrive — if not, build the table and lift it onto the pads when they land.

### Next Steps

- [x] ~~Thursday Apr 23 afternoon: call to finalize table design~~ — superseded by Apr 22 afternoon sign-off
- [x] ~~Acquire gym weights~~ — replaced by 25kg Hormigón Seco H25 bags as in-place ballast
- [x] ~~Car pickup of boards~~ — ruled out (2.5×1.2m doesn't fit in a hatchback)
- [x] Leroy Merlin order placed on Andreas's account, paid, invoiced to autónomo
- [ ] **Friday Apr 24:** build day — Ola in studio morning, Andreas afternoon; materials delivered same day
- [ ] Weigh the rig on build day and add more bags if the 2-bag ballast comes in under the 200kg target
- [ ] Verify Sylomer load window once rig is assembled; extra 8×25kg variants on standby for 3-per-rack-unit layout
- [ ] After PoC validates: mold handle-equipped concrete weights from leftover phenolic + spare bags
- [ ] Ola reviews new layout against Apr 18 drawings — does the shorter desk or the "same width, more breathing room" version win?
- [ ] Decide Kaossilator placement: flat next to mixer vs. front-shelf cut-out
- [ ] Verify Kaossilator Pro+ dimensions against Korg spec sheet (value in the table above is from memory, confirm before final cut)
- [ ] Spec laptop stands / tilt (maker-built vs off-the-shelf)
- [ ] Re-source secondhand motorized desk frame (Wallapop) at the new width
- [ ] Update quick-release cable plan for 2x USB-C + Kaossilator channel pair + optional MIDI
- [ ] Decide with Ola whether vinyl-as-MIDI-controller research continues given the pivot
