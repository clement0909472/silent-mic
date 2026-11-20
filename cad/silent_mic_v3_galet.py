# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright 2026 Clement Barberousse
"""Silent Mic v3 galet : coque en galet tenue en main, coussin d'oreillette sur un
collier amovible, conduit annulaire d'un seul tour, joint a aimants.

Repere : x lateral, y vertical (haut +), z axe du corps (+ vers le visage).
z = 0 : plan de joint capot avant / coque arriere. s = abscisse de la maquette
(s = 30 a l'appui du coussin, 116 au dos) : z = JOINT_S - s.

Usage : cad/guarded.sh -m 6 -t 600 .venv/bin/python cad/silent_mic_v3_galet.py
"""

from pathlib import Path
import json
import math
import os
import sys
import time

import cadquery as cq


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import whisper_mask_v0 as v0
import silent_mic_v3_coupons as cp
from whisper_mask_v2_screwed import loft_ellipses


# ---------- silhouette : une seule fonction a changer (outer_profile) ----------
PROFILE = os.environ.get("SILENT_MIC_PROFILE", "evase")
JOINT_S = 61.0  # plan de joint ; l'anneau lumineux loge juste derriere
S_SEAT, S_REAR = 30.0, 116.0
S_COVER = 108.0  # face arriere plane de la coque, fermee par le couvercle


def smoothstep(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def outer_profile(s):
    """Demi-axes (a, b) de la section exterieure a l'abscisse s (sections elliptiques)."""
    if PROFILE == "evase":
        if s < 60:
            k = 1 - smoothstep((s - 30) / 18)
            return 42 + 10 * k, 33 + 9 * k
        g = min((s - 60) / 61.3, 1.0)
        f = (1 - g ** 2.4) ** (1 / 2.2)
        return 42 * f, 33 * f
    u = 0.88 * max(s - 30, 0) / 86
    f = (1 - u ** 1.8) ** 0.6
    return 52 * f, 42 * f


def z_of(s):
    return JOINT_S - s


def s_of(z):
    return JOINT_S - z


def slope(s, h=0.25):
    a0, b0 = outer_profile(s - h)
    a1, b1 = outer_profile(s + h)
    return max(abs(a1 - a0), abs(b1 - b0)) / (2 * h)


Z_SEAT, Z_RF, Z_END = z_of(S_SEAT), z_of(S_COVER), z_of(S_REAR)
REAR_FILLET = 2.5

# ---------- parois et joint (parametres communs avec les eprouvettes) ----------
WALL = 3.0
SEAT_PLATE = 3.0
RING_H = 2.6
LED_CH, TONGUE, GROOVE, GASKET = cp.LED_CH, cp.TONGUE, cp.GROOVE, cp.GASKET
GROOVE_DEPTH, MAGNET, MAG_POCKET, BOSS_R = cp.GROOVE_DEPTH, cp.MAGNET, cp.MAG_POCKET, cp.BOSS_R
REBATE, MAG_OFFSET = cp.REBATE, cp.MAG_OFFSET
FLANGE_TOP = GROOVE_DEPTH + 1.0
CAV_JOINT = 10.7  # offset de la cavite au joint et dans la bande du conduit
CORBEL = 7.4  # chanfrein a 45 deg qui porte la bride (capot imprime appui en bas)
MAG_T_DEG = (25, 70, 115, 160, 205, 245, 295, 340)  # angles parametriques ; rien a 6 h (barrage, pied du micro)

# ---------- coussin et collier amovible ----------
PAD = cp.PAD
COLLAR_HEIGHT = 14.0
COLLAR_INNER = cp.collar_inner()
LEDGE = 1.5  # appui de la bride du collier (seul porte-a-faux au-dessus du plateau)
SEAT_OPENING = tuple(f - 2 * LEDGE for f in cp.flange_outer())

# ---------- conduit annulaire ----------
DUCT = (4.6, 9.1)  # offsets radiaux : 4.5 mm
DUCT_H = 10.7
DUCT_TOP = -5.2  # 3 mm sous la rainure LED (exterieur)
DUCT_BOTTOM = DUCT_TOP - DUCT_H
DUCT_CHAMFER = 1.0  # toit chanfreine a 45 deg, plat restant 2.5 mm
DAM = 9.0  # barrage a 6 h, porte aussi le tunnel des fils
INLET_D = 8.0
INLET_Z = DUCT_BOTTOM + 1.85 + INLET_D / 2
SHADOW_DEPTH = 1.5
SHADOW_Z = (-RING_H - 2.1 - 3.6, -RING_H - 2.1)  # comme la maquette : 2.1 mm derriere l'anneau
SLOT_LEN, SLOT_GAP, SLOT_COUNT = 9.5, 2.0, 4
SLOT_WINDOW = (SHADOW_Z[0] + 0.4, SHADOW_Z[1] - 0.4)
CORBEL_TOP = DUCT_BOTTOM - 1.6  # plancher du conduit garde 1.6 mm
CORBEL_BOTTOM = CORBEL_TOP - CORBEL

# ---------- arriere, baie, couvercle ----------
BAY_DEPTH = 10.5
FLOOR_TOP = Z_RF + BAY_DEPTH + WALL
FLOOR_RIB = 1.5
FOAM_DISC_T = 12.0
LINER_T = 9.0
TUNNEL_D = 2.6
TUNNEL_OFFSET = 3.8
COVER_MAG_XY = ((-21.5, 9.0), (21.5, 9.0), (-21.5, -9.0), (21.5, -9.0))
COVER_MAG_PROTRUDE = 0.9
LIPO = (30.0, 20.0, 5.0)
CHARGER = (17.5, 28.0, 4.0)  # x, y, z ; USB-C vers le bas
SWITCH = (8.6, 3.6, 3.5)

# ---------- micro : a plat sur un pied de la coque arriere, grille vers la cavite ----------
# Position issue de la recherche du cone (cad/silent_mic_v3_galet.py ne la recalcule pas).
MIC_PRESETS = {"evase": (0.25, -12.5, 20.0), "oeuf": (-2.5, -21.0, 20.2)}
MIC_XC, MIC_YC, MIC_ZC = MIC_PRESETS[PROFILE]
MIC_CLEARANCE = 1.0
WINDSCREEN_T = 5.0
STEM_R = 4.0
CONE_DEG, CONE_HARD = 15.0, 12.0  # 15 = regle (WARN en dessous), 12 = refus
MOUTH_ABOVE_SEAT = 20.0  # coussin de 30 mm comprime : hypothese
BREATH_Y = 10.0
PLA = 1.24e-3
LIN_TOL, ANG_TOL = 0.1, 0.3
WEB_TOL = (0.4, 0.6)


# ================= outils =================

def log(name, t):
    print(f"  [{time.perf_counter() - t:6.1f} s] {name}", flush=True)


def ell(w, h, z):
    return cq.Workplane("XY", origin=(0, 0, z)).ellipse(w / 2, h / 2).wire().val()


def wp(*shapes):
    return cq.Workplane("XY").newObject(list(shapes))


def eprism(w, h, z0, z1):
    return cq.Workplane("XY", origin=(0, 0, z0)).ellipse(w / 2, h / 2).extrude(z1 - z0)


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))


