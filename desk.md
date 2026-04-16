---
layout: default
title: Desk Design
---

# Desk Design

## Equipment Dimensions

| Unit | W x D x H (mm) | Weight |
|------|----------------|--------|
| Technics SL-1200MK7 | 453 x 353 x 169 | 9.6 kg |
| Pioneer CDJ-3000 | 329 x 453 x 118 | 5.5 kg |
| Allen & Heath Xone:96 | 336 x 410 x 109 | 7 kg |

## Layout

```
┌───────────┐ ┌─────────┐ ┌────────┐ ┌─────────┐ ┌───────────┐
│ Technics L│ │ CDJ-L   │ │ Mixer  │ │ CDJ-R   │ │ Technics R│
│  453mm    │ │  329mm  │ │ 336mm  │ │  329mm  │ │  453mm    │
│  x 353mm  │ │  x 453mm│ │ x 410mm│ │  x 453mm│ │  x 353mm  │
│  h: 169mm │ │  h:118mm│ │ h:109mm│ │  h:118mm│ │  h: 169mm │
└───────────┘ └─────────┘ └────────┘ └─────────┘ └───────────┘
├─────────────────── ~2,020mm (with 30mm gaps) ──────────────────┤
```

## Key Measurements

| Measurement | Value |
|-------------|-------|
| Total minimum width | ~1,900mm |
| Recommended width (30mm gaps) | **~2,020mm (~2m)** |
| Depth (equipment only) | 453mm |
| Depth with cable space | ~500–550mm |
| Height difference | Turntables 169mm vs CDJs/mixer 109–118mm |

> **Note:** Turntables are ~60mm taller than CDJs and mixer. Consider recessing the turntables into the desk surface, or raising CDJs/mixer on a platform for level playing surfaces.

## Equipment Positioning — CDJs vs Turntables

### Recommended: Turntables Outside, CDJs Inside (Current Layout)

```
┌───────────┐ ┌─────────┐ ┌────────┐ ┌─────────┐ ┌───────────┐
│ Technics  │ │  CDJ    │ │ Mixer  │ │  CDJ    │ │ Technics  │
│ (outside) │ │ (inside)│ │        │ │ (inside)│ │ (outside) │
└───────────┘ └─────────┘ └────────┘ └─────────┘ └───────────┘
```

This is the **Paradise Garage / classic club booth standard** and the best fit for this build:

- **Isolation**: turntables are furthest from mixer vibration and desk center, reducing needle skip risk
- **Short USB runs**: CDJs next to the Xone:96 keeps digital connections (HID) clean — critical for the dual USB sound card
- **Ergonomics**: hands naturally rest on the active source closest to the crossfader and EQ
- **DVS-friendly**: when running DVS through the Technics, the vinyl signal path to the phono inputs is already short from the outside position
- **Height differential**: turntables on the outer edges makes it easier to build isolated risers without cramping the central workspace

### Alternative: CDJs Outside, Turntables Inside

Some DJs prefer this when vinyl is the primary medium:

- Keeps platters closest to the mixer for faster cueing and scratching
- More common in hip-hop / scratch setups where CDJs are rarely touched mid-set
- **Downside**: worse isolation — turntables closer to sub frequencies transmitted through the desk
- **Not recommended for this build** given the Xone:96 dual USB architecture and mixed digital/analog workflow

### Spacing

Leave **40–50mm between the CDJ and turntable** on each side — enough air gap for vibration isolation, close enough to reach both without shifting stance. The 30mm gaps in the current layout are tight; consider widening to 40mm on the CDJ-turntable boundaries specifically.

## Design Considerations

### Isolation

Turntable isolation is critical. Bass vibration from speakers feeding back through the deck causes needle skip and rumble.

- Rubber isolation feet under each turntable
- Ideally: separate isolated shelf or slab (heavy stone/MDF on sorbothane pads)
- Decouple turntable section from the main desk structure if possible

### Ergonomics

| Position | Desk Height |
|----------|-------------|
| Standing | 90–100cm |
| Seated (stool) | 70–75cm |

### Cable Routing

- Plan channels underneath or behind for RCA + power cables
- Each turntable: 1x RCA pair + 1x power
- Each CDJ: 1x RCA pair + 1x power + optional 1x ethernet (Link)
- Mixer: 4x RCA in + 1x XLR master out + 1x power + optional USB
- Total: ~10 cables minimum — route cleanly

### Ventilation

CDJs and mixer generate heat. Don't fully enclose the back panel. Leave at least 50mm clearance behind units for airflow.

### Materials

- **Recommended:** MDF or plywood, 18mm+ thickness
- **Avoid:** Glass (resonance), thin metal (vibration), particle board (weak)
- **Finish:** Consider acoustic dampening material on inner surfaces

### Total Weight

The desk needs to support: 2x 9.6kg + 2x 5.5kg + 7kg = **~37kg** of equipment, plus the desk's own weight. Build sturdy.

---

## Design Evolution (Apr 12 — Ola's Proposal)

Based on Ola and Andreas's discussion, the desk concept has evolved significantly from a static surface.

### Height-Adjustable Base

Ola proposed mounting the desk on a **motorized sit/stand base**:

- Use Ola's existing **rack carts** as a rolling foundation
- Source a secondhand **electric height-adjustable desk frame** (Wallapop) and mount it onto the rack carts
- Connect the frame to the tabletop — full range from seated work height (~70cm) to standing DJ height (~100cm)
- Rationale: the space is shared (DJ studio + Ola's workspace). If the height is uncomfortable for either user, they'll use the space less.

### Modularity — Hard Requirement

Andreas pushed back on fully recessed/inserted equipment. **All gear must be easy to disconnect and transport:**

- Forest raves in Galicia (Pedro / Espacio Perez) have existing stages — only need to bring CDJs + mixer
- B2B setups at other venues
- Equipment may be rented out (David's business idea)

Ola agreed: "there are a bunch of ways to make that process smooth and easy without really adding any costs — it's about planning."

**Implication:** equipment sits on top of the surface (not flush-mounted), with quick-release cable management. The desk is optimized for the space, but each unit can be lifted out independently.

### Dual-Use Workspace

The desk must also function as Ola's work surface:

- Acrylic or plastic cover panel over the center section when working
- Easy to remove when switching to DJ mode

### Power Filtering

Ola is contributing a **power supply filter** from his existing rack gear:

- Filters mains power before it reaches the audio chain
- A/B tested: audible improvement in clarity and speaker top-end
- Protects circuitry across the full system
- Lives in the rack cart base — clean integration

### Vinyl-as-MIDI-Controller (Research Needed)

Ola raised an interesting idea: can turntables act as **digital controllers for CDJs**, like a MIDI controller for a synth? This could allow switching between real vinyl and digital control without changing the physical setup.

Existing tech in this space:
- **DVS (Digital Vinyl System)** — Serato / Traktor timecode vinyl controls software, but requires a laptop
- **Direct turntable → CDJ MIDI** — largely unexplored; could be a niche opportunity

### Next Steps

- [ ] **Ola brings desk drawings — Friday Apr 18**
- [ ] Andreas documents equipment requirements as bullet points before Friday
- [ ] Source secondhand motorized desk frame on Wallapop
- [ ] Plan quick-release cable management for modular gear
- [ ] Research DVS / turntable-as-controller options
