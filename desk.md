---
layout: default
title: Desk Design
---

# Desk Design

> **Update (Apr 18):** CDJs dropped from the build (see the [strategy shift](equipment)). Desk now has two laptops running Reason at the central positions, and the Korg Kaoss Pad takes a dedicated spot next to the mixer. Total width shrinks from ~2m to ~1.6m. The rest of the design (height-adjustable base, isolation, modularity) is unchanged.

## Equipment Dimensions

| Unit | W x D x H (mm) | Weight |
|------|----------------|--------|
| Technics SL-1200MK7 | 453 x 353 x 169 | 9.6 kg |
| Allen & Heath Xone:96 | 336 x 410 x 109 | 7 kg |
| Korg Kaoss Pad (KP3+) | 170 x 200 x 48 | ~0.9 kg |
| Laptop (13–14") | ~315 x 220 x 20 | ~1.5 kg |

## Layout

```
┌───────────┐ ┌─────────┐ ┌────────┐ ┌──────┐ ┌─────────┐ ┌───────────┐
│ Technics L│ │ Laptop A│ │ Mixer  │ │Kaoss │ │ Laptop B│ │ Technics R│
│  453mm    │ │ (Reason)│ │ 336mm  │ │ Pad  │ │ (Reason)│ │  453mm    │
│  x 353mm  │ │  ~315mm │ │ x 410mm│ │170mm │ │  ~315mm │ │  x 353mm  │
│  h: 169mm │ │         │ │ h:109mm│ │      │ │         │ │  h: 169mm │
└───────────┘ └─────────┘ └────────┘ └──────┘ └─────────┘ └───────────┘
├──────────────────── ~2,250mm (with 30mm gaps) ──────────────────────┤
```

Alternative tighter layout — Kaoss Pad in front of the mixer on a shallow shelf, laptops flanking the mixer directly:

```
┌───────────┐ ┌─────────┐ ┌────────┐ ┌─────────┐ ┌───────────┐
│ Technics L│ │ Laptop A│ │ Mixer  │ │ Laptop B│ │ Technics R│
│           │ │         │ │ ╔════╗ │ │         │ │           │
│           │ │         │ │ ║KP3+║ │ │         │ │           │
└───────────┘ └─────────┘ └────────┘ └─────────┘ └───────────┘
├─────────────────── ~1,900mm (with 30mm gaps) ──────────────────┤
```

Front-shelf layout is tighter and closer to the Paradise Garage booth footprint; flat layout gives the Kaoss Pad more elbow room for two-hand performance.

## Key Measurements

| Measurement | Value |
|-------------|-------|
| Total width — flat layout | **~2,250mm** |
| Total width — front-shelf layout | **~1,900mm** |
| Depth (equipment only) | 453mm |
| Depth with cable space | ~500–550mm |
| Height difference | Turntables 169mm vs mixer/laptop ~109mm — same ~60mm delta as before |

> **Note:** The turntable height delta from the mixer/laptops is the same as before (turntables ~60mm taller). Same options apply: recess the turntables into the surface, or raise the central row on a platform.

## Equipment Positioning

### Recommended: Turntables outside, laptops inside, mixer central

```
┌─────────┐ ┌────────┐ ┌─────────┐ ┌────────┐ ┌─────────┐
│Technics │ │Laptop A│ │ Mixer + │ │Laptop B│ │Technics │
│(outside)│ │(inside)│ │  Kaoss  │ │(inside)│ │(outside)│
└─────────┘ └────────┘ └─────────┘ └────────┘ └─────────┘
```

Carries over from the CDJ layout:

- **Isolation:** turntables furthest from mixer vibration and central workspace — needle-skip risk minimized
- **Short USB runs:** laptops next to the Xone:96 keep the two dual-USB cables tidy
- **Ergonomics:** hands naturally rest on whichever source is closest to the mixer; the Kaoss Pad sits within arm's reach of both

New consideration with the Reason rig:

- **Screen angle matters.** Unlike CDJs, laptop screens are part of the performance surface. Plan for ~15° tilt toward the DJ (laptop stands or a sloped shelf), with enough height that the screen doesn't occlude the mixer.

### Kaoss Pad placement options

1. **Flat, next to the mixer** — best two-hand performance, adds ~170mm to total width
2. **Front shelf / sloped lip in front of the mixer** — tighter footprint, but constrains finger room
3. **Right of laptop B on the lip** — asymmetric, keeps mixer centered

Option 1 is the default for the initial build; revisit after playing the rig.

### Spacing

Leave **40–50mm between the turntable and whatever's next to it** — enough air gap for vibration isolation, close enough to reach both without shifting stance.

## Design Considerations

### Isolation

Turntable isolation is still critical. Bass vibration from the speakers feeding back through the deck causes needle skip and rumble — unchanged by the pivot.

- Rubber isolation feet under each turntable
- Ideally: separate isolated shelf or slab (heavy stone/MDF on sorbothane pads)
- Decouple turntable section from the main desk structure if possible

### Ergonomics

| Position | Desk Height |
|----------|-------------|
| Standing | 90–100cm |
| Seated (stool) | 70–75cm |

### Cable Routing

New cable counts with the Reason rig:

- Each turntable: 1x RCA pair + 1x ground + 1x power
- Each laptop: 1x USB-C → Xone:96 USB + 1x power
- Mixer: 4x RCA in (turntables) + 2x USB (laptops) + 1x send to Kaoss Pad + 1x return from Kaoss Pad + 1x XLR master out + 1x power
- Kaoss Pad: 1x RCA pair in, 1x RCA pair out, 1x power

Roughly **~14 cables** at full deployment — a couple more than before thanks to Kaoss Pad send/return, but 2x USB replaces 2x RCA that CDJs required. Route channels cleanly; consider a cable dropbox at the rear.

### Ventilation

No CDJs means less heat — just mixer + two laptops. Laptops need airflow under them (cooling stands or ventilated riser). Leave at least 50mm clearance behind units.

### Materials

- **Recommended:** MDF or plywood, 18mm+ thickness
- **Avoid:** Glass (resonance), thin metal (vibration), particle board (weak)
- **Finish:** Consider acoustic dampening material on inner surfaces

### Total Weight

Reason-rig version: 2x 9.6kg (Technics) + 7kg (mixer) + 2x 1.5kg (laptops) + ~1kg (Kaoss Pad) = **~30kg**, down from ~37kg with CDJs. Still build sturdy — the turntables dominate anyway.

---

## Design Evolution

### Apr 12 (Ola's Proposal) — still in scope

- **Motorized sit/stand base** on Ola's rack carts — Wallapop frame to be sourced
- **Modularity** — all gear lifts off the surface, no flush-mounting, quick-release cable management
- **Dual-use workspace** — acrylic/plastic cover panel when in "Ola's workspace" mode
- **Power filtering** — Ola contributing a rack power-supply filter, lives in the cart base

### Apr 18 — Reason pivot, desk implications

- CDJ footprint removed → desk shortens by ~350mm, or stays the same width and gains breathing room for Kaoss Pad and screen real estate
- Two laptop positions need tilt/stand provisions (sloped shelf or laptop risers built in)
- 2x USB-C runs added between laptops and mixer — keep short
- Kaoss Pad needs either a flat slot next to the mixer or a front-shelf cut-out
- "Vinyl-as-MIDI-controller" research from the Apr 12 session is **deprioritized** — the point of the pivot is that Reason + Kaoss Pad already give you the creative layer without needing to virtualize CDJ control through turntables

### Next Steps

- [ ] Ola reviews new layout against Apr 18 drawings — does the shorter desk or the "same width, more breathing room" version win?
- [ ] Decide Kaoss Pad placement: flat next to mixer vs. front-shelf cut-out
- [ ] Spec laptop stands / tilt (maker-built vs off-the-shelf)
- [ ] Re-source secondhand motorized desk frame (Wallapop) at the new width
- [ ] Update quick-release cable plan for 2x USB-C + Kaoss Pad send/return
- [ ] ~~Research turntable-as-MIDI-controller~~ — deprioritized by the Reason pivot