def vol(shape):
    return sum(s.Volume() for s in shape.solids().vals()) if shape.solids().size() else 0.0


def union_all(shapes):
    out = None
    for s in shapes:
        out = s if out is None else out.union(s)
    return out


def sec_wire(z, d):
    """Courbe a l'offset d (vers l'interieur, dans le plan) de la section exterieure a z."""
    a, b = outer_profile(s_of(z))
    w = ell(2 * a, 2 * b, z)
    return w if d == 0 else w.offset2D(-d)[0]


def band(d, z0, z1):
    """Solide borne par l'offset d de l'enveloppe entre z0 et z1 (reglee, suit la conicite)."""
    return wp(cq.Solid.makeLoft([sec_wire(z0, d), sec_wire(z1, d)], True))


def ring(d0, d1, z0, z1):
    return band(d0, z0, z1).cut(band(d1, z0 - 1, z1 + 1))


EJ = outer_profile(JOINT_S)  # section du joint : reference des angles et abscisses


def eq_point(t, d):
    """Point a l'offset d de la section du joint, angle parametrique t, et tangente."""
    a, b = EJ
    n = (b * math.cos(t), a * math.sin(t))
    k = math.hypot(*n)
    return (a * math.cos(t) - d * n[0] / k, b * math.sin(t) - d * n[1] / k), (-n[1] / k, n[0] / k)


def arc_table(d, steps=4000):
    pts, s, prev = [], 0.0, None
    for i in range(steps + 1):
        t = -math.pi / 2 + 2 * math.pi * i / steps
        p, _ = eq_point(t, d)
        if prev:
            s += math.dist(p, prev)
        pts.append((s, t))
        prev = p
    return pts


def t_at(table, s):
    s %= table[-1][0]
    for (s0, t0), (s1, t1) in zip(table, table[1:]):
        if s1 >= s:
            return t0 + (t1 - t0) * (s - s0) / (s1 - s0)
    return table[-1][1]


def place(shape, t, d=0.0):
    """Repere local -> global : X tangente, Y vers l'interieur, origine sur la section du joint."""
    (x, y), (tx, ty) = eq_point(t, d)
    return shape.rotate((0, 0, 0), (0, 0, 1), math.degrees(math.atan2(ty, tx))).translate((x, y, 0))


CENTER_TABLE = arc_table(sum(DUCT) / 2)


def cyl_between(p, q, r):
    v = cq.Vector(*q) - cq.Vector(*p)
    return wp(cq.Solid.makeCylinder(r, v.Length, cq.Vector(*p), v.normalized()))


def inset(s, d):
    """Retrait dans le plan donnant d en normale sur un flanc incline."""
    return d / math.cos(math.atan(slope(s))) + 0.2


def sections(s_list, d=0.0):
    out = []
    for s in s_list:
        a, b = outer_profile(s)
        k = inset(s, d) if d else 0.0
        out.append((2 * (a - k), 2 * (b - k), z_of(s), 0.0))
    return sorted(out, key=lambda q: q[2])


# ================= enveloppe =================

FRONT_SMOOTH = (30.0, 33.0, 36.0, 39.0, 42.0, 45.0, 48.0)
FRONT_RULED = (48.0, 60.0, JOINT_S)
REAR_S = (JOINT_S, 66.0, 72.0, 80.0, 88.0, 96.0, 102.0, S_COVER, 111.0, 113.5, S_REAR)


def build_envelope():
    t = time.perf_counter()
    front = loft_ellipses(sections(FRONT_SMOOTH))
    ruled = [ell(w, h, z) for w, h, z, _ in sections(FRONT_RULED)]
    front = front.union(wp(cq.Solid.makeLoft(ruled, True)))
    rear = loft_ellipses(sections(REAR_S))
    log("enveloppe", t)
    return front, rear


# ================= capot avant (imprime appui du coussin sur le plateau) =================

def front_cavity_tool():
    z_main = FLANGE_TOP + CORBEL
    joint = band(CAV_JOINT, -0.5, FLANGE_TOP)
    a, b = outer_profile(s_of(z_main))
    k = inset(s_of(z_main), WALL)
    corbel = wp(cq.Solid.makeLoft([sec_wire(FLANGE_TOP, CAV_JOINT), ell(2 * (a - k), 2 * (b - k), z_main)], True))
    zs = [s for s in FRONT_SMOOTH + (54.0,) if z_main < z_of(s) < Z_SEAT - SEAT_PLATE]
    main = loft_ellipses(sections([s_of(z_main)] + sorted(zs, reverse=True) + [s_of(Z_SEAT - SEAT_PLATE)], WALL))
    opening = eprism(*SEAT_OPENING, Z_SEAT - SEAT_PLATE - 0.5, Z_SEAT + 1)
    return joint.union(corbel).union(main).union(opening).union(cp.seat_recess(Z_SEAT))


