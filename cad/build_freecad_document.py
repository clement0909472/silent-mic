"""Rebuild the technical FreeCAD document from the current STEP exports."""

from pathlib import Path
import re
import sys

import FreeCAD as App
import Part


SOURCE_DIR = Path(sys.argv[-3]).resolve()
STEM = sys.argv[-2]
TARGET = Path(sys.argv[-1]).resolve()

PARTS = (
    ("Printed upper", f"{STEM}-upper.step"),
    ("Printed lower", f"{STEM}-lower.step"),
    ("Vertical baffle", f"{STEM}-divider.step"),
    ("Continuous air path", f"{STEM}-air-path.step"),
    ("Handle foam left", f"{STEM}-handle-foam-left.step"),
    ("Handle foam right", f"{STEM}-handle-foam-right.step"),
    ("Joint gasket", f"{STEM}-gasket.step"),
    ("Hidden M3 screws", "07-m3-bolts-reference.step"),
    ("Captive M3 nuts", "08-m3-nuts-reference.step"),
    ("Mic steel disc", "09-mic-steel-disc-30mm.step"),
    ("DJI Mic Mini 2", "10-dji-mic-mini-2.step"),
    ("DJI USB-C dongle", "11-dji-usb-c-dongle.step"),
    ("Dongle magnet", "12-dongle-magnet.step"),
    ("Dongle steel disc", "13-dongle-steel-disc.step"),
    ("Brainwavz cushion", "14-brainwavz-cushion.step"),
    ("Pop mesh", "15-existing-pop-mesh.step"),
    ("Main foam", "16-main-foam.step"),
)


document = App.newDocument("SilentMicTechnical")
for label, filename in PARTS:
    shape = Part.Shape()
    shape.read(str(SOURCE_DIR / filename))
    name = re.sub(r"[^A-Za-z0-9_]", "", label.replace(" ", "_"))
    obj = document.addObject("PartDesign::Feature", name)
    obj.Label = label
    obj.Shape = shape

document.recompute()
TARGET.parent.mkdir(parents=True, exist_ok=True)
document.saveAs(str(TARGET))
print(f"Saved {TARGET}")
