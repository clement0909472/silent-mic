# Launch verification, 9 September 2026

## What this review establishes

The public baseline was `43f98ee` on `main`. The working directory contained later CAD changes from the compact prototype/slicing session of 17 August. The latest files explicitly handed to the slicer were the compact upper/lower STL pair, not the longer standard variant. The review preserves that geometry rather than silently redesigning the physical prototype.

Key compact parameters: handle body height 91 mm (excluding the base), inclination about 24.8 degrees, divider top Z = -4 mm, inlet bottom Z = -4 mm, 11 mm clearance above the divider, flat base with two 12 mm exhausts. The standard alternative has a 19 mm divider clearance. Both share the latest inlet duct/base construction.

An initial isolated rebuild detected stale **standard lower STEP** geometry in the working exports. Both variants were regenerated from their current sources. The compact upper/lower STEP geometry was already identical to its local source model. The inherited FreeCAD snapshots are not rebuilt by the generators and are now explicitly labeled legacy and moved to `cad/archive/v2-screwed`, without deleting them.

## Runnable checks

Use Python 3.12 and `cadquery==2.8.0`, then run:

```sh
python cad/check_exports.py
```

The checker rebuilds both variants in a temporary directory, runs the generators' assertions, compares STEP solid counts, summed volumes and bounding boxes, compares printed upper/lower shapes by symmetric-difference volume, and compares STL bytes. STEP headers/identifiers can change without a shape change. This check is pinned to the documented environment; a different CAD kernel/exporter can require geometric review even if only tessellation changes.

Result on 9 September 2026: **PASS for both variants**, covering 38 STEP and 6 STL files. Python syntax and local Markdown links also passed. These are local checks, not a hosted CI run or a physical test.

The generator checks include upper/lower validity and non-intersection, microphone/receiver layout clearances, handle-foam/plastic clearance, baffle attachment, connected air volume after subtracting the printed walls and handle foam, and a non-colliding print layout within 180 x 180 x 180 mm. A connected void does **not** prove adequate airflow or acoustic attenuation.

Expected plate bounds:

| Variant | Arranged plate dimensions, mm |
|---|---:|
| Standard | 114.7 x 169.0 x 116.0 |
| Compact | 159.9 x 159.8 x 95.0 |

## Documentation and shopping corrections

- The compact variant is the first build path. Print the upper/lower STL pair OR their combined plate. Reference solids and the integrated baffle are not extra printed parts.
- Fastener direction corrected: screws enter from below the lower flange; nuts are inserted in the upper cup from the chamber side.
- The former [Amazon screw kit](https://www.amazon.com/dp/B0FGV5FCBN) lists socket-head screws. It was removed from the BOM because the CAD expects countersunk heads.
- [DJI EU mobile bundle](https://store.dji.com/lv/product/dji-mic-mini-2-1tx-1-mobile-rx-charging-case): listed at EUR 59 when reviewed. The former French direct link could not be retrieved. Buy the matching mobile receiver, not the larger camera receiver.
- [Brainwavz oval collection](https://www.brainwavzaudio.com/collections/oval-memory-foam-earpds): USD 16.88 sale / USD 22.50 regular for the basic oval pads; nominal outer 110 x 90 mm, inner 70 x 50 mm. Thickness varies with style. Prefer a non-perforated PU cover for this experiment; this is a design choice, not a manufacturer-certified acoustic seal.
- [8 x 1 mm magnet](https://www.amazon.com/dp/B0BJQ918KX): listing identifies the specified size and self-adhesive dots. Live regional price/delivery was not established.
- Foam and steel-disc links remain original sourcing references, not newly certified materials. Steel-disc page retrieval failed; foam material suitability and all accessory prices need buyer verification. Do not use shedding or unsuitable foam near the mouth.
- The BOM now separates observed listed prices from accessory allowances and gives a rounded EU planning budget, not a false mixed-currency total.
- No guaranteed support-free recipe, filament mass, USB compatibility across all hosts, silence or cloud privacy is claimed.

## Remaining physical validation

The author reports a first prototype built within 24 hours, including Amazon delivery, AI-assisted design and printing. No acoustic measurements, independent replication, exact as-printed revision manifest or reusable slicer profile is provided here. This review cannot establish those remotely.

The nominal 1 mm shell-joint gasket overlaps the rigid halves in the reference assembly: there is no designed compression gap. Dry-fit a thinner compressible seal and verify screw engagement; do not assume a rigid 1 mm gasket will fit. This is distinct from the priority improvement at the upper cushion-to-shell interface.

The base exhausts open downwards and can be blocked on a desk. Keep them clear during use. The geometric air reference overlaps some internal structure by design; it is an inspection aid, not CFD or an acoustic simulation. A physical test must examine intelligible speech leakage (including nasal sounds), transcription, breathing comfort, condensation and cleaning.

The README roadmap covers cushion-interface sealing, miniaturization, repeatable assembly and measurements. The project is shareable as an **experimental open-source prototype**, not a certified privacy product.