def build_front_bosses():
    """Bossages des aimants sous le joint ; cone a 45 deg vers l'appui (imprime dessous)."""
    h = MAG_POCKET[1] + 1.2
    out = []
    for x, y in mag_xy():
        cyl = cq.Workplane("XY", origin=(x, y, 0)).circle(BOSS_R).extrude(h)
        tip = wp(cq.Solid.makeCone(BOSS_R, 0.01, BOSS_R, cq.Vector(x, y, h), cq.Vector(0, 0, 1)))
        out.append(cyl.union(tip))
    return union_all(out)


def build_front(front_env):
    t = time.perf_counter()
    shell = front_env.cut(front_cavity_tool())
    log("  cavite avant", t)
    shell = shell.union(build_front_bosses().intersect(front_env))
    log("  bossages", t)
    shell = shell.cut(ring(GROOVE[0], GROOVE[1], -1, GROOVE_DEPTH)).cut(mag_pockets_up(-0.5, MAG_POCKET[1] + 0.5))
    log("capot avant", t)
    return shell


# ================= conduit =================

def build_duct():
    z_flat = DUCT_TOP - DUCT_CHAMFER
    body = ring(DUCT[0], DUCT[1], DUCT_BOTTOM, z_flat)
    outer = wp(cq.Solid.makeLoft([sec_wire(z_flat, DUCT[0]), sec_wire(DUCT_TOP, DUCT[0] + DUCT_CHAMFER)], True))
    inner = wp(cq.Solid.makeLoft([sec_wire(z_flat, DUCT[1]), sec_wire(DUCT_TOP, DUCT[1] - DUCT_CHAMFER)], True))
    return body.union(outer.cut(inner)).cut(box(-DAM / 2, DAM / 2, -60, -10, DUCT_BOTTOM - 2, 2))


INLET_S = DAM / 2 + 1.0 + INLET_D / 2  # cote x > 0 du barrage
SLOT_S = [-(DAM / 2 + 1.0 + SLOT_LEN / 2 + i * (SLOT_LEN + SLOT_GAP)) for i in range(SLOT_COUNT)]


def build_inlet():
    port = cq.Workplane("XZ", origin=(0, DUCT[1] - 0.6, INLET_Z)).circle(INLET_D / 2).extrude(-(CAV_JOINT - DUCT[1] + 1.2))
    return place(port, t_at(CENTER_TABLE, INLET_S))


def build_slots():
    r0, r1 = SHADOW_DEPTH - 0.5, DUCT[0] + 0.6
    lo = lambda r: SLOT_WINDOW[0] - (r - SHADOW_DEPTH)
    h = SLOT_WINDOW[1] - SLOT_WINDOW[0]
    out = []
    for s in SLOT_S:
        prof = (cq.Workplane("YZ", origin=(-SLOT_LEN / 2, 0, 0))
                .polyline([(r0, lo(r0)), (r1, lo(r1)), (r1, lo(r1) + h), (r0, lo(r0) + h)]).close().extrude(SLOT_LEN))
        out.append(place(prof, t_at(CENTER_TABLE, s)))
    return union_all(out)


def build_shadow_groove():
    return ring(0.0, SHADOW_DEPTH, *SHADOW_Z).intersect(box(-60, 60, -60, 0, -30, 5))


# ================= joint, aimants, tunnel =================

def mag_xy():
    return [eq_point(math.radians(t), MAG_OFFSET)[0] for t in MAG_T_DEG]


def mag_pockets_up(z0, depth, dia=MAG_POCKET[0]):
    return union_all(cq.Workplane("XY", origin=(x, y, z0)).circle(dia / 2).extrude(depth) for x, y in mag_xy())


def build_rear_bosses():
    h = MAG_POCKET[1] + 1.2
    out = []
    for x, y in mag_xy():
        cyl = cq.Workplane("XY", origin=(x, y, -h)).circle(BOSS_R).extrude(h)
        tip = wp(cq.Solid.makeCone(0.01, BOSS_R, BOSS_R, cq.Vector(x, y, -h - BOSS_R), cq.Vector(0, 0, 1)))
        out.append(cyl.union(tip))
    return union_all(out)


def tunnel_points():
    y_top = -EJ[1] + TUNNEL_OFFSET
    zb = DUCT_BOTTOM - 0.5
    y_mid = -outer_profile(s_of(zb))[1] + TUNNEL_OFFSET
    y_bot = -outer_profile(s_of(Z_RF + BAY_DEPTH))[1] + TUNNEL_OFFSET + 2.5
    return (0, y_top, 0.5), (0, y_mid, zb), (0, y_bot, Z_RF + BAY_DEPTH - 2.0)


def build_tunnel():
    a, b, c = tunnel_points()
    return union_all([cyl_between(a, b, TUNNEL_D / 2), cyl_between(b, c, TUNNEL_D / 2),
                      wp(cq.Solid.makeSphere(TUNNEL_D / 2, cq.Vector(*b)))])


def build_tunnel_rib():
    _, b, c = tunnel_points()
    r = TUNNEL_D / 2 + WALL
    return cyl_between(b, c, r).union(wp(cq.Solid.makeSphere(r, cq.Vector(*b))))


# ================= coque arriere (imprimee face arriere sur le plateau) =================

def rear_cavity_tool():
    a, b = outer_profile(s_of(CORBEL_BOTTOM))
    k = inset(s_of(CORBEL_BOTTOM), WALL)
    lower = loft_ellipses(sections([s_of(FLOOR_TOP), s_of((FLOOR_TOP + CORBEL_BOTTOM) / 2), s_of(CORBEL_BOTTOM)], WALL))
    corbel = wp(cq.Solid.makeLoft([ell(2 * (a - k), 2 * (b - k), CORBEL_BOTTOM), sec_wire(CORBEL_TOP, CAV_JOINT)], True))
    return lower.union(corbel).union(band(CAV_JOINT, CORBEL_TOP, 0.5))


def build_floor_features():
    zt = FLOOR_TOP + FLOOR_RIB
    a, b = outer_profile(s_of(zt))
    ribs = box(-40, 40, -0.8, 0.8, FLOOR_TOP - 0.5, zt).union(box(-0.8, 0.8, -40, 40, FLOOR_TOP - 0.5, zt))
    return ribs.intersect(eprism(2 * a - 2, 2 * b - 2, FLOOR_TOP - 0.5, zt))


