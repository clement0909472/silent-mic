# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright 2026 Clement Barberousse
"""Silent Mic v3 galet : kit de decoupe des mousses.

Pour chaque piece de mousse ouverte : un gabarit imprimable (plaque de 1.2 mm au contour exact,
nom grave) a poser sur la plaque de mousse pour guider la lame, et le meme contour en SVG a
l'echelle 1 avec une barre de controle de 50 mm. Le manchon avant, qui tapisse une paroi conique,
est livre en bande developpee a plat (secteur d'anneau).

Usage : cad/guarded.sh -m 6 -t 600 .venv/bin/python cad/foam_templates.py
"""

from pathlib import Path
import json
import math
import sys

import cadquery as cq


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import whisper_mask_v0 as v0
import silent_mic_v3_galet as g

PLATE_T, ENGRAVE = 1.2, 0.6
BED = 175.0
OUT = HERE / "out" / "v3-galet" / "foam"


def polygon_face(points):
    return cq.Workplane("XY").polyline(points).close().extrude(PLATE_T)


def ellipse_points(a, b, n=180):
    return [(a * math.cos(2 * math.pi * i / n), b * math.sin(2 * math.pi * i / n)) for i in range(n)]


# ---------- pieces ----------

def disc_piece():
    """Couche du fond, a couper deux fois dans la plaque de 10 mm."""
    a, b, (nx0, nx1, ny) = g.disc_layer_shape()
    pts = []
    for x, y in ellipse_points(a, b, 240):
        if nx0 < x < nx1 and y < ny:
            continue
        pts.append((x, y))
    # remplace l'arc retire par le fond droit de l'encoche
    yb = lambda x: -b * math.sqrt(max(0.0, 1 - (x / a) ** 2))
    out, inserted = [], False
    for i, (x, y) in enumerate(pts):
        out.append((x, y))
        if not inserted and i + 1 < len(pts):
            x2, y2 = pts[i + 1]
            if y < 0 and x < nx0 + 0.01 and x2 > nx1 - 0.01:
                out += [(nx0, yb(nx0)), (nx0, ny), (nx1, ny), (nx1, yb(nx1))]
                inserted = True
    assert inserted, "encoche du fond non inseree"
    return out


def mid_ellipse(z):
    """Ellipse a mi-epaisseur du manchon a la hauteur z."""
    s = g.s_of(z)
    a, b = g.outer_profile(s)
    k = g.inset(s, g.WALL) + 0.2 + g.LINER_T / 2
    return a - k, b - k


def sleeve_piece():
    """Manchon avant developpe : secteur d'anneau (tronc de cone equivalent), raccord bout a bout
    a 6 h, une encoche rectangulaire au pied de chaque contrefort d'aimant du capot."""
    z0, z1 = g.liner_z()
    (a0, b0), (a1, b1) = mid_ellipse(z0), mid_ellipse(z1)
    p0, p1 = g.ellipse_arc_length(a0, b0, 0.0), g.ellipse_arc_length(a1, b1, 0.0)
    r0, r1 = p0 / (2 * math.pi), p1 / (2 * math.pi)
    dz = z1 - z0
    slant = math.hypot(dz, r1 - r0)
    rho0 = slant * r0 / (r1 - r0)
    rho1 = rho0 + slant
    theta = 2 * math.pi * r1 / rho1

    def frac(a, b, t):
        return g.ellipse_arc_length(a, b, 0.0, -math.pi / 2, t, 600) / g.ellipse_arc_length(a, b, 0.0)

    xg = 0.5  # raccord bout a bout a 6 h : le micro, au centre, ne coupe plus le manchon
    f_gap0 = frac(a0, b0, -math.pi / 2 + math.asin(xg / a0))
    f_gap1 = frac(a1, b1, -math.pi / 2 + math.asin(xg / a1))
    # encoches des contreforts : largeur du bossage + 1 mm, hauteur jusqu'a leur retour dans la paroi
    # contrefort (g.build_front_bosses) : cercle de rayon BOSS_R a h, qui se reduit a 0.8 mm en rentrant
    # dans la paroi a zb ; l'encoche prend sa largeur au bas du manchon + 1 mm, jusqu'a zb
    h = g.MAG_POCKET[1] + 1.2
    zb = h + g.STEEP * ((g.MAG_OFFSET + g.BOSS_R) - 2.3)
    r_bot = g.BOSS_R + (0.8 - g.BOSS_R) * (z0 - h) / (zb - h)
    n_h = (min(zb, z1) - z0) * slant / dz
    n_w = 2 * r_bot + 1.0
    notches = sorted(f % 1.0 for f in (frac(a0, b0, math.radians(t)) for t in g.MAG_T_DEG))
    pt = lambda rho, f: (rho * math.sin(theta * (f - 0.5)), -rho * math.cos(theta * (f - 0.5)))
    inner = []
    steps = 360
    f = f_gap0
    while f < 1 - f_gap0:
        hit = next((fn for fn in notches if abs(f - fn) * theta * rho0 < n_w / 2), None)
        if hit is not None:
            fa, fb = hit - n_w / 2 / (theta * rho0), hit + n_w / 2 / (theta * rho0)
            inner += [pt(rho0, fa), pt(rho0 + n_h, fa), pt(rho0 + n_h, fb), pt(rho0, fb)]
            f = fb + 1e-6
            notches.remove(hit)
            continue
        inner.append(pt(rho0, f))
        f += 1 / steps
    inner.append(pt(rho0, 1 - f_gap0))
    outer = [pt(rho1, 1 - f_gap1 - i * (1 - 2 * f_gap1) / steps) for i in range(steps + 1)]
    # nom : au milieu du plus grand intervalle libre entre encoches, tangent a la bande
    fs = sorted(f % 1.0 for f in (frac(a0, b0, math.radians(t)) for t in g.MAG_T_DEG))
    gaps = [(b - a, (a + b) / 2) for a, b in zip(fs, fs[1:]) if a > f_gap0 and b < 1 - f_gap0]
    fl = max(gaps)[1]
    lx, ly = pt((rho0 + rho1) / 2, fl)
    label_at = (lx, ly, math.degrees(theta * (fl - 0.5)), 4.0)
    info = {"rayons_developpes_mm": [round(rho0, 1), round(rho1, 1)], "angle_deg": round(math.degrees(theta), 1),
            "hauteur_bande_mm": round(slant, 1), "encoches": len(g.MAG_T_DEG), "encoche_mm": [round(n_w, 1), round(n_h, 1)]}
    return inner + outer, info, label_at


