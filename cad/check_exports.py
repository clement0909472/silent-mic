# SPDX-License-Identifier: CERN-OHL-S-2.0
"""Rebuild in isolation and compare published print files. Does not overwrite them."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import cadquery as cq


def main():
    source = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix="silent-mic-check-") as tmp:
        isolated = Path(tmp)
        for filename in ("whisper_mask_v0.py", "whisper_mask_v2_screwed.py", "whisper_mask_v2_compact.py"):
            shutil.copy2(source / filename, isolated / filename)
        for variant in ("screwed", "compact"):
            subprocess.run([sys.executable, str(isolated / f"whisper_mask_v2_{variant}.py")], check=True)
            current = source / "out" / f"v2-{variant}"
            rebuilt = isolated / "out" / f"v2-{variant}"
            for filename in rebuilt.glob("*.step"):
                published = cq.importers.importStep(str(current / filename.name))
                fresh = cq.importers.importStep(str(filename))
                assert published.val().isValid(), filename.name
                assert published.solids().size() == fresh.solids().size(), filename.name
                # Assembly references overlap intentionally: compare summed solid volumes.
                volume = lambda shape: sum(s.Volume() for s in shape.solids().vals())
                assert abs(volume(published) - volume(fresh)) < 0.01, filename.name
                a, b = published.val().BoundingBox(), fresh.val().BoundingBox()
                for axis in ("xmin", "xmax", "ymin", "ymax", "zmin", "zmax"):
                    assert abs(getattr(a, axis) - getattr(b, axis)) < 0.001, filename.name
                if filename.name.endswith(("-upper.step", "-lower.step")):
                    assert volume(published.cut(fresh)) + volume(fresh.cut(published)) < 0.01, filename.name
            for filename in rebuilt.glob("*.stl"):
                assert (current / filename.name).read_bytes() == filename.read_bytes(), filename.name
            print(f"PASS {variant}: STEP metrics, exact printed geometry and deterministic STL exports")


if __name__ == "__main__":
    main()
