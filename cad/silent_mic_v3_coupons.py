# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright 2026 Clement Barberousse
"""Silent Mic v3 galet : eprouvettes a imprimer avant le corps.

- trois capots d'essai du coussin d'oreillette (collier 3, 10 et 16 mm) ;
- eprouvette de joint (deux moities, deux poches d'aimant chacune, rainure de mousse) ;
- eprouvette de lumiere (bande translucide en marches de 0.8 a 2.4 mm).

Ce module porte aussi les parametres du coussin et du joint, repris par le corps.
Usage : cad/guarded.sh -m 6 -t 600 .venv/bin/python cad/silent_mic_v3_coupons.py
"""

from pathlib import Path
import math
import sys
import time

import cadquery as cq


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import whisper_mask_v0 as v0


# ---------- coussin d'oreillette ----------
# Montage v0/v2 eprouve : l'ouverture du coussin s'enfile sur un collier rigide.
PADS = {
    "brainwavz": {"outer": v0.PAD_OUTER, "opening": v0.PAD_OPENING, "thickness": v0.PAD_THICKNESS},
    # Type Sony MDR-7506, cotes de fiches vendeur, non verifiees sur piece.
    "small-oval": {"outer": (100.0, 81.0), "opening": (60.0, 40.0), "thickness": 20.0},
}
PAD = PADS["brainwavz"]
PAD_CLEARANCE = 2.0  # v0 : 2.5 ; 2.0 garde l'ouverture du collier a 62 x 42
COLLAR_WALL = 2.0
COLLAR_ROUND = 0.95  # arrondi du sommet, quasi demi-rond sur 2 mm
SEAT = (104.0, 84.0)
MIN_COLLAR_INNER = (62.0, 42.0)


def collar_outer(pad=PAD):
    return tuple(s - 2 * PAD_CLEARANCE for s in pad["opening"])


def collar_inner(pad=PAD):
    return tuple(s - 2 * COLLAR_WALL for s in collar_outer(pad))


# ---------- joint ----------
RING_DEPTH, RING_H = 2.5, 2.8  # anneau translucide visible
REBATE = 2.6
LED_CH = (2.6, 5.0, 2.2)  # offsets et profondeur de la rainure du filament LED
TONGUE = (6.0, 9.0, 2.0)  # offsets et hauteur de la languette (coque arriere)
GROOVE = (5.9, 9.1)  # rainure du capot avant
GASKET = (3.0, 2.0)  # bande de mousse a cellules fermees
GASKET_COMPRESSION = 0.55
GROOVE_DEPTH = TONGUE[2] + GASKET[1] - GASKET_COMPRESSION
MAGNET = (6.0, 2.0)
MAG_POCKET = (MAGNET[0] + 0.2, MAGNET[1] + 0.1)
MAG_OFFSET = 12.9
BOSS_R = MAG_POCKET[0] / 2 + 1.2

# ---------- capots d'essai ----------
CAP_COLLARS = (3.0, 10.0, 16.0)
CAP_DEPTH = 28.0  # interieur derriere l'appui : DJI 28.6 x 28 x 13.5 a plat + ecouteur
CAP_WALL = 3.0
CABLE_PORT = 5.5

LIGHT_STEPS = (0.8, 1.2, 1.6, 2.0, 2.4)
LIN_TOL, ANG_TOL = 0.1, 0.3


def ell_prism(w, h, z0, z1):
    return cq.Workplane("XY", origin=(0, 0, z0)).ellipse(w / 2, h / 2).extrude(z1 - z0)


def ell_wire(w, h, z):
    return cq.Workplane("XY", origin=(0, 0, z)).ellipse(w / 2, h / 2).wire().val()


def funnel(w, h, z_top, depth=40.0):
    """Entonnoir a 45 deg sous une ouverture : imprimable sans support."""
    return cq.Workplane("XY").newObject([cq.Solid.makeLoft(
        [ell_wire(w + 2 * depth, h + 2 * depth, z_top - depth), ell_wire(w, h, z_top)], True)])


def collar(z_seat, height, pad=PAD):
    co, ci = collar_outer(pad), collar_inner(pad)
    ring = ell_prism(*co, z_seat - 0.5, z_seat + height).cut(ell_prism(*ci, z_seat - 1, z_seat + height + 1))
    return ring.faces(">Z").edges().fillet(COLLAR_ROUND)


def teardrop_x(x0, zc, d, length):
    """Trou horizontal selon x, en goutte (toit a 45 deg) : imprimable sans support."""
    r = d / 2
    k = r / math.sqrt(2)
    prof = (cq.Workplane("YZ", origin=(x0, 0, zc)).moveTo(-k, k).lineTo(0, r * math.sqrt(2)).lineTo(k, k)
            .threePointArc((r, 0), (k, -k)).threePointArc((0, -r), (-k, -k)).threePointArc((-r, 0), (-k, k)).close())
    return prof.extrude(length)


def vol(w):
    return sum(s.Volume() for s in w.solids().vals())