def area(points):
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]))) / 2


# ---------- sorties ----------

def template(points, label, sub="", at=None):
    """Plaque de 1.2 mm au contour ; nom grave a `at` = (x, y, angle, taille) ou au centre."""
    plate = polygon_face(points)
    bb = plate.val().BoundingBox()
    if at is None:
        at = ((bb.xmin + bb.xmax) / 2, (bb.ymin + bb.ymax) / 2, 0.0, 6.0 if bb.ylen > 25 else 4.0)
    x, y, ang, size = at
    txt = (cq.Workplane("XY").text(label + (" " + sub if sub else ""), size, -ENGRAVE, combine=False, halign="center", valign="center")
           .rotate((0, 0, 0), (0, 0, 1), ang).translate((x, y, PLATE_T)))
    cut = plate.cut(txt)
    assert vol(plate) - vol(cut) > 1.0, f"nom non grave sur le gabarit {label}"
    return cut


def vol(w):
    return sum(s.Volume() for s in w.solids().vals())


def svg(points, label, sub, path):
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    x0, y0, x1, y1 = min(xs) - 10, min(ys) - 25, max(xs) + 10, max(ys) + 22
    x1 = max(x1, x0 + 180.0)  # place pour la consigne et la barre de 50 mm
    w, h = x1 - x0, y1 - y0
    d = "M " + " L ".join(f"{x - x0:.2f},{y1 - y:.2f}" for x, y in points) + " Z"
    bar_y = h - 8
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.1f}mm" height="{h:.1f}mm" viewBox="0 0 {w:.2f} {h:.2f}">',
             f'<rect width="{w:.2f}" height="{h:.2f}" fill="white"/>',
             f'<path d="{d}" fill="none" stroke="black" stroke-width="0.3"/>',
             f'<line x1="10" y1="{bar_y:.2f}" x2="60" y2="{bar_y:.2f}" stroke="black" stroke-width="0.6"/>',
             f'<line x1="10" y1="{bar_y - 2:.2f}" x2="10" y2="{bar_y + 2:.2f}" stroke="black" stroke-width="0.3"/>',
             f'<line x1="60" y1="{bar_y - 2:.2f}" x2="60" y2="{bar_y + 2:.2f}" stroke="black" stroke-width="0.3"/>',
             f'<text x="64" y="{bar_y + 1.5:.2f}" font-size="4" font-family="sans-serif">50 mm : verifier a la regle avant de couper</text>',
             f'<text x="10" y="8" font-size="5" font-family="sans-serif">{label}</text>',
             f'<text x="10" y="14" font-size="3.5" font-family="sans-serif">{sub}</text>', "</svg>"]
    path.write_text("\n".join(parts))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sleeve_pts, sleeve_info, sleeve_label = sleeve_piece()
    pieces = [
        ("fond", disc_piece(), "x2", 10.0, 2, "plaque de 10 mm, deux couches identiques, encoche vers le bas (6 h)", None),
        ("manchon", sleeve_pts, "", 10.0, 1, "plaque de 10 mm, bord court (rayon interieur) vers le joint, raccord en bas (6 h)", sleeve_label),
    ]
    report = {}
    for name, pts, sub, thick, qty, note, at in pieces:
        plate = template(pts, name.upper(), sub, at)
        bb = plate.val().BoundingBox()
        assert plate.val().isValid() and plate.solids().size() == 1, name
        assert bb.xlen <= BED and bb.ylen <= BED, (name, bb.xlen, bb.ylen)
        cq.exporters.export(plate, str(OUT / f"gabarit-{name}.stl"), tolerance=0.05, angularTolerance=0.1)
        svg(pts, name.upper(), f"{sub} - {note}", OUT / f"contour-{name}.svg")
        a = area(pts)
        report[name] = {"plaque_mm": thick, "quantite": qty, "aire_mm2": round(a), "volume_cm3": round(a * thick * qty / 1000, 1),
                        "gabarit_mm": [round(bb.xlen, 1), round(bb.ylen, 1)], "note": note}
        print(name, report[name], flush=True)
    report["manchon"]["developpement"] = sleeve_info
    report["total_volume_cm3"] = round(sum(v["volume_cm3"] for k, v in report.items() if isinstance(v, dict) and "volume_cm3" in v), 1)
    (OUT / "kit-mousse.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print("total", report["total_volume_cm3"], "cm3 ->", OUT)


if __name__ == "__main__":
    main()