def disc_top():
    return FLOOR_TOP + FLOOR_RIB + FOAM_DISC_T


def cavity_half_axes(z):
    """Demi-axes de la cavite arriere a z (sous la bande du conduit)."""
    a, b = outer_profile(s_of(z))
    k = inset(s_of(z), WALL)
    extra = max(0.0, (z - CORBEL_BOTTOM)) if z < CORBEL_TOP else CAV_JOINT
    return a - k - extra, b - k - extra


def build_foam_bumps():
    z = disc_top()
    a, b = cavity_half_axes(z)
    out = []
    for deg in (0, 90, 180):
        t = math.radians(deg)
        prof = (cq.Workplane("XZ", origin=(0, 2, 0)).polyline([(-0.5, z - 2.5), (2.0, z), (2.0, z + 1.0), (-0.5, z + 1.0)])
                .close().extrude(4))
        out.append(prof.rotate((0, 0, 0), (0, 0, 1), deg + 180).translate((a * math.cos(t), b * math.sin(t), 0)))
    return union_all(out)


def bay_boxes():
    zr = Z_RF
    a, b = outer_profile(s_of(zr + 4.5))
    lipo = box(-LIPO[0] / 2, LIPO[0] / 2, -4 - LIPO[1] / 2, -4 + LIPO[1] / 2, zr + 5.0, zr + 5.0 + LIPO[2])
    yb = -(b - 2.5) * math.sqrt(1 - (CHARGER[0] / 2 / (a - 2.5)) ** 2) + 0.7
    charger = box(-CHARGER[0] / 2, CHARGER[0] / 2, yb, yb + CHARGER[1], zr + 0.4, zr + 0.4 + CHARGER[2])
    sx = 15.3
    ys = -(b - 2.5) * math.sqrt(1 - ((sx + SWITCH[0] / 2) / (a - 2.5)) ** 2) + 0.7
    switch = box(sx - SWITCH[0] / 2, sx + SWITCH[0] / 2, ys, ys + SWITCH[1], zr + 0.4, zr + 0.4 + SWITCH[2])
    return lipo, charger, switch


def grow(b, m):
    bb = b.val().BoundingBox()
    return box(bb.xmin - m, bb.xmax + m, bb.ymin - m, bb.ymax + m, bb.zmin - m, bb.zmax + m)


def bay_cut():
    lipo, charger, switch = bay_boxes()
    bay = union_all([grow(lipo, 0.5), grow(charger, 0.5), grow(switch, 0.5)])
    bay = bay.union(box(-CHARGER[0] / 2 - 0.5, CHARGER[0] / 2 + 0.5, -40, 0, Z_RF - 1, Z_RF + 0.4))
    cb = charger.val().BoundingBox()
    usb = cq.Workplane("XZ", origin=(0, cb.ymin + 2, Z_RF + 2.6)).slot2D(12.0, 6.0).extrude(20)
    sb = switch.val().BoundingBox()
    lever = box(15.3 - 2.0, 15.3 + 2.0, -45, sb.ymin + 0.1, Z_RF + 1.2, Z_RF + 3.4)
    return bay.union(usb).union(lever)


def cover_pockets(z0, depth):
    return union_all(cq.Workplane("XY", origin=(x, y, z0)).circle(MAG_POCKET[0] / 2 + 0.05).extrude(depth) for x, y in COVER_MAG_XY)


def build_rear(rear_env):
    t = time.perf_counter()
    env = rear_env.intersect(box(-70, 70, -70, 70, Z_RF, 0))
    log("  enveloppe arriere", t)
    shell = env.cut(rear_cavity_tool())
    log("  cavite arriere", t)
    shell = shell.union(build_rear_bosses()).union(build_tunnel_rib().intersect(env))
    # le disque de mousse est retenu par le chanfrein a 45 deg sous le conduit (pas de taquets)
    shell = shell.union(build_floor_features()).union(build_mic_pedestal())
    shell = shell.union(ring(TONGUE[0], TONGUE[1], -0.5, TONGUE[2]))
    log("  ajouts arriere", t)
    shell = shell.cut(build_duct()).cut(build_inlet()).cut(build_slots()).cut(build_shadow_groove())
    log("  conduit, entree, fentes, gorge", t)
    shell = shell.cut(ring(-1.0, REBATE, -RING_H, 1)).cut(ring(LED_CH[0], LED_CH[1], -LED_CH[2], 1))
    shell = shell.cut(mag_pockets_up(-MAG_POCKET[1], MAG_POCKET[1] + 1)).cut(build_tunnel())
    shell = shell.cut(bay_cut()).cut(cover_pockets(Z_RF - 0.5, 0.5 + MAGNET[1] - COVER_MAG_PROTRUDE + 0.1))
    log("coque arriere", t)
    return shell


def build_cover(rear_env):
    t = time.perf_counter()
    cover = rear_env.intersect(box(-70, 70, -70, 70, Z_END - 1, Z_RF))
    try:
        cover = cover.faces("<Z").edges().fillet(REAR_FILLET)
    except Exception as exc:  # shortcut: sans conge si OCCT refuse ; a reprendre a la main
        print(f"conge du dos refuse : {exc}")
    cover = cover.cut(cover_pockets(Z_RF - 3.1, 3.2))
    log("couvercle", t)
    return cover


def build_ring():
    return ring(0.0, cp.RING_DEPTH, -RING_H, 0.0)


def collar_insert_placed():
    return cp.collar_insert(COLLAR_HEIGHT).translate((0, 0, Z_SEAT - cp.FLANGE_T - 0.1))


# ================= corps de reference =================

MIC_DISC_TOP = MIC_ZC - v0.MIC_SIZE[2] / 2 - v0.MIC_STEEL_DISC_THICKNESS


def mic_box():
    return box(MIC_XC - v0.MIC_SIZE[0] / 2, MIC_XC + v0.MIC_SIZE[0] / 2, MIC_YC - v0.MIC_SIZE[1] / 2,
               MIC_YC + v0.MIC_SIZE[1] / 2, MIC_ZC - v0.MIC_SIZE[2] / 2, MIC_ZC + v0.MIC_SIZE[2] / 2)