def pad_test_cap(height):
    """Capot ferme : dos plat au plateau, appui du coussin en haut, collier au-dessus."""
    z_seat = CAP_WALL + CAP_DEPTH
    ci = collar_inner()
    body = ell_prism(*SEAT, 0, z_seat)
    # l'entonnoir rejoint l'interieur du collier sans rebord (sinon 1 mm en surplomb)
    z_top = z_seat - 0.5
    inner = ell_prism(SEAT[0] - 2 * CAP_WALL, SEAT[1] - 2 * CAP_WALL, CAP_WALL, z_top).intersect(funnel(*ci, z_top))
    inner = inner.union(ell_prism(*ci, z_top - 0.2, z_seat + 1))
    cap = body.cut(inner).union(collar(z_seat, height))
    cap = cap.cut(teardrop_x(SEAT[0] / 2 - CAP_WALL - 1, CAP_WALL + CABLE_PORT / 2 + 1.5, CABLE_PORT, CAP_WALL + 2))
    # repere grave au dos, lisible de l'exterieur (texte vu depuis -z)
    label = (cq.Workplane(cq.Plane(origin=(0, 0, 0), xDir=(-1, 0, 0), normal=(0, 0, -1)))
             .text(f"{height:g} mm", 12, -0.6, combine=False, halign="center", valign="center"))
    return cap.cut(label)


def joint_coupon_halves(length=40.0, width=18.0, thick=6.0):
    """Troncon droit du joint : y = offset depuis la peau, z = 0 plan de joint."""
    def strip(y0, y1, z0, z1):
        return cq.Workplane("XY").box(length + 2, y1 - y0, z1 - z0).translate((0, (y0 + y1) / 2, (z0 + z1) / 2))

    pockets = lambda z0, d, dia=MAG_POCKET[0]: (
        cq.Workplane("XY", origin=(0, MAG_OFFSET, min(z0, z0 + d))).pushPoints([(-10, 0), (10, 0)])
        .circle(dia / 2).extrude(abs(d)))
    front = cq.Workplane("XY").box(length, width, thick).translate((0, width / 2, thick / 2))
    front = front.cut(strip(GROOVE[0], GROOVE[1], -1, GROOVE_DEPTH)).cut(pockets(0, MAG_POCKET[1]))
    rear = cq.Workplane("XY").box(length, width, thick).translate((0, width / 2, -thick / 2))
    rear = rear.union(cq.Workplane("XY").box(length, TONGUE[1] - TONGUE[0], TONGUE[2] + 0.5)
                      .translate((0, (TONGUE[0] + TONGUE[1]) / 2, (TONGUE[2] - 0.5) / 2)))
    rear = rear.cut(strip(-1, REBATE, -RING_H, 1)).cut(strip(LED_CH[0], LED_CH[1], -LED_CH[2], 1))
    rear = rear.cut(pockets(0, -MAG_POCKET[1]))
    return front, rear


def light_coupon(width=12.0, step=10.0):
    out = None
    for i, t in enumerate(LIGHT_STEPS):
        b = cq.Workplane("XY").box(step + 0.01, width, t, centered=(False, True, False)).translate((i * step, 0, 0))
        out = b if out is None else out.union(b)
    return out


def check():
    ci = collar_inner()
    assert ci[0] >= MIN_COLLAR_INNER[0] - 1e-9 and ci[1] >= MIN_COLLAR_INNER[1] - 1e-9, ci
    comp = TONGUE[2] + GASKET[1] - GROOVE_DEPTH
    assert 0.5 <= comp <= 0.6, comp
    assert GROOVE[1] - GROOVE[0] >= GASKET[0] and TONGUE[1] - TONGUE[0] <= GROOVE[1] - GROOVE[0]
    assert TONGUE[0] - GROOVE[0] <= 0.15 and GROOVE[1] - TONGUE[1] <= 0.15, "centrage languette/rainure"
    assert LED_CH[0] >= REBATE and TONGUE[0] - LED_CH[1] >= 0.9
    return comp


def export(out=HERE / "out" / "v3-galet" / "coupons"):
    out.mkdir(parents=True, exist_ok=True)
    comp = check()
    report = {}

    def save(name, shape):
        t = time.perf_counter()
        assert shape.val().isValid() and shape.solids().size() == 1, name
        cq.exporters.export(shape, str(out / f"{name}.step"))
        cq.exporters.export(shape, str(out / f"{name}.stl"), tolerance=LIN_TOL, angularTolerance=ANG_TOL)
        bb = shape.val().BoundingBox()
        report[name] = {"volume_cm3": round(vol(shape) / 1000, 2), "size_mm": [round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1)]}
        print(f"{name}: {report[name]}  ({time.perf_counter() - t:.1f} s)", flush=True)

    for h in CAP_COLLARS:
        t = time.perf_counter()
        cap = pad_test_cap(h)
        print(f"construit capot {h:g} mm en {time.perf_counter() - t:.1f} s", flush=True)
        bb = cap.val().BoundingBox()
        assert bb.xlen <= 180 and bb.ylen <= 180 and bb.zlen <= 180
        inner = CAP_DEPTH
        assert inner >= v0.MIC_SIZE[2] + 8.0, "place pour DJI a plat + ecouteur"
        save(f"pad-test-cap-collar-{h:g}mm", cap)
    front, rear = joint_coupon_halves()
    assert vol(front.intersect(rear)) < 1e-6
    save("joint-coupon-front", front)
    # impression languette en haut : on garde l'orientation du corps (z vers le haut)
    save("joint-coupon-rear", rear)
    save("light-coupon-petg", light_coupon())
    (out / "coupons.json").write_text(json.dumps({"gasket_compression_mm": comp, "parts": report}, indent=2))
    print(f"OK compression joint {comp:.2f} mm, sorties {out}")


import json  # noqa: E402

if __name__ == "__main__":
    export()
