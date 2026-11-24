# SPDX-License-Identifier: CERN-OHL-S-2.0
"""Rebuild in isolation and compare published print files. Does not overwrite them."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import cadquery as cq


SOURCES = ("whisper_mask_v0.py", "whisper_mask_v2_screwed.py", "whisper_mask_v2_compact.py",
           "silent_mic_v3_coupons.py", "silent_mic_v3_galet.py", "foam_templates.py", "guarded.sh")


def volume(shape):
    return sum(s.Volume() for s in shape.solids().vals())


def compare_steps(current, rebuilt, exact_suffixes=()):
    for filename in rebuilt.glob("*.step"):
        published = cq.importers.importStep(str(current / filename.name))
        fresh = cq.importers.importStep(str(filename))
        assert published.val().isValid(), filename.name
        # un STEP qui perd des faces se relit en zero solide : sans ce plancher, 0 == 0 passait
        assert published.solids().size() == fresh.solids().size() >= 1, filename.name
        # Assembly references overlap intentionally: compare summed solid volumes.
        assert abs(volume(published) - volume(fresh)) < 0.01, filename.name
        a, b = published.val().BoundingBox(), fresh.val().BoundingBox()
        for axis in ("xmin", "xmax", "ymin", "ymax", "zmin", "zmax"):
            assert abs(getattr(a, axis) - getattr(b, axis)) < 0.001, filename.name
        if filename.name.endswith(exact_suffixes):
            a_, b_ = published.val(), fresh.val()
            assert a_.cut(b_).Volume() + b_.cut(a_).Volume() < 0.01, filename.name


def compare_stls(current, rebuilt):
    for filename in rebuilt.glob("*.stl"):
        assert (current / filename.name).read_bytes() == filename.read_bytes(), filename.name


def main():
    source = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix="silent-mic-check-") as tmp:
        isolated = Path(tmp)
        for filename in SOURCES:
            shutil.copy2(source / filename, isolated / filename)
        for variant in ("screwed", "compact"):
            subprocess.run([sys.executable, str(isolated / f"whisper_mask_v2_{variant}.py")], check=True)
            current = source / "out" / f"v2-{variant}"
            rebuilt = isolated / "out" / f"v2-{variant}"
            compare_steps(current, rebuilt, ("-upper.step", "-lower.step"))
            compare_stls(current, rebuilt)
            print(f"PASS {variant}: STEP metrics, exact printed geometry and deterministic STL exports")
        # v3 galet : sous le garde memoire/duree (un booleen OCCT qui degenere a deja sature la machine)
        guard = [str(isolated / "guarded.sh"), "-m", "6", "-t", "600", sys.executable]
        for script in ("silent_mic_v3_coupons.py", "silent_mic_v3_galet.py", "foam_templates.py"):
            subprocess.run(guard + [str(isolated / script)], check=True, stdout=subprocess.DEVNULL)
        for sub in ("v3-galet", "v3-galet/coupons"):
            compare_steps(source / "out" / sub, isolated / "out" / sub,
                          ("-front.step", "-rear.step", "-cover.step", "-ring.step", "-r70.step", "cap.step"))
            compare_stls(source / "out" / sub, isolated / "out" / sub)
        compare_stls(source / "out" / "v3-galet" / "foam", isolated / "out" / "v3-galet" / "foam")
        print("PASS v3-galet: assertions, STEP metrics, exact printed geometry and deterministic STL exports")


if __name__ == "__main__":
    main()
