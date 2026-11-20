# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright 2026 Clement Barberousse
"""Silent Mic v3 galet : eprouvettes a imprimer avant le corps.

- un capot d'essai du coussin d'oreillette et trois colliers amovibles (3, 10 et 16 mm) ;
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
FLANGE_T, FLANGE_W, FLANGE_GAP = 1.2, 9.0, 0.2  # bride du collier amovible

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
    ring = ell_prism(*co, z_seat - 0.1, z_seat + height).cut(ell_prism(*ci, z_seat - 1, z_seat + height + 1))
    return ring.faces(">Z").edges().fillet(COLLAR_ROUND)


def teardrop_x(x0, zc, d, length):
    """Trou horizontal selon x, en goutte (toit a 45 deg) : imprimable sans support."""
    r = d / 2
    k = r / math.sqrt(2)
    prof = (cq.Workplane("YZ", origin=(x0, 0, zc)).moveTo(-k, k).lineTo(0, r * math.sqrt(2)).lineTo(k, k)
            .threePointArc((r, 0), (k, -k)).threePointArc((0, -r), (-k, -k)).threePointArc((-r, 0), (-k, k)).close())
    return prof.extrude(length)


def pocket_down(x, y, z0):
    """Poche d'aimant ouverte vers le plateau : toit conique a 45 deg au lieu d'un pont plat."""
    r, d = MAG_POCKET[0] / 2, MAG_POCKET[1]
    cyl = cq.Workplane("XY", origin=(x, y, z0 - 0.5)).circle(r).extrude(d + 0.5)
    roof = cq.Workplane("XY").newObject([cq.Solid.makeCone(r, 0.0, r, cq.Vector(x, y, z0 + d), cq.Vector(0, 0, 1))])
    return cyl.union(roof)


def clean_stl(path):
    """Retire les triangles degeneres qu'OCCT pose au sommet des cones (toits des poches d'aimant),
    puis exige un maillage ferme : chaque arete partagee par exactement deux faces."""
    import numpy as np
    path = Path(path)
    raw = path.read_bytes()
    n = int.from_bytes(raw[80:84], "little")
    assert len(raw) == 84 + 50 * n, f"{path.name} : STL binaire attendu"
    tri = np.frombuffer(raw, np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]), n, 84)
    f = np.unique(tri["v"].reshape(-1, 3), axis=0, return_inverse=True)[1].reshape(-1, 3)
    keep = (f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 2] != f[:, 0])
    f = f[keep]
    edges = np.sort(np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), axis=1)
    counts = np.unique(edges, axis=0, return_counts=True)[1]
    assert (counts == 2).all(), f"{path.name} : {int((counts != 2).sum())} aretes ouvertes ou partagees par plus de deux faces"
    if not keep.all():
        path.write_bytes(raw[:80] + int(keep.sum()).to_bytes(4, "little") + tri[keep].tobytes())
    return int((~keep).sum())


def vol(w):
    return sum(s.Volume() for s in w.solids().vals())


def seat_recess(z_seat):
    """Logement peu profond de la bride du collier dans l'appui du coussin."""
    fo = flange_outer()
    return ell_prism(fo[0] + 2 * FLANGE_GAP, fo[1] + 2 * FLANGE_GAP, z_seat - FLANGE_T - 0.1, z_seat + 1)


def flange_outer():
    return tuple(c + 2 * FLANGE_W for c in collar_inner())


def collar_insert(height):
    """Collier amovible : bride plate posee dans le logement, serree par le coussin."""
    ci = collar_inner()
    # bride biseautee a 38 deg (1.3 / 1) : va dans le logement droit du capot d'essai et dans le cone du corps
    fo = flange_outer()
    k = 2 * FLANGE_T / 1.3
    flange = cq.Workplane("XY").newObject([cq.Solid.makeLoft([ell_wire(fo[0] - k, fo[1] - k, 0), ell_wire(*fo, FLANGE_T)], True)])
    flange = flange.cut(ell_prism(*ci, -1, FLANGE_T + 1))
    ins = flange.union(collar(FLANGE_T, height))
    # hauteur gravee sur la bride, cote +x, lisible une fois le collier retire
    x = (collar_outer()[0] / 2 + flange_outer()[0] / 2) / 2
    label = (cq.Workplane(cq.Plane(origin=(x, 0, FLANGE_T), xDir=(0, 1, 0), normal=(0, 0, 1)))
             .text(f"{height:g}", 5, -0.4, combine=False, halign="center", valign="center"))
    return ins.cut(label)


def pad_test_cap():
    """Capot ferme : dos plat au plateau, appui du coussin en haut avec logement de collier."""
    z_seat = CAP_WALL + CAP_DEPTH
    ci = collar_inner()
    body = ell_prism(*SEAT, 0, z_seat)
    # l'entonnoir rejoint l'ouverture du collier sans rebord (sinon surplomb)
    z_top = z_seat - FLANGE_T - 0.3
    inner = ell_prism(SEAT[0] - 2 * CAP_WALL, SEAT[1] - 2 * CAP_WALL, CAP_WALL, z_top).intersect(funnel(*ci, z_top))
    inner = inner.union(ell_prism(*ci, z_top - 0.2, z_seat + 1))
    cap = body.cut(inner).cut(seat_recess(z_seat))
    return cap.cut(teardrop_x(SEAT[0] / 2 - CAP_WALL - 1, CAP_WALL + CABLE_PORT / 2 + 1.5, CABLE_PORT, CAP_WALL + 2))


def joint_coupon_halves(length=40.0, width=18.0, thick=6.0):
    """Troncon droit du joint : y = offset depuis la peau, z = 0 plan de joint."""
    def strip(y0, y1, z0, z1):
        return cq.Workplane("XY").box(length + 2, y1 - y0, z1 - z0).translate((0, (y0 + y1) / 2, (z0 + z1) / 2))

    pockets = lambda z0, d, dia=MAG_POCKET[0]: (
        cq.Workplane("XY", origin=(0, MAG_OFFSET, min(z0, z0 + d))).pushPoints([(-10, 0), (10, 0)])
        .circle(dia / 2).extrude(abs(d)))
    front = cq.Workplane("XY").box(length, width, thick).translate((0, width / 2, thick / 2))
    front = front.cut(strip(GROOVE[0], GROOVE[1], -1, GROOVE_DEPTH))
    for x in (-10, 10):
        front = front.cut(pocket_down(x, MAG_OFFSET, 0))
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
        clean_stl(out / f"{name}.stl")
        bb = shape.val().BoundingBox()
        report[name] = {"volume_cm3": round(vol(shape) / 1000, 2), "size_mm": [round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1)]}
        print(f"{name}: {report[name]}  ({time.perf_counter() - t:.1f} s)", flush=True)

    t = time.perf_counter()
    cap = pad_test_cap()
    print(f"construit capot en {time.perf_counter() - t:.1f} s", flush=True)
    assert CAP_DEPTH >= v0.MIC_SIZE[2] + 8.0, "place pour DJI a plat + ecouteur"
    save("pad-test-cap", cap)
    for h in CAP_COLLARS:
        ins = collar_insert(h)
        z_seat = CAP_WALL + CAP_DEPTH
        placed = ins.translate((0, 0, z_seat - FLANGE_T - 0.1))
        assert vol(placed.intersect(cap)) < 1e-6, "collier / capot"
        save(f"collar-insert-{h:g}mm", ins)
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