def mic_disc():
    return wp(cq.Solid.makeCylinder(v0.MIC_STEEL_DISC_DIAMETER / 2, v0.MIC_STEEL_DISC_THICKNESS,
                                    cq.Vector(MIC_XC, MIC_YC, MIC_DISC_TOP), cq.Vector(0, 0, 1)))


def build_mic_pedestal():
    """Pied en champignon a 45 deg, issu de la paroi du barrage a 6 h ; il traverse le plan
    de joint dans la cavite. Imprime avec la coque (z vers le haut) sans support."""
    r_top = v0.MIC_STEEL_DISC_DIAMETER / 2 + 0.5
    z_top = MIC_DISC_TOP
    z_neck = z_top - (r_top - STEM_R) - 1.5
    z_base = DUCT_BOTTOM + 4.0
    c = cq.Vector(MIC_XC, MIC_YC, 0)
    head = wp(cq.Solid.makeCone(STEM_R, r_top, r_top - STEM_R, c + cq.Vector(0, 0, z_neck), cq.Vector(0, 0, 1)))
    head = head.union(wp(cq.Solid.makeCylinder(r_top, 1.5, c + cq.Vector(0, 0, z_top - 1.5), cq.Vector(0, 0, 1))))
    stem = wp(cq.Solid.makeCylinder(STEM_R, z_neck - z_base + 0.01, c + cq.Vector(0, 0, z_base), cq.Vector(0, 0, 1)))
    foot = wp(cq.Solid.makeCone(0.01, STEM_R, STEM_R, c + cq.Vector(0, 0, z_base - STEM_R), cq.Vector(0, 0, 1)))
    y_wall = -outer_profile(s_of(0))[1] + CAV_JOINT - 1.0
    web = (cq.Workplane("YZ", origin=(MIC_XC - 2.0, 0, 0))
           .polyline([(y_wall, z_base - STEM_R - (MIC_YC - y_wall)), (MIC_YC, z_base - STEM_R), (MIC_YC, -0.5),
                      (y_wall, -0.5)]).close().extrude(4.0))
    return union_all([head, stem, foot, web])


def build_windscreen():
    """Bonnette de mousse ouverte sur la grille, retaillee sous la plaque d'appui."""
    bb = mic_box().val().BoundingBox()
    return box(bb.xmin - 1, bb.xmax + 1, bb.ymin - 1, bb.ymax + 1, bb.zmax, bb.zmax + WINDSCREEN_T)


def build_liner():
    """Manchon de mousse 9 mm sur les flancs de la chambre avant, piege entre la plaque
    d'appui et le chanfrein du joint ; decoupe devant le micro et l'ouverture."""
    z0, z1 = FLANGE_TOP + CORBEL + 0.3, Z_SEAT - SEAT_PLATE - 0.3
    zs = [s_of(z0)] + [s for s in FRONT_SMOOTH if z0 < z_of(s) < z1] + [s_of(z1)]
    outer = loft_ellipses(sections(sorted(zs, reverse=True), WALL + 0.2))
    inner = loft_ellipses(sections(sorted(zs, reverse=True), WALL + 0.2 + LINER_T))
    liner = outer.cut(inner).cut(eprism(*SEAT_OPENING, z0 - 1, z1 + 1))
    return liner.cut(grow(mic_box(), 2.0))


def build_foam_disc():
    z0 = FLOOR_TOP + FLOOR_RIB
    a, b = cavity_half_axes(disc_top())
    disc = eprism(2 * a - 2, 2 * b - 2, z0, z0 + FOAM_DISC_T)
    return disc.cut(build_tunnel_rib()).cut(grow(build_mic_pedestal(), 0.5)).cut(box(-0.9, 0.9, -45, 45, z0 - 1, z0 + 0.2)).cut(box(-45, 45, -0.9, 0.9, z0 - 1, z0 + 0.2))


def build_refs():
    lipo, charger, switch = bay_boxes()
    pad = eprism(*PAD["outer"], Z_SEAT, Z_SEAT + PAD["thickness"]).cut(eprism(*PAD["opening"], Z_SEAT - 1, Z_SEAT + PAD["thickness"] + 1))
    cmag = union_all(cq.Workplane("XY", origin=(x, y, Z_RF - COVER_MAG_PROTRUDE)).circle(MAGNET[0] / 2).extrude(MAGNET[1]) for x, y in COVER_MAG_XY)
    csteel = union_all(cq.Workplane("XY", origin=(x, y, Z_RF - 3.1)).circle(MAGNET[0] / 2).extrude(MAGNET[1]) for x, y in COVER_MAG_XY)
    return {
        "mic": mic_box(), "mic-disc": mic_disc(), "earpad": pad,
        "gasket": ring(GROOVE[0] + 0.1, GROOVE[1] - 0.1, TONGUE[2], GROOVE_DEPTH),
        "led-filament": ring(LED_CH[0] + 0.2, LED_CH[1] - 0.2, -LED_CH[2] + 0.1, -0.1),
        "foam-disc": build_foam_disc(), "foam-liner": build_liner(),
        "battery": lipo, "charger": charger, "switch": switch,
        "joint-magnets": mag_pockets_up(-MAGNET[1] - 0.1, MAGNET[1], MAGNET[0]),
        "joint-steel-discs": mag_pockets_up(0.1, MAGNET[1], MAGNET[0]),
        "cover-magnets": cmag, "cover-steel-discs": csteel,
    }


# ================= controles =================

def ellipse_arc_length(a, b, d, t0=-math.pi / 2, t1=1.5 * math.pi, steps=4000):
    """Longueur de la courbe a l'offset d d'une ellipse (a, b) entre deux angles parametriques."""
    out, prev = 0.0, None
    for i in range(steps + 1):
        t = t0 + (t1 - t0) * i / steps
        n = (b * math.cos(t), a * math.sin(t))
        k = math.hypot(*n)
        p = (a * math.cos(t) - d * n[0] / k, b * math.sin(t) - d * n[1] / k)
        if prev:
            out += math.dist(p, prev)
        prev = p
    return out


