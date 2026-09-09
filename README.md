# Silent Mic

[![Prototype](https://img.shields.io/badge/status-experimental%20prototype-f59e0b)](#prototype-status)
[![CERN-OHL-S-2.0](https://img.shields.io/badge/license-CERN--OHL--S--2.0-2563eb)](LICENSE)

**Speak to your AI without broadcasting your prompt.**

![A fictional startup professional holding a black Silent Mic against the mouth at a laptop in an open office](images/silent-mic-in-use-v2.png)

*AI-generated illustration, not a photograph of the built prototype or an exact CAD rendering.*

**Start here:** build the [compact version](cad/out/v2-compact). Download the [print plate](cad/out/v2-compact/whisper-mask-v2-compact-print-plate.stl), buy the [components](#shopping-list), then follow the [assembly guide](#step-by-step-setup). No coding is needed unless you want to change the design.

I built the first prototype in under 24 hours, including AI-assisted design with Astra, an Amazon component order and 3D printing. That is my own build experience, not a promised delivery or printing time for everyone. This repository shares the design so others can build, test and improve it.

## The pain

Voice is often the fastest way to work with an AI agent, but speaking prompts aloud in an open office is distracting and can expose private context. Noise-cancelling microphones improve what the computer hears. They do not stop nearby people from hearing the speaker.

Silent Mic explores a physical alternative: a handheld, mouth-only enclosure for short AI dictation sessions. The goal is to preserve clear transcription while reducing intelligible speech leakage around the user.

## The solution

The device holds a wireless microphone close to the mouth inside a 3D-printed cup. A headphone cushion is intended to seal around the mouth while leaving the nose free. Open-cell foam and a baffled handle are intended to reduce sound escaping through the enclosure and its exhaust. The design follows the familiar speech-mask / Stenomask form factor; its acoustic performance is still being evaluated.

```text
mouth -> close microphone -> USB-C receiver -> AI app
          |
          +-> foam + baffle + long air path -> exhaust
```

Typical use:

1. Plug the DJI mobile receiver into the computer over USB-C.
2. Keep headphones or AirPods as the audio output.
3. Hold Silent Mic against the mouth and speak softly to ChatGPT, Claude, or another voice-enabled agent.
4. Put it down when the prompt is finished.

This addresses **nearby acoustic leakage**, not the privacy policy of your AI service. The microphone transmits wirelessly to its receiver; your chosen app may send audio or transcripts to the cloud. Silent Mic adds no firmware, account, app, encryption guarantee or offline AI processing.

## Shopping list

Budget estimates, not a checkout quote. Links reviewed on 9 September 2026; DJI's EU listing shows EUR 59 and Brainwavz's oval collection shows USD 16.88 on sale / USD 22.50 regular. Other accessory amounts below are planning allowances, not verified live prices. Shipping, taxes and availability vary. Do not add EUR and USD as if they were the same currency.

| Part | Purpose | Typical price |
|---|---|---:|
| [DJI Mic Mini 2, 1 TX + 1 Mobile RX + charging case](https://store.dji.com/lv/product/dji-mic-mini-2-1tx-1-mobile-rx-charging-case) | One transmitter inside the cup; USB-C mobile receiver on the computer. Choose this bundle, not the larger camera receiver | EUR 59 (EU listing) |
| [Brainwavz oval memory-foam earpads](https://www.brainwavzaudio.com/collections/oval-memory-foam-earpds) | One pad required, generally sold as a pair. Non-perforated PU leather, not XL round / angled / velour. Nominal outside 110 x 90 mm, opening 70 x 50 mm | USD 16.88 sale / 22.50 regular |
| [12.7 mm open-cell foam](https://www.amazon.com/dp/B0FFBG6ZZZ) | Internal absorption | $10-15 |
| 4 x M3 x 6 mm **countersunk** screws, 4 standard M3 hex nuts | Joint between cup and handle. Head must fit the 6.2 mm countersink, nuts the 6.7 mm across-corners pocket; dry-fit before buying a large pack | USD 3 loose / 10 small pack allowance |
| [30 mm adhesive steel discs](https://www.amazon.com/dp/B0DYNS2CXR) | Passive magnetic mounting surfaces | about $8 |
| [8 x 1 mm adhesive neodymium magnet](https://www.amazon.com/dp/B0BJQ918KX) | Optional: retains the USB-C receiver for storage only | about USD 8 |
| Up to 1 mm compressible EVA or rubber sheet | Experimental joint gasket between the two printed halves, **not** the cushion seal | about USD 5 |
| PLA or PETG | Two rigid printed parts; use the slicer's mass estimate, not a fixed weight claim | about USD 5 of filament |

**Rough planning budget: EUR 120-150 from scratch, or EUR 50-80 if you already own the matching microphone and receiver.** This is a rounded EU allowance, not a currency conversion or a guaranteed basket total. Printer access and shipping are extra; small packs cost more than the material actually used. Optional receiver storage can be omitted.

You also need a slicer, printer access, calipers/ruler, scissors or a craft knife and a driver matching the screws. Verify the receiver is recognized by your computer and records in your chosen AI app **before** printing. Different DJI models and camera/mobile receivers are not interchangeable CAD shapes: the design envelopes are TX 28.58 x 28.04 x 13.52 mm and mobile RX 39.26 x 27.26 x 8.97 mm. Measure your actual units, including clips/covers.

The former Amazon screw-kit link was removed because it listed socket-head screws, not the required countersunk heads. Accessory links are examples, not compatibility certification; check dimensions, material and pack contents before ordering.

## Files

- [`cad/whisper_mask_v2_compact.py`](cad/whisper_mask_v2_compact.py): **current starting point**, matching the compact files last handed to the slicer. Shorter angled handle, extended inlet duct and flat perforated base.
- [`cad/whisper_mask_v2_screwed.py`](cad/whisper_mask_v2_screwed.py): shared two-part geometry and checks, plus a longer-handle alternative.
- [`cad/whisper_mask_v0.py`](cad/whisper_mask_v0.py): reusable upper cup, component layout, and cushion interface.
- [`cad/out/v2-screwed/whisper-mask-v2-screwed-print-plate.stl`](cad/out/v2-screwed/whisper-mask-v2-screwed-print-plate.stl): both printed parts arranged for a 180 x 180 mm bed.
- [`cad/out/v2-compact/whisper-mask-v2-compact-print-plate.stl`](cad/out/v2-compact/whisper-mask-v2-compact-print-plate.stl): compact variant arranged for the same bed.
- [`cad/out/v2-screwed/whisper-mask-v2-screwed-upper.stl`](cad/out/v2-screwed/whisper-mask-v2-screwed-upper.stl): mouth cup.
- [`cad/out/v2-screwed/whisper-mask-v2-screwed-lower.stl`](cad/out/v2-screwed/whisper-mask-v2-screwed-lower.stl): baffled handle.
- [`cad/out/v2-screwed/whisper-mask-v2-screwed-technical.step`](cad/out/v2-screwed/whisper-mask-v2-screwed-technical.step): full technical assembly.
- [`cad/out/v2-compact/whisper-mask-v2-compact-upper.stl`](cad/out/v2-compact/whisper-mask-v2-compact-upper.stl) and [lower STL](cad/out/v2-compact/whisper-mask-v2-compact-lower.stl): compact parts separately, if you prefer to arrange them yourself.
- [`cad/out/v2-compact/whisper-mask-v2-compact-technical.step`](cad/out/v2-compact/whisper-mask-v2-compact-technical.step): current compact inspection assembly, openable in FreeCAD.
- [`cad/check_exports.py`](cad/check_exports.py): isolated rebuild and comparison against the published print files.

Both export folders contain foam/gasket cutting references and electronics/fastener inspection objects. **Print only the upper and lower STL files, or their combined plate, not both.** The divider is already part of the lower piece. The colored air path is a reference volume, not a part to print or an acoustic simulation. The technical assembly also includes overlapping inspection references.

The older `silent-mic-v2-*.FCStd` files are **legacy inspection snapshots**, retained in [`cad/archive/v2-screwed`](cad/archive/v2-screwed) for history; they predate the latest inlet/base changes. Do not print from them. Current Python + STEP + STL are authoritative. No printer-specific G-code or proven slicer profile is supplied. See the [verification record](docs/verification.md).

## Step-by-step setup

### 1. Check the fit before printing

The CAD assumes a Brainwavz oval cushion around 110 x 90 x 30 mm with a 70 x 50 mm opening. Thickness varies with pad style and real cushions vary by a few millimetres. Hold it horizontally around the mouth and confirm that the nose remains clear. The cushion-to-printed-lip fit is experimental: check its underside mounting skirt, not just the opening dimensions. Do not assume that stretching it over the lip makes an acoustic seal.

### 2. Slice and print

Download this repository (GitHub: **Code > Download ZIP**, then unzip). Import the **compact** print-plate STL into OrcaSlicer or another slicer in millimetres, at 100% scale. Keep files from the same variant and revision together.

Recommended starting settings:

- 0.20 mm layer height
- 4 wall loops
- 15% infill
- inspect overhangs, the cup roof and internal duct in the layer preview; support-free printing is **not a validated recipe**
- PLA for a fast prototype, PETG for better heat and impact resistance

The standard arranged plate is approximately 115 x 169 x 116 mm. The compact plate is approximately 160 x 160 x 95 mm. Both fit a Bambu A1 mini build volume.

These are arranged print-plate dimensions, not assembled device dimensions. Both bases must touch the build plate after import. Check the first layers, all exhaust holes, bridge spans, estimated time and filament mass before sending. Match the physical loaded filament to the sliced material and nozzle; do not override a PETG/TPU mismatch warning. If internal supports cannot be removed, revise orientation/settings rather than leaving them in the air path.

### 3. Prepare the soft parts

1. Use the gasket STEP from your chosen variant as a cutting reference. Its nominal thickness is 1 mm, but the rigid CAD halves have **no dedicated gasket gap**. Dry-fit a thin compressible seal; do not force a solid 1 mm TPU sheet between them. Gasket compression and screw engagement still need physical validation.
2. Cut the main cup foam around the microphone and receiver volumes. Never cover the microphone grille.
3. Cut two removable strips for the handle using the left and right handle-foam STEP files as guides.
4. Keep both exhaust ports completely open for the first airflow test.

### 4. Install the electronics

1. Attach a passive steel disc to the vertical support inside the upper cup.
2. Clip the DJI transmitter magnetically to the disc, with its grille facing the mouth.
3. Use the small magnet and second steel disc only to store the USB-C receiver inside the device when it is not plugged into the computer.
4. Fit the Brainwavz cushion over the printed front lip. Inspect the full cushion-to-shell perimeter, especially the upper edge under the nose. A removable external seam seal can help compare leakage in a test, but is not a validated permanent fix. Keep adhesive outside the mouth opening and away from electronics and vents.

### 5. Close the enclosure

1. Insert the four M3 nuts into the **upper cup**, from the chamber side, before fitting foam over access points.
2. Dry-fit the upper cup onto the lower handle, aligning the four holes and inlet duct. Fit the experimental thin joint seal only if it compresses evenly without forcing the halves apart.
3. Insert four M3 x 6 mm countersunk screws **upwards from underneath the lower flange**. The screw heads sit below; the captive nuts sit above. Check that every screw engages properly before tightening.
4. Tighten evenly by hand. Stop if a nut spins, a screw bottoms out or the flange bends. Do not crush the flange or use extra torque to compensate for an oversized gasket.

### 6. Connect and test

1. Plug the DJI receiver into USB-C.
2. Select it as the microphone input in the operating system or AI app.
3. Keep headphones as the output device.
4. Start with a short recording, holding the mouth cup comfortably against the face, nose clear and both base exhausts uncovered by your hand. **Do not speak into it while its flat base is on a desk:** the desk can block the outlets.
5. Use the same non-sensitive script and speaking level for three recordings: without the device, with it, then with handle foam. Ask a listener at 0.5 m, 1 m and 2 m what words they can actually understand. Compare transcription errors as well as perceived loudness.
6. Only if comfortable, extend to a few minutes. Stop immediately if breathing feels restricted or discomfort occurs. Remove electronics before cleaning; let cushion and foam dry fully. Do not share a damp cushion.

Troubleshooting: no input signal means checking receiver pairing, USB connection, app permissions and input selection first. Poor transcription means checking grille clearance and input gain. Audible leakage means checking cushion/skin contact, cushion/printed-shell contact and the shell joint separately, without blocking the vents.

## Rebuild the CAD

The rebuild was checked with Python 3.12 and CadQuery 2.8.0. From the repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python cad/whisper_mask_v2_screwed.py
python cad/whisper_mask_v2_compact.py
python cad/check_exports.py
```

On Windows use `.venv\Scripts\activate` instead. Run the two generators as separate processes; the compact script configures the shared standard model. Rebuilding overwrites that variant's STEP/STL exports; commit or back up edits first. The checker instead rebuilds in a temporary directory without touching published files.

Assertions check solids, specified component clearances, non-colliding printed halves, connected reference/actual air voids, baffle clearance and 180 mm bed fit. These are geometric checks, not airflow, acoustic or manufacturing validation. Large STEP diffs are often generated geometry records, not hand-written code.

## Improvements and contributions

The next priorities are concrete, and are **not yet solved**:

1. **Seal the cushion-to-printed-shell interface**, especially its upper edge under the nose. Explore a removable clamping ring, a continuous gasket or a better-fitting lip. Keep the nose free and do not confuse this interface with the lower shell joint. Compare word intelligibility before/after at the same distances and speaking level.
2. **Miniaturize the device.** Reduce cup volume and handle bulk while preserving microphone clearance, cleanability and an unobstructed exhaust. The compact version is a starting point, not the final size. Report size, mass, print time and transcription/leakage trade-offs.
3. **Make assembly repeatable.** Validate cushion retention, gasket compression, screw length/engagement and support removal. Share a printer/material-specific slicer profile and photos of the actual build.
4. **Measure performance.** Publish repeatable leakage/transcription tests, including nasal sounds, different faces and a short comfort/condensation check. No guaranteed silence or confidentiality until demonstrated, and never a blanket guarantee.

Built one or found an improvement? [Open an issue](https://github.com/clement0909472/silent-mic/issues) or a pull request with the variant/revision, printer and material, exact changed dimensions, photos and a before/after test. For CAD changes include the Python sources and regenerated STEP/STL files, and run `python cad/check_exports.py`. Use non-sensitive speech samples and get consent before sharing recordings.

## Prototype status

The author reports building a first physical prototype within 24 hours. The current compact files match the latest local version handed to the slicer; that does not establish a measured performance result or prove which revision every physical print used. The files have passed the documented CAD checks. There is **no published validation yet** for:

- acoustic attenuation in dB or speech-intelligibility reduction;
- a reliable seal on different faces;
- comfort, condensation, cleaning, or five-minute breathing performance;
- final transcription quality;
- a reproducible, printer-specific slicer recipe or independent build replication.

Do not treat Silent Mic as hearing protection, respiratory protection, or a certified privacy device. Do not block the exhaust ports.

## License

Hardware source, CAD, exports, and documentation are released under the [CERN Open Hardware Licence Version 2 - Strongly Reciprocal](LICENSE). `SPDX-License-Identifier: CERN-OHL-S-2.0`.

DJI and Brainwavz are trademarks of their respective owners. This independent project is not affiliated with or endorsed by either company.

The open-source portion is the enclosure design and repository content, not DJI's proprietary electronics/firmware or third-party accessories. AI illustrations are labeled as such and are not engineering specifications.
