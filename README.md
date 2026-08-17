# Silent Mic

[![Prototype](https://img.shields.io/badge/status-untested%20prototype-f59e0b)](#prototype-status)
[![CERN-OHL-S-2.0](https://img.shields.io/badge/license-CERN--OHL--S--2.0-2563eb)](LICENSE)

**Speak to your AI without broadcasting your prompt.**

![Clément using the Silent Mic in an open office](images/silent-mic-in-use.png)

*AI-generated concept image. It is not evidence of a tested physical prototype.*

## The pain

Voice is often the fastest way to work with an AI agent, but speaking prompts aloud in an open office is distracting and can expose private context. Noise-cancelling microphones improve what the computer hears. They do not stop nearby people from hearing the speaker.

Silent Mic explores a physical alternative: a handheld, mouth-only enclosure for short AI dictation sessions. The goal is to preserve clear transcription while reducing intelligible speech leakage around the user.

## The solution

The device holds a wireless microphone close to the mouth inside a sealed 3D-printed cup. A memory-foam cushion seals around the mouth while leaving the nose free. Open-cell foam absorbs internal reflections, and the long baffled handle provides an indirect exhaust path for spoken air.

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

## Shopping list

Prices are approximate retail prices observed in August 2026. Availability and regional pricing change.

| Part | Purpose | Typical price |
|---|---|---:|
| [DJI Mic Mini 2, 1 transmitter + mobile USB-C receiver](https://store.dji.com/fr/product/dji-mic-mini-2-1tx-1-mobile-rx-charging-case) | Captures speech and connects to the computer | about $69 / EUR 59 |
| [Brainwavz oval memory-foam earpads](https://www.brainwavzaudio.com/collections/accessories/brainwavz-hm5) | Mouth seal and comfort, 110 x 90 mm outside, 70 x 50 mm opening | $23-30 per pair |
| [12.7 mm open-cell foam](https://www.amazon.com/dp/B0FFBG6ZZZ) | Internal absorption | $10-15 |
| 4 x M3 x 16 mm screws, 4 nuts, 8 washers | Joins the upper cup and handle | $3 loose or [$10 kit](https://www.amazon.com/dp/B0FGV5FCBN) |
| [30 mm adhesive steel discs](https://www.amazon.com/dp/B0DYNS2CXR) | Passive magnetic mounting surfaces | about $8 |
| [8 x 1 mm adhesive neodymium magnet](https://www.amazon.com/dp/B0BJQ918KX) | Retains the USB-C receiver for storage | about $8 |
| 1 mm EVA, TPU, or rubber sheet | Joint gasket | about $5 |
| 150-250 g PLA or PETG | Printed upper and lower parts | about $5 |

**Expected basket price: about $130-150 from scratch, or $60-80 if you already own the DJI microphone.** Printer access is not included, and the amount of material actually consumed is cheaper than buying every pack.

## Files

- [`cad/whisper_mask_v2_screwed.py`](cad/whisper_mask_v2_screwed.py): final two-part parametric model and geometry checks.
- [`cad/whisper_mask_v0.py`](cad/whisper_mask_v0.py): reusable upper cup, component layout, and cushion interface.
- [`cad/out/v2-screwed/whisper-mask-v2-screwed-print-plate.stl`](cad/out/v2-screwed/whisper-mask-v2-screwed-print-plate.stl): both printed parts arranged for a 180 x 180 mm bed.
- [`cad/out/v2-screwed/whisper-mask-v2-screwed-upper.stl`](cad/out/v2-screwed/whisper-mask-v2-screwed-upper.stl): mouth cup.
- [`cad/out/v2-screwed/whisper-mask-v2-screwed-lower.stl`](cad/out/v2-screwed/whisper-mask-v2-screwed-lower.stl): baffled handle.
- [`cad/out/v2-screwed/whisper-mask-v2-screwed-technical.step`](cad/out/v2-screwed/whisper-mask-v2-screwed-technical.step): full technical assembly.
- [`cad/out/v2-screwed/silent-mic-v2-simple.FCStd`](cad/out/v2-screwed/silent-mic-v2-simple.FCStd): simple FreeCAD view with the two printed parts.
- [`cad/out/v2-screwed/silent-mic-v2-technical-flat.FCStd`](cad/out/v2-screwed/silent-mic-v2-technical-flat.FCStd): flat FreeCAD document with the internal references.

The remaining STEP files in [`cad/out/v2-screwed`](cad/out/v2-screwed) expose the gasket, foam, baffle, air path, fasteners, cushion, microphone, and receiver as separate inspection objects.

## Step-by-step setup

### 1. Check the fit before printing

The CAD assumes a Brainwavz oval cushion around 110 x 90 x 30 mm with a 70 x 50 mm opening. Real cushions vary by a few millimetres. Hold it horizontally around the mouth and confirm that the nose remains clear.

### 2. Slice and print

Import the print-plate STL into OrcaSlicer or another slicer.

Recommended starting settings:

- 0.20 mm layer height
- 4 wall loops
- 15% infill
- no supports
- PLA for a fast prototype, PETG for better heat and impact resistance

The arranged plate is approximately 115 x 169 x 116 mm and fits a Bambu A1 mini build volume.

### 3. Prepare the soft parts

1. Cut the 1 mm gasket using `whisper-mask-v2-screwed-gasket.step` as the template.
2. Cut the main cup foam around the microphone and receiver volumes. Never cover the microphone grille.
3. Cut two removable strips for the handle using `whisper-mask-v2-screwed-handle-foam.step` as a guide.
4. Keep both exhaust ports completely open for the first airflow test.

### 4. Install the electronics

1. Attach a passive steel disc to the vertical support inside the upper cup.
2. Clip the DJI transmitter magnetically to the disc, with its grille facing the mouth.
3. Use the small magnet and second steel disc only to store the USB-C receiver inside the device when it is not plugged into the computer.
4. Fit the Brainwavz cushion over the printed front lip.

### 5. Close the enclosure

1. Place the 1 mm gasket between the upper cup and lower handle.
2. Insert four M3 x 16 mm screws with washers.
3. Seat the four M3 nuts in the captive pockets.
4. Tighten evenly until the gasket is compressed. Do not crush the printed flange.

### 6. Connect and test

1. Plug the DJI receiver into USB-C.
2. Select it as the microphone input in the operating system or AI app.
3. Keep headphones as the output device.
4. Record the same five-minute prompt with and without handle foam.
5. Check transcription accuracy and ask a listener to score intelligibility at 0.5 m, 1 m, and 2 m.

## Rebuild the CAD

With Python 3.11+:

```bash
python -m pip install -r requirements.txt
python cad/whisper_mask_v2_screwed.py
```

The model contains assertions for solid validity, component collisions, a continuous air path, baffle clearance, and 180 mm print-bed fit.

## Prototype status

The current files have passed CAD solid-validity and layout checks. They have **not** yet proven:

- acoustic attenuation in dB or speech-intelligibility reduction;
- a reliable seal on different faces;
- comfort, condensation, cleaning, or five-minute breathing performance;
- final transcription quality;
- a validated slicer recipe or completed physical print.

Do not treat Silent Mic as hearing protection, respiratory protection, or a certified privacy device. Do not block the exhaust ports.

## License

Hardware source, CAD, exports, and documentation are released under the [CERN Open Hardware Licence Version 2 - Strongly Reciprocal](LICENSE). `SPDX-License-Identifier: CERN-OHL-S-2.0`.

DJI and Brainwavz are trademarks of their respective owners. This independent project is not affiliated with or endorsed by either company.