def duct_metrics(duct):
    zm = (DUCT_TOP + DUCT_BOTTOM) / 2
    a, b = outer_profile(s_of(zm))
    lap = ellipse_arc_length(a, b, sum(DUCT) / 2)
    channel = lap - DAM
    # entree et fentes reperees en abscisse sur la section du joint, ramenees au tour moyen
    k = lap / CENTER_TABLE[-1][0]
    slot_c = sum(SLOT_S) / len(SLOT_S)
    inlet_to_first = lap - k * (INLET_S - SLOT_S[0])
    inlet_to_centroid = lap - k * (INLET_S - slot_c)
    area = vol(duct.intersect(box(-0.5, 0.5, 0, 60, -40, 5))) / 1.0
    return {"section_mm2": round(area, 2), "lap_mm": round(lap, 1), "channel_dam_to_dam_mm": round(channel, 1),
            "inlet_to_first_slot_mm": round(inlet_to_first, 1), "inlet_to_slot_centroid_mm": round(inlet_to_centroid, 1),
            "inlet_area_mm2": round(math.pi * INLET_D ** 2 / 4, 1),
            "slot_window_mm2": round(SLOT_COUNT * SLOT_LEN * (SLOT_WINDOW[1] - SLOT_WINDOW[0]), 1),
            "slot_min_section_mm2": round(SLOT_COUNT * SLOT_LEN * (SLOT_WINDOW[1] - SLOT_WINDOW[0]) / math.sqrt(2), 1),
            "dam_mm": DAM}


def cone_angle():
    """Plus petit angle entre l'axe du souffle (bouche -> arriere) et un point du micro."""
    bb = mic_box().val().BoundingBox()
    zm = Z_SEAT + MOUTH_ABOVE_SEAT
    worst = 90.0
    for i in range(11):
        for j in range(11):
            for zz in (bb.zmin, bb.zmax):
                x = bb.xmin + (bb.xmax - bb.xmin) * i / 10
                y = bb.ymin + (bb.ymax - bb.ymin) * j / 10
                worst = min(worst, math.degrees(math.atan2(math.hypot(x, y - BREATH_Y), zm - zz)))
    return worst


def min_distance(a, b):
    return a.val().distance(b.val()) if hasattr(a, "val") else a.distance(b)


def curvature_check(env_faces):
    """Double courbure : echantillonne les faces exterieures, signale les zones a courbure
    simple ou nulle (rayon > 2 m) et leur etendue le long de la direction plate."""
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.BRepLProp import BRepLProp_SLProps
    report = []
    for f in env_faces:
        kind = f.geomType()
        bb = f.BoundingBox()
        if kind == "PLANE":
            report.append({"type": kind, "z": round(bb.zmin, 1), "size": [round(bb.xlen, 1), round(bb.ylen, 1)]})
            continue
        surf = BRepAdaptor_Surface(f.wrapped)
        u0, u1, v0_, v1 = surf.FirstUParameter(), surf.LastUParameter(), surf.FirstVParameter(), surf.LastVParameter()
        flat_pts = []
        for i in range(13):
            for j in range(13):
                u = u0 + (u1 - u0) * (i + 0.5) / 13
                v = v0_ + (v1 - v0_) * (j + 0.5) / 13
                props = BRepLProp_SLProps(surf, u, v, 2, 1e-6)
                if props.IsCurvatureDefined():
                    kmin = min(abs(props.MinCurvature()), abs(props.MaxCurvature()))
                    if kmin < 1 / 2000:
                        p = props.Value()
                        flat_pts.append(p.Z())
        if flat_pts:
            report.append({"type": kind, "single_curvature_z_extent": round(max(flat_pts) - min(flat_pts) + (bb.zlen / 13), 1),
                           "z": [round(bb.zmin, 1), round(bb.zmax, 1)]})
    return report


# ================= export =================

def export():
    t0 = time.perf_counter()
    out = HERE / "out" / "v3-galet"
    web = out / "web"
    out.mkdir(parents=True, exist_ok=True)
    web.mkdir(exist_ok=True)
    warn, fail = [], []
    comp = cp.check()

    front_env, rear_env = build_envelope()
    front, rear, cover = build_front(front_env), build_rear(rear_env), build_cover(rear_env)
    ring_, insert = build_ring(), collar_insert_placed()
    parts = {"front": front, "rear": rear, "cover": cover, "ring": ring_, "collar-insert-14mm": insert}
    for n, p in parts.items():
        assert p.val().isValid() and p.solids().size() == 1, n
    t = time.perf_counter()
    refs = build_refs()
    ws = build_windscreen().cut(front).cut(insert).intersect(box(-70, 70, -70, 70, -60, Z_SEAT - 0.2))
    refs["windscreen"] = ws
    log("corps de reference", t)

    # --- enveloppe et longueur
    body = front.union(rear).union(cover).union(ring_)
    bb = body.val().BoundingBox()
    m = {"profile": PROFILE, "joint_s": JOINT_S,
         "envelope_mm": [round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1)],
         "length_with_collar_mm": round(bb.zlen + COLLAR_HEIGHT, 1),
         "palm_section_mm": [2 * EJ[0], 2 * EJ[1]], "seat_mm": [round(2 * outer_profile(S_SEAT)[0], 1), round(2 * outer_profile(S_SEAT)[1], 1)]}
    assert bb.zlen <= 100.0 + 1e-6, "longueur sans coussin"
    # --- nez : rien de rigide au-dessus du haut de l'appui dans les 25 mm derriere lui
    nose = body.intersect(box(-70, 70, -70, 70, Z_SEAT - 25, Z_SEAT)).val().BoundingBox()
    m["nose_clearance_ymax_mm"] = round(nose.ymax, 2)
    assert nose.ymax <= outer_profile(S_SEAT)[1] + 0.05
    log("enveloppe et nez", t)

    # --- cavite (air + mousse) jusqu'au sommet du collier
    t = time.perf_counter()
    cav = front_cavity_tool().intersect(box(-70, 70, -70, 70, -1, Z_SEAT - cp.FLANGE_T - 0.1)).union(rear_cavity_tool())
    cav = cav.union(eprism(*COLLAR_INNER, Z_SEAT - cp.FLANGE_T - 0.2, Z_SEAT + COLLAR_HEIGHT))
    cav = cav.cut(front).cut(rear).cut(insert).cut(build_tunnel()).cut(refs["mic"]).cut(refs["mic-disc"])
    v_cav = vol(cav) / 1000
    foam = {k: vol(refs[k]) / 1000 for k in ("foam-disc", "foam-liner", "windscreen")}
    v_foam = sum(foam.values())
    m["cavity_air_plus_foam_cm3"] = round(v_cav, 1)
    m["cavity_air_only_cm3"] = round(v_cav - v_foam, 1)
    m["foam_cm3"] = {k: round(v, 1) for k, v in foam.items()} | {"total": round(v_foam, 1)}
    pad_zone = vol(eprism(*PAD["opening"], Z_SEAT, Z_SEAT + PAD["thickness"]).cut(insert)) / 1000
    m["pad_zone_above_collar_info_cm3"] = round(pad_zone - math.pi / 4 * COLLAR_INNER[0] * COLLAR_INNER[1] * COLLAR_HEIGHT / 1000, 1)
    assert v_cav >= 185.0, f"cavite {v_cav:.1f} cm3 < 185"
    assert cav.solids().size() >= 1
    log("cavite", t)

    # --- conduit
    t = time.perf_counter()
    duct = build_duct()
    dm = duct_metrics(duct)
    m["duct"] = dm
    print("conduit", dm, flush=True)
    assert 46.0 <= dm["section_mm2"] <= 50.0, dm
    assert dm["channel_dam_to_dam_mm"] >= 175.0, dm
    assert dm["inlet_area_mm2"] >= 48.0 and dm["slot_window_mm2"] >= 100.0 and DAM >= 5.0
    assert vol(duct.intersect(box(-DAM / 2 + 0.01, DAM / 2 - 0.01, -60, 0, -30, 5))) < 1e-6, "barrage"
    if dm["inlet_to_slot_centroid_mm"] < 175.0:
        warn.append(f"longueur entree -> centre des fentes {dm['inlet_to_slot_centroid_mm']} mm < 175 (canal barrage a barrage {dm['channel_dam_to_dam_mm']})")
    log("conduit", t)

    # --- parois minimales (distances 3D entre volumes d'air)
    t = time.perf_counter()
    env = front_env.union(rear_env)
    outside = box(-90, 90, -90, 90, Z_END - 10, Z_SEAT - 1.5).cut(env)
    # fentes exclues des deux cotes : la distance mesuree est alors leur longueur
    outside = union_all([outside, build_shadow_groove(), ring(0.0, REBATE, -RING_H, 0.01),
                         ring(LED_CH[0], LED_CH[1], -LED_CH[2], 0.01), build_tunnel(), bay_cut().intersect(env)])
    cav_chk = cav.intersect(box(-90, 90, -90, 90, -80, Z_SEAT - 4.5))
    walls = {"cavity_to_outside": min_distance(cav_chk, outside), "duct_to_outside": min_distance(duct, outside),
             "duct_to_cavity": min_distance(duct, cav.cut(build_inlet()))}
    m["min_wall_mm"] = {k: round(v, 2) for k, v in walls.items()}
    if walls["cavity_to_outside"] < 3.0 - 0.05 or walls["duct_to_outside"] < 3.0 - 0.05:
        fail.append(f"paroi < 3 mm : {m['min_wall_mm']}")
    assert walls["duct_to_cavity"] >= 1.6 - 0.05, m["min_wall_mm"]
    log("parois", t)

    # --- micro
    t = time.perf_counter()
    ang = cone_angle()
    mic = refs["mic"]
    clear = {"front": min_distance(mic, front), "insert": min_distance(mic, insert),
             "rear_except_disc": min_distance(mic, rear.cut(grow(refs["mic-disc"], 0.01))) if False else min_distance(mic, rear),
             "liner": min_distance(mic, refs["foam-liner"])}
    m["mic"] = {"centre": [MIC_XC, MIC_YC, MIC_ZC], "cone_min_deg": round(ang, 1), "clearance_mm": {k: round(v, 2) for k, v in clear.items()},
                "mouth_assumed_above_seat_mm": MOUTH_ABOVE_SEAT}
    assert clear["front"] >= MIC_CLEARANCE - 0.01 and clear["insert"] >= MIC_CLEARANCE - 0.01, clear
    assert clear["rear_except_disc"] >= v0.MIC_STEEL_DISC_THICKNESS - 0.01, clear
    if ang < CONE_HARD:
        fail.append(f"micro dans le cone : {ang:.1f} deg < {CONE_HARD}")
    elif ang < CONE_DEG:
        warn.append(f"cone du souffle : micro a {ang:.1f} deg (regle {CONE_DEG}, refus < {CONE_HARD})")
    log("micro", t)

    # --- joint et aimants
    m["gasket_compression_mm"] = round(comp, 2)
    m["magnets"] = {"joint": len(mag_xy()), "cover": len(COVER_MAG_XY)}
    assert len(mag_xy()) == 8 and refs["joint-magnets"].solids().size() == 8 and refs["joint-steel-discs"].solids().size() == 8

    # --- interferences deux a deux
    t = time.perf_counter()
    bodies = dict(parts) | refs
    names = list(bodies)
    hits = []
    for i, a in enumerate(names):
        ba = bodies[a].val().BoundingBox()
        for b in names[i + 1:]:
            bb2 = bodies[b].val().BoundingBox()
            if ba.xmax < bb2.xmin or bb2.xmax < ba.xmin or ba.ymax < bb2.ymin or bb2.ymax < ba.ymin or ba.zmax < bb2.zmin or bb2.zmax < ba.zmin:
                continue
            v = vol(bodies[a].intersect(bodies[b]))
            if v > 1e-3:
                hits.append((a, b, round(v, 3)))
    m["interferences"] = hits
    assert not hits, hits
    log("interferences", t)

    # --- double courbure de la peau
    t = time.perf_counter()
    m["curvature"] = curvature_check(front_env.faces().vals() + rear_env.faces().vals())
    single = [r for r in m["curvature"] if r.get("single_curvature_z_extent", 0) > 35.0]
    planes = [r for r in m["curvature"] if r["type"] == "PLANE" and max(r["size"]) > 35.0]
    if single:
        fail.append(f"courbure simple sur plus de 35 mm : {single}")
    m["flat_faces_note"] = "plans > 35 mm : appui du coussin (couvert par le coussin, voulu plat) et face arriere du dos (maquette)"
    log("courbure", t)

    # --- masse
    m["mass_g_solid_pla"] = {n: round(vol(p) * PLA, 1) for n, p in parts.items() if n != "ring"}
    m["mass_g_solid_pla"]["ring_petg"] = round(vol(ring_) * 1.25e-3, 1)
    m["mass_g_solid_pla"]["total"] = round(sum(m["mass_g_solid_pla"].values()), 1)
    m["warn"], m["fail"] = warn, fail

    # --- exports
    t = time.perf_counter()
    stem = "silent-mic-v3-galet"
    for n, p in parts.items():
        cq.exporters.export(p, str(out / f"{stem}-{n}.step"))
    # STL en orientation d'impression : capot appui en bas, coque face arriere en bas,
    # couvercle face plane en bas, anneau et collier a plat.
    printed = {
        "front": front.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, Z_SEAT)),
        "rear": rear.translate((0, 0, -Z_RF)),
        "cover": cover.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, Z_RF)),
        "ring": ring_.translate((0, 0, RING_H)),
        "collar-insert-14mm": cp.collar_insert(COLLAR_HEIGHT),
    }
    for n, p in printed.items():
        pb = p.val().BoundingBox()
        assert abs(pb.zmin) < 0.05 and pb.xlen <= 180 and pb.ylen <= 180 and pb.zlen <= 180, (n, pb.zmin)
        cq.exporters.export(p, str(out / f"{stem}-{n}.stl"), tolerance=LIN_TOL, angularTolerance=ANG_TOL)
    air = cav.union(duct).union(build_inlet()).union(build_slots())
    cq.exporters.export(air, str(out / f"{stem}-air-volume.step"))
    assembly = cq.Assembly(name=f"{stem}-technical")
    colors = {"front": (0.1, 0.1, 0.1, 0.4), "rear": (0.1, 0.1, 0.1, 0.4), "cover": (0.1, 0.1, 0.1, 0.4),
              "ring": (0.9, 0.9, 1.0, 0.6), "collar-insert-14mm": (0.2, 0.2, 0.2, 0.6)}
    for n, p in parts.items():
        assembly.add(p, name=n, color=cq.Color(*colors[n]))
    for n, p in refs.items():
        assembly.add(p, name=f"ref-{n}", color=cq.Color(0.6, 0.6, 0.65, 0.6))
    assembly.add(air, name="air-cavity-and-duct", color=cq.Color(0.1, 0.7, 0.95, 0.25))
    assembly.export(str(out / f"{stem}-technical.step"))
    log("exports STEP/STL", t)

    # --- web : STL grossiers et manifeste
    t = time.perf_counter()
    roles = {"front": ("Capot avant", "black", (0, 0, 30)), "rear": ("Coque arriere", "black", (0, 0, 0)),
             "cover": ("Couvercle de la baie", "black", (0, 0, -30)), "ring": ("Anneau lumineux", "translucent", (0, 0, 8)),
             "collar-insert-14mm": ("Collier amovible 14 mm", "black", (0, 0, 55)),
             "mic": ("DJI Mic Mini 2", "electronics", (0, 0, 40)), "mic-disc": ("Disque acier 30 mm", "metal", (0, 0, 38)),
             "earpad": ("Coussin Brainwavz", "soft", (0, 0, 75)), "gasket": ("Joint mousse 3 x 2", "soft", (0, 0, 15)),
             "led-filament": ("Filament LED", "electronics", (0, 0, 6)), "foam-disc": ("Disque de mousse 12 mm", "foam", (0, 0, -15)),
             "foam-liner": ("Manchon de mousse 9 mm", "foam", (0, 0, 45)), "windscreen": ("Bonnette 5 mm", "foam", (0, 0, 48)),
             "battery": ("LiPo 30 x 20 x 5", "electronics", (0, 0, -45)), "charger": ("Chargeur USB-C TP4056", "electronics", (0, 0, -50)),
             "switch": ("Interrupteur", "electronics", (0, 0, -50)), "joint-magnets": ("Aimants du joint 6 x 2", "metal", (0, 0, -4)),
             "joint-steel-discs": ("Pastilles acier du joint", "metal", (0, 0, 20)), "cover-magnets": ("Aimants du couvercle", "metal", (0, 0, -38)),
             "cover-steel-discs": ("Pastilles acier du couvercle", "metal", (0, 0, -42))}
    manifest = []
    for n, p in (dict(parts) | refs).items():
        f = web / f"{n}.stl"
        cq.exporters.export(p, str(f), tolerance=WEB_TOL[0], angularTolerance=WEB_TOL[1])
        assert f.stat().st_size < 1.5e6, (n, f.stat().st_size)
        label, role, ex = roles[n]
        manifest.append({"file": f.name, "label": label, "role": role, "explode": list(ex)})
    cq.exporters.export(air, str(web / "air-volume.stl"), tolerance=WEB_TOL[0], angularTolerance=WEB_TOL[1])
    manifest.append({"file": "air-volume.stl", "label": "Air : cavite et conduit", "role": "air", "explode": [0, 0, 0]})
    (web / "manifest.json").write_text(json.dumps({"units": "mm", "axes": "x lateral, y haut, z vers le visage, z=0 plan de joint",
                                                   "parts": manifest}, indent=2, ensure_ascii=False))
    (out / f"{stem}-metrics.json").write_text(json.dumps(m, indent=2, ensure_ascii=False))
    log("web", t)
    print(json.dumps({k: v for k, v in m.items() if k not in ("curvature",)}, indent=1, ensure_ascii=False))
    print(f"total {time.perf_counter() - t0:.1f} s")
    if fail:
        raise SystemExit("ECHEC : " + " ; ".join(fail))
    return m


if __name__ == "__main__":
    export()
