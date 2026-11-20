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
CORBEL = 9.5  # chanfrein sous le conduit (arriere) : 7.5 mm sur 9.5, 38 deg ; 45 deg pile est refuse par Orca
CORBEL_FRONT = 8.0  # sous la bride du capot : 43 deg, compromis avec l'angle du micro
MAG_T_DEG = (0, 36, 72, 108, 144, 180, 225, 315)  # angles parametriques ; rien en bas (micro, pied, barrage)

# ---------- coussin et collier amovible ----------
PAD = cp.PAD
COLLAR_HEIGHT = 14.0
COLLAR_INNER = cp.collar_inner()
LEDGE = 1.5  # appui de la bride du collier (seul porte-a-faux au-dessus du plateau)
SEAT_OPENING = tuple(f - 2 * LEDGE for f in cp.flange_outer())
OPENING_CHAMFER = (2.5, 1.0)  # largeur, hauteur : sous le bord de l'ouverture, face au plateau en impression (pente libre)

# ---------- conduit annulaire ----------
DUCT = (4.6, 9.1)  # offsets radiaux : 4.5 mm
DUCT_H = 12.13  # 9.2 de flanc droit + toit en pointe 2.9 (faite vif) : 48 mm2, imprimable sans support
DUCT_TOP = -5.2  # 3 mm sous la rainure LED (exterieur)
DUCT_BOTTOM = DUCT_TOP - DUCT_H
DUCT_APEX = 0.0  # faite vif : un plat, meme de 0.3 mm, est un plafond qu'Orca supporte
STEEP = 1.3  # pente des surplombs internes : 1.3 en hauteur pour 1 en largeur (38 deg)
DUCT_ROOF_H = STEEP * ((DUCT[1] - DUCT[0]) - DUCT_APEX) / 2
DAM = 9.0  # barrage a 6 h, porte aussi le tunnel des fils
INLET_D = 8.0  # largeur de l'entree (voir INLET_W)
INLET_Z = DUCT_BOTTOM + 4.5  # repere de hauteur de l'entree (debut du controle de passage)
SHADOW_DEPTH = 1.5
SHADOW_Z = (-RING_H - 1.2 - 5.0, -RING_H - 1.2)  # 5 mm visibles, 1.2 mm derriere l'anneau
SHADOW_FLOOR_TOP = SHADOW_Z[1] - 1.3 * 1.5  # fond vertical, puis flanc haut a 38 deg
SLOT_LEN, SLOT_GAP, SLOT_COUNT = 10.5, 2.0, 4
SLOT_STEEP = 2.5  # fentes a 22 deg de la verticale : a 38 et 32 deg Orca les supportait encore
SLOT_WINDOW = (SHADOW_Z[0] + 0.3, SHADOW_FLOOR_TOP - 0.3)  # fenetres dans le fond vertical seulement
CORBEL_TOP = DUCT_BOTTOM - 1.6  # plancher du conduit garde 1.6 mm
CORBEL_BOTTOM = CORBEL_TOP - CORBEL

# ---------- arriere, baie, couvercle ----------
BAY_DEPTH = 10.5
FLOOR_TOP = Z_RF + BAY_DEPTH + WALL
FLOOR_RIB = 1.5
FOAM_DISC_T = 20.0
LINER_T = 10.0
REAR_LINER_T = 8.0
MIN_PASSAGE = 1200.0  # section d'air libre le long de l'axe, de l'entree au coussin
TUNNEL_D = 2.6
TUNNEL_OFFSET = 3.8
COVER_MAG_XY = ((-21.5, 9.0), (21.5, 9.0), (-21.5, -9.0), (21.5, -9.0))
COVER_MAG_PROTRUDE = 0.9
LIPO = (30.0, 20.0, 5.0)
CHARGER = (17.5, 28.0, 4.0)  # x, y, z ; USB-C vers le bas
SWITCH = (8.6, 3.6, 3.5)

# ---------- micro : a plat sur un pied de la coque arriere, grille vers la cavite ----------
# Position issue de la recherche du cone (cad/silent_mic_v3_galet.py ne la recalcule pas).
MIC_PRESETS = {"evase": (0.25, -12.25, 20.0), "oeuf": (-2.5, -21.0, 20.2)}
MIC_XC, MIC_YC, MIC_ZC = MIC_PRESETS[PROFILE]
MIC_CLEARANCE = 1.0
WINDSCREEN_T = 5.0
WINDSCREEN_GAP = 0.5  # la bonnette, collee au manchon, effleure la grille quand le capot est ferme
STEM_R = 4.0
# Nid du micro : 4 butees basses, une par face, sur la tete du pied. Le micro se pose et se retire
# en translation selon +z ; au-dessus des butees, ses 4 faces restent libres pour les doigts.
NEST_GAP, NEST_H, NEST_T = 0.45, 4.0, 1.2
NEST_STEEP = 2.5  # dessous des butees a 22 deg : a 38 deg Orca supporte encore ces petits porte-a-faux
NEST_STOP = 1.8  # longueur de chaque butee, de part et d'autre du milieu de la face
MIC_STACK_EXTRA = float(os.environ.get("SILENT_MIC_STACK_EXTRA", 0.0))  # clip ou aimant sous le boitier, a mesurer
FINGER = 15.0  # largeur de doigt controlee de chaque cote du micro, capot avant retire
CONE_DEG, CONE_HARD = 15.0, 12.0  # 15 = regle (WARN en dessous), 12 = refus
MOUTH_ABOVE_SEAT = 20.0  # coussin de 30 mm comprime : hypothese
BREATH_Y = 10.0
PLA = 1.24e-3
LIN_TOL, ANG_TOL = 0.02, 0.1  # a 0.1 / 0.3 rad, OCCT maillait la coque arriere 6 % trop petite
WEB_TOL = (0.4, 0.6)
WEB_TOL_FINE = (0.06, 0.15)  # pieces imprimees : le pavillon ne doit pas paraitre a facettes


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
    z_main = FLANGE_TOP + CORBEL_FRONT
    joint = band(CAV_JOINT, -0.5, FLANGE_TOP)
    a, b = outer_profile(s_of(z_main))
    k = inset(s_of(z_main), WALL)
    corbel = wp(cq.Solid.makeLoft([sec_wire(FLANGE_TOP, CAV_JOINT), sec_wire(z_main, k)], True))
    zs = [s for s in FRONT_SMOOTH + (54.0,) if z_main < z_of(s) < Z_SEAT - SEAT_PLATE]
    main = loft_ellipses(sections([s_of(z_main)] + sorted(zs, reverse=True) + [s_of(Z_SEAT - SEAT_PLATE)], WALL))
    # siege conique a 38 deg de la bride biseautee du collier (pas de logement plat : capot imprime appui en bas)
    top = tuple(f + 2 * cp.FLANGE_GAP for f in cp.flange_outer())
    z_low = Z_SEAT - STEEP * (top[0] - SEAT_OPENING[0]) / 2
    opening = eprism(*SEAT_OPENING, Z_SEAT - SEAT_PLATE - 1.0, z_low)
    cone_ = wp(cq.Solid.makeLoft([ell(*SEAT_OPENING, z_low), ell(*top, Z_SEAT), ell(top[0] + 0.02, top[1] + 0.02, Z_SEAT + 1)], True))
    # chanfrein sous le bord de l'ouverture : le coin haut du micro voyait l'arete de la plaque a 1.25 mm
    zp = Z_SEAT - SEAT_PLATE
    cw, ch = OPENING_CHAMFER
    chamfer = wp(cq.Solid.makeLoft([ell(SEAT_OPENING[0] + 2 * cw, SEAT_OPENING[1] + 2 * cw, zp - 0.01),
                                    ell(*SEAT_OPENING, zp + ch)], True))
    return joint.union(corbel).union(main).union(opening).union(cone_).union(chamfer)


def section_point(t, d, z):
    """Point a l'offset d de la section locale a z, angle parametrique t."""
    a, b = outer_profile(s_of(z))
    n = (b * math.cos(t), a * math.sin(t))
    k = math.hypot(*n)
    return a * math.cos(t) - d * n[0] / k, b * math.sin(t) - d * n[1] / k


def build_front_bosses():
    """Bossages des aimants sous le joint, prolonges par un contrefort a 38 deg qui
    rentre dans la paroi : aucune pointe pendante quand le capot est imprime appui en bas."""
    h = MAG_POCKET[1] + 1.2
    r_end, d_end = 0.8, 1.5
    z_end = h + STEEP * ((MAG_OFFSET + BOSS_R) - (d_end + r_end))
    out = []
    for t in MAG_T_DEG:
        x, y = eq_point(math.radians(t), MAG_OFFSET)[0]
        xe, ye = section_point(math.radians(t), d_end, z_end)
        cyl = cq.Workplane("XY", origin=(x, y, 0)).circle(BOSS_R).extrude(h)
        but = wp(cq.Solid.makeLoft([cq.Workplane("XY", origin=(x, y, h)).circle(BOSS_R).wire().val(),
                                    cq.Workplane("XY", origin=(xe, ye, z_end)).circle(r_end).wire().val()], True))
        out.append(cyl.union(but))
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

def loft_wires(pairs):
    """Loft regle a plusieurs sections (z, offset) : flanc et toit d'une seule surface, sans
    face de jonction (une jonction coplanaire donnait des faces degenerees et un STL troue)."""
    return wp(cq.Solid.makeLoft([sec_wire(z, d) for z, d in pairs], True))


def build_duct():
    z_flat = DUCT_TOP - DUCT_ROOF_H
    mid, ext = sum(DUCT) / 2, 0.3
    z_ext = DUCT_TOP + STEEP * ext
    # les deux pans sont prolonges au-dela du faite : leur intersection donne une arete vive
    outer = loft_wires([(DUCT_BOTTOM, DUCT[0]), (z_flat, DUCT[0]), (z_ext, mid + ext)])
    inner = loft_wires([(DUCT_BOTTOM - 1.0, DUCT[1]), (z_flat, DUCT[1]), (z_ext, mid - ext)])
    return outer.cut(inner).cut(box(-DAM / 2, DAM / 2, -60, -10, DUCT_BOTTOM - 2, 2))


INLET_S = DAM / 2 + 1.0 + INLET_D / 2  # cote x > 0 du barrage
SLOT_S = [-(DAM / 2 + 1.0 + SLOT_LEN / 2 + i * (SLOT_LEN + SLOT_GAP)) for i in range(SLOT_COUNT)]


INLET_W, INLET_RECT = 8.0, 3.5
INLET_BOTTOM = DUCT_BOTTOM + 0.33
INLET_AREA = INLET_W * INLET_RECT + INLET_W * STEEP * INLET_W / 4


def build_inlet():
    """Entree en pentagone : flancs verticaux, toit a 38 deg dont le faite reste sous le toit
    interieur du conduit (sinon poche dans le toit, qu'Orca supporte)."""
    zb, zr = INLET_BOTTOM, INLET_BOTTOM + INLET_RECT
    port = (cq.Workplane("XZ", origin=(0, DUCT[1] - 0.6, 0))
            .polyline([(-INLET_W / 2, zb), (INLET_W / 2, zb), (INLET_W / 2, zr), (0, zr + STEEP * INLET_W / 2), (-INLET_W / 2, zr)])
            .close().extrude(-(CAV_JOINT - DUCT[1] + 1.2)))
    return place(port, t_at(CENTER_TABLE, INLET_S))


def build_slots():
    r0, r1 = SHADOW_DEPTH - 0.05, DUCT[0] + 0.6  # debouche dans le fond vertical, pas dans le flanc
    lo = lambda r: SLOT_WINDOW[0] - SLOT_STEEP * (r - SHADOW_DEPTH)
    h = SLOT_WINDOW[1] - SLOT_WINDOW[0]
    out = []
    for s in SLOT_S:
        prof = (cq.Workplane("YZ", origin=(-SLOT_LEN / 2, 0, 0))
                .polyline([(r0, lo(r0)), (r1, lo(r1)), (r1, lo(r1) + h), (r0, lo(r0) + h)]).close().extrude(SLOT_LEN))
        out.append(place(prof, t_at(CENTER_TABLE, s)))
    return union_all(out)


def build_shadow_groove():
    """Gorge d'ombre : fond vertical puis flanc haut a 38 deg (la coque s'imprime face arriere
    en bas ; un rebord plat serait un surplomb sur la peau visible)."""
    z_ch, z_top = SHADOW_FLOOR_TOP, SHADOW_Z[1] + 0.3
    skin = loft_wires([(SHADOW_Z[0], -1.0), (z_top, -1.0)])
    keep = loft_wires([(SHADOW_Z[0] - 1.0, SHADOW_DEPTH), (z_ch, SHADOW_DEPTH), (z_top, -0.3), (z_top + 1.0, -1.1)])
    return skin.cut(keep.intersect(box(-70, 70, -70, 70, SHADOW_Z[0] - 1.0, z_top))).intersect(box(-60, 60, -60, 0, -30, 5))


# ================= joint, aimants, tunnel =================

def mag_xy():
    return [eq_point(math.radians(t), MAG_OFFSET)[0] for t in MAG_T_DEG]


def mag_pockets_up(z0, depth, dia=MAG_POCKET[0]):
    return union_all(cq.Workplane("XY", origin=(x, y, z0)).circle(dia / 2).extrude(depth) for x, y in mag_xy())


def build_rear_bosses():
    """Bossages des aimants, prolonges par un contrefort a 38 deg qui finit dans la paroi
    interieure du conduit (coque imprimee z vers le haut : pas de pointe pendante)."""
    h = MAG_POCKET[1] + 1.2
    r_end, d_end = 0.8, 10.0
    out = []
    for t in MAG_T_DEG:
        x, y = eq_point(math.radians(t), MAG_OFFSET)[0]
        z_end = -h - STEEP * ((MAG_OFFSET + BOSS_R) - (d_end + r_end))
        xe, ye = section_point(math.radians(t), d_end, z_end)
        cyl = cq.Workplane("XY", origin=(x, y, -h)).circle(BOSS_R).extrude(h)
        but = wp(cq.Solid.makeLoft([cq.Workplane("XY", origin=(xe, ye, z_end)).circle(r_end).wire().val(),
                                    cq.Workplane("XY", origin=(x, y, -h)).circle(BOSS_R).wire().val()], True))
        out.append(cyl.union(but))
    return union_all(out)


def tunnel_points():
    y_top = -EJ[1] + TUNNEL_OFFSET
    zb = DUCT_BOTTOM - 0.5
    y_mid = -outer_profile(s_of(zb))[1] + TUNNEL_OFFSET
    y_bot = -outer_profile(s_of(Z_RF + BAY_DEPTH))[1] + TUNNEL_OFFSET + 2.5
    return (0, y_top, 0.5), (0, y_mid, zb), (0, y_bot, Z_RF + BAY_DEPTH - 2.0)


def build_tunnel():
    a, b, c = tunnel_points()
    # sans sphere au coude : son dome serait un plafond ; le troncon vertical deborde de 1.5 mm
    return cyl_between(a, (b[0], b[1], b[2] - 1.5), TUNNEL_D / 2).union(cyl_between(b, c, TUNNEL_D / 2))


def build_tunnel_rib():
    _, b, c = tunnel_points()
    r = TUNNEL_D / 2 + WALL
    return cyl_between(b, c, r).union(wp(cq.Solid.makeSphere(r, cq.Vector(*b))))


# ================= coque arriere (imprimee face arriere sur le plateau) =================

def rear_cavity_tool():
    a, b = outer_profile(s_of(CORBEL_BOTTOM))
    k = inset(s_of(CORBEL_BOTTOM), WALL)
    lower = loft_ellipses(sections([s_of(FLOOR_TOP), s_of((FLOOR_TOP + CORBEL_BOTTOM) / 2), s_of(CORBEL_BOTTOM)], WALL))
    corbel = wp(cq.Solid.makeLoft([sec_wire(CORBEL_BOTTOM, k), sec_wire(CORBEL_TOP, CAV_JOINT)], True))
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
    # un seul plafond de baie (pont unique) : chaque logement monte jusqu'au plafond
    full = lambda b: box(*(lambda q: (q.xmin - 0.5, q.xmax + 0.5, q.ymin - 0.5, q.ymax + 0.5, Z_RF - 1, Z_RF + BAY_DEPTH))(b.val().BoundingBox()))
    bay = union_all([full(lipo), full(charger), full(switch)])
    bay = bay.union(box(-CHARGER[0] / 2 - 0.5, CHARGER[0] / 2 + 0.5, -40, 0, Z_RF - 1, Z_RF + 0.4))
    cb = charger.val().BoundingBox()
    usb = cq.Workplane("XZ", origin=(0, cb.ymin + 2, Z_RF + 2.6)).slot2D(12.0, 6.0).extrude(20)
    roof = cq.Workplane("XZ", origin=(0, cb.ymin + 2, 0)).polyline([(-3.0, Z_RF + 5.6), (3.0, Z_RF + 5.6), (0.0, Z_RF + 5.6 + 3.0 * STEEP)]).close().extrude(20)
    usb = usb.union(roof)
    sb = switch.val().BoundingBox()
    lever = box(15.3 - 2.0, 15.3 + 2.0, -45, sb.ymin + 0.1, Z_RF + 1.2, Z_RF + 3.4)
    return bay.union(usb).union(lever)


def cover_pockets(z0, depth, roof=0):
    """Poches des aimants du couvercle ; roof = +1 ou -1 ajoute un toit conique a 45 deg
    au fond (cote +z ou -z) pour une poche ouverte vers le plateau."""
    r = MAG_POCKET[0] / 2 + 0.05
    out = []
    for x, y in COVER_MAG_XY:
        p = cq.Workplane("XY", origin=(x, y, z0)).circle(r).extrude(depth)
        if roof:
            base = z0 + depth if roof > 0 else z0
            p = p.union(wp(cq.Solid.makeCone(r, 0.0, r, cq.Vector(x, y, base), cq.Vector(0, 0, roof))))
        out.append(p)
    return union_all(out)


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
    shell = shell.cut(bay_cut()).cut(cover_pockets(Z_RF - 0.5, 0.5 + MAGNET[1] - COVER_MAG_PROTRUDE + 0.1, roof=1))
    log("coque arriere", t)
    return shell


def build_cover(rear_env):
    t = time.perf_counter()
    cover = rear_env.intersect(box(-70, 70, -70, 70, Z_END - 1, Z_RF))
    try:
        cover = cover.faces("<Z").edges().fillet(REAR_FILLET)
    except Exception as exc:  # shortcut: sans conge si OCCT refuse ; a reprendre a la main
        print(f"conge du dos refuse : {exc}")
    cover = cover.cut(cover_pockets(Z_RF - 3.1, 3.2, roof=-1))
    log("couvercle", t)
    return cover


def build_ring():
    return ring(0.0, cp.RING_DEPTH, -RING_H, 0.0)


def collar_insert_placed():
    # la bride biseautee touche le cone quand son bord haut (flange_outer) rencontre le cone
    return cp.collar_insert(COLLAR_HEIGHT).translate((0, 0, Z_SEAT - STEEP * cp.FLANGE_GAP - cp.FLANGE_T + 0.05))


# ================= corps de reference =================

MIC_DISC_TOP = MIC_ZC - v0.MIC_SIZE[2] / 2 - v0.MIC_STEEL_DISC_THICKNESS


MIC_BOTTOM = MIC_DISC_TOP + v0.MIC_STEEL_DISC_THICKNESS


def mic_box(extra=None):
    """Boitier DJI (cotes de la fiche officielle) pose sur le disque ; extra = epaisseur d'un clip
    ou d'un aimant entre disque et boitier, qui souleve le micro."""
    e = MIC_STACK_EXTRA if extra is None else extra
    return box(MIC_XC - v0.MIC_SIZE[0] / 2, MIC_XC + v0.MIC_SIZE[0] / 2, MIC_YC - v0.MIC_SIZE[1] / 2,
               MIC_YC + v0.MIC_SIZE[1] / 2, MIC_BOTTOM + e, MIC_BOTTOM + e + v0.MIC_SIZE[2])


def build_mic_nest():
    """8 butees de 4 mm, deux par face, a 0.45 mm du boitier : position et orientation indexees,
    pose et retrait en translation pure. Elles evitent le milieu des faces, ou le disque de 30 mm
    deborde du boitier. Chaque butee est un seul profil : dessous a 38 deg ancre dans le flanc de la
    tete du pied a 22 deg (coque imprimee z vers le haut), partie interieure sous le niveau du micro."""
    r_head = v0.MIC_STEEL_DISC_DIAMETER / 2 + 0.5
    r_disc = v0.MIC_STEEL_DISC_DIAMETER / 2 + 0.2
    zs = MIC_DISC_TOP - 1.5 + 0.06  # bas du flanc vertical de la tete
    z1 = MIC_BOTTOM + NEST_H
    zin = MIC_BOTTOM - NEST_GAP  # dessus de la partie interieure, sous le boitier
    out = []
    for axis, half in (("x", v0.MIC_SIZE[0] / 2 + NEST_GAP), ("y", v0.MIC_SIZE[1] / 2 + NEST_GAP)):
        u0, u1 = half, half + NEST_T
        t0 = math.sqrt(r_disc ** 2 - u0 ** 2) + 0.1
        t1 = t0 + NEST_STOP
        ui = math.sqrt(r_head ** 2 - t1 ** 2) - 0.05  # sur le flanc vertical de la tete, meme a l'extremite
        assert zs + NEST_STEEP * (u0 - ui) <= zin - 0.02, "profil de butee qui se recoupe"
        prof = [(ui, zs), (u1, zs + NEST_STEEP * (u1 - ui)), (u1, z1), (u0, z1), (u0, zin), (ui, zin)]
        for sgn in (-1, 1):
            for tsg in (-1, 1):
                a, b = sorted((tsg * t0, tsg * t1))
                if axis == "x":
                    solid = (cq.Workplane("XZ", origin=(0, MIC_YC + b, 0))
                             .polyline([(MIC_XC + sgn * u, z) for u, z in prof]).close().extrude(b - a))
                else:
                    solid = (cq.Workplane("YZ", origin=(MIC_XC + a, 0, 0))
                             .polyline([(MIC_YC + sgn * u, z) for u, z in prof]).close().extrude(b - a))
                out.append(solid)
    return union_all(out)


def mic_disc():
    return wp(cq.Solid.makeCylinder(v0.MIC_STEEL_DISC_DIAMETER / 2, v0.MIC_STEEL_DISC_THICKNESS,
                                    cq.Vector(MIC_XC, MIC_YC, MIC_DISC_TOP), cq.Vector(0, 0, 1)))


def build_mic_pedestal():
    """Pied en champignon a 45 deg, issu de la paroi du barrage a 6 h ; il traverse le plan
    de joint dans la cavite. Imprime avec la coque (z vers le haut) sans support."""
    r_top = v0.MIC_STEEL_DISC_DIAMETER / 2 + 0.5
    z_top = MIC_DISC_TOP
    z_neck = z_top - STEEP * (r_top - STEM_R) - 1.5
    z_base = DUCT_BOTTOM + 4.0
    c = cq.Vector(MIC_XC, MIC_YC, 0)
    head = wp(cq.Solid.makeCone(STEM_R, r_top, STEEP * (r_top - STEM_R), c + cq.Vector(0, 0, z_neck), cq.Vector(0, 0, 1)))
    head = head.union(wp(cq.Solid.makeCylinder(r_top, 1.5, c + cq.Vector(0, 0, z_top - 1.5), cq.Vector(0, 0, 1))))
    stem = wp(cq.Solid.makeCylinder(STEM_R, z_neck - z_base + 0.01, c + cq.Vector(0, 0, z_base), cq.Vector(0, 0, 1)))
    foot = wp(cq.Solid.makeCone(0.01, STEM_R, STEEP * STEM_R, c + cq.Vector(0, 0, z_base - STEEP * STEM_R), cq.Vector(0, 0, 1)))
    y_wall = -outer_profile(s_of(0))[1] + CAV_JOINT - 1.0
    web = (cq.Workplane("YZ", origin=(MIC_XC - 2.0, 0, 0))
           .polyline([(y_wall, z_base - STEEP * (STEM_R + MIC_YC - y_wall)), (MIC_YC, z_base - STEEP * STEM_R), (MIC_YC, -0.5),
                      (y_wall, -0.5)]).close().extrude(4.0))
    return union_all([head, stem, foot, web, build_mic_nest()])


def build_windscreen():
    """Bonnette de 5 mm au-dessus de la grille, collee au manchon du capot avant (elle part avec
    lui) ; retaillee ensuite contre le capot et le col."""
    bb = mic_box().val().BoundingBox()
    z0 = bb.zmax + WINDSCREEN_GAP
    # empreinte micro + 2 mm : elle rejoint le bord de la decoupe du manchon, ou elle est collee
    return box(bb.xmin - 2, bb.xmax + 2, bb.ymin - 2, bb.ymax + 2, z0, z0 + WINDSCREEN_T)


def windscreen_room(steps=25):
    """Epaisseur de mousse disponible au-dessus de la grille (sans contact avec une piece rigide),
    en grille sur l'empreinte du micro : sous la plaque d'appui, sous la bride du col, sous l'ouverture du col."""
    bb = mic_box().val().BoundingBox()
    z0 = bb.zmax + WINDSCREEN_GAP
    inside = lambda x, y, w, h: (x / (w / 2)) ** 2 + (y / (h / 2)) ** 2 <= 1
    zones = {"sous_plaque": [], "sous_bride_du_col": [], "sous_ouverture_du_col": []}
    for i in range(steps + 1):
        for j in range(steps + 1):
            x = bb.xmin + (bb.xmax - bb.xmin) * i / steps
            y = bb.ymin + (bb.ymax - bb.ymin) * j / steps
            if not inside(x, y, *SEAT_OPENING):
                zones["sous_plaque"].append(Z_SEAT - SEAT_PLATE - z0)
            elif not inside(x, y, *COLLAR_INNER):
                zones["sous_bride_du_col"].append(Z_SEAT - cp.FLANGE_T - 0.1 - z0)
            else:
                zones["sous_ouverture_du_col"].append(WINDSCREEN_T)
    n = sum(len(v) for v in zones.values())
    return {k: {"part_de_la_face_pct": round(100 * len(v) / n), "epaisseur_mm": round(min(min(v), WINDSCREEN_T), 2)}
            for k, v in zones.items() if v}


def build_liner():
    """Manchon de mousse 9 mm sur les flancs de la chambre avant, piege entre la plaque
    d'appui et le chanfrein du joint ; decoupe devant le micro et l'ouverture."""
    z0, z1 = FLANGE_TOP + CORBEL_FRONT + 0.3, Z_SEAT - SEAT_PLATE - 0.3
    zs = [s_of(z0)] + [s for s in FRONT_SMOOTH if z0 < z_of(s) < z1] + [s_of(z1)]
    outer = loft_ellipses(sections(sorted(zs, reverse=True), WALL + 0.2))
    inner = loft_ellipses(sections(sorted(zs, reverse=True), WALL + 0.2 + LINER_T))
    liner = outer.cut(inner).cut(eprism(*SEAT_OPENING, z0 - 1, z1 + 1))
    # couche de 5 mm sur le chanfrein du joint, sous le manchon (section encore large a cet endroit)
    zl, zm, t = FLANGE_TOP + 0.2, FLANGE_TOP + CORBEL_FRONT + 0.3, 5.5
    k = inset(s_of(FLANGE_TOP + CORBEL_FRONT), WALL)
    a_ = wp(cq.Solid.makeLoft([sec_wire(FLANGE_TOP, CAV_JOINT + 0.2), sec_wire(FLANGE_TOP + CORBEL_FRONT, k + 0.2)], True))
    b_ = wp(cq.Solid.makeLoft([sec_wire(FLANGE_TOP, CAV_JOINT + 0.2 + t), sec_wire(FLANGE_TOP + CORBEL_FRONT, k + 0.2 + t)], True))
    liner = liner.union(a_.cut(b_).intersect(box(-70, 70, -70, 70, zl, zm)))
    return liner.cut(grow(mic_box(), 2.0)).cut(build_front_bosses()).cut(grow(build_mic_pedestal(), 1.0))


def inlet_notch():
    bb = build_inlet().val().BoundingBox()
    return box(bb.xmin - 3, bb.xmax + 3, -60, bb.ymax + 4, DUCT_BOTTOM - 2, 1)


def build_foam_disc(rear=None):
    """Disque de 20 mm qui epouse tout le fond de la cavite (retenu par le chanfrein sous le conduit),
    entaille devant l'entree du conduit, autour du pied du micro et du tunnel des fils."""
    z0 = FLOOR_TOP + FLOOR_RIB
    disc = rear_cavity_tool().intersect(box(-70, 70, -70, 70, z0, z0 + FOAM_DISC_T))
    if rear is not None:
        disc = disc.cut(rear)
    return disc.cut(build_tunnel_rib()).cut(grow(build_mic_pedestal(), 0.5)).cut(inlet_notch()).cut(
        box(-0.9, 0.9, -45, 45, z0 - 1, z0 + 0.2)).cut(box(-45, 45, -0.9, 0.9, z0 - 1, z0 + 0.2))


def build_rear_liner(rear=None):
    """Pieces de 8 mm sur les flancs de la bande du conduit, posees sur le disque et tenues
    sous les contreforts des aimants ; rien en bas (entree du conduit, pied du micro)."""
    z0, z1 = FLOOR_TOP + FLOOR_RIB + FOAM_DISC_T, -MAG_POCKET[1] - 1.2 - 0.3
    liner = ring(CAV_JOINT + 0.05, CAV_JOINT + REAR_LINER_T, z0, z1).intersect(box(-70, 70, -8.0, 70, z0, z1))
    liner = liner.cut(build_rear_bosses()).cut(grow(build_mic_pedestal(), 1.0)).cut(inlet_notch())
    return liner if rear is None else liner.cut(rear)


def build_refs():
    lipo, charger, switch = bay_boxes()
    pad = eprism(*PAD["outer"], Z_SEAT, Z_SEAT + PAD["thickness"]).cut(eprism(*PAD["opening"], Z_SEAT - 1, Z_SEAT + PAD["thickness"] + 1))
    cmag = union_all(cq.Workplane("XY", origin=(x, y, Z_RF - COVER_MAG_PROTRUDE)).circle(MAGNET[0] / 2).extrude(MAGNET[1]) for x, y in COVER_MAG_XY)
    csteel = union_all(cq.Workplane("XY", origin=(x, y, Z_RF - 3.1)).circle(MAGNET[0] / 2).extrude(MAGNET[1]) for x, y in COVER_MAG_XY)
    return {
        "mic": mic_box(), "mic-disc": mic_disc(), "earpad": pad,
        "gasket": ring(GROOVE[0] + 0.1, GROOVE[1] - 0.1, TONGUE[2], GROOVE_DEPTH),
        "led-filament": ring(LED_CH[0] + 0.2, LED_CH[1] - 0.2, -LED_CH[2] + 0.1, -0.1),
        "foam-disc": build_foam_disc(), "foam-liner": build_liner(), "foam-liner-rear": build_rear_liner(),
        "battery": lipo, "charger": charger, "switch": switch,
        "joint-magnets": mag_pockets_up(-MAGNET[1] - 0.1, MAGNET[1], MAGNET[0]),
        "joint-steel-discs": mag_pockets_up(0.1, MAGNET[1], MAGNET[0]),
        "cover-magnets": cmag, "cover-steel-discs": csteel,
    }


def web_earpad(levels=13, n=2.6):
    """Coussin arrondi pour la vue web : section en superellipse (20 mm de large, 30 de haut)
    balayee le long de l'ellipse moyenne du coussin. Le corps de reference CAO reste l'anneau plein."""
    cw, ch = (PAD["outer"][0] + PAD["opening"][0]) / 2, (PAD["outer"][1] + PAD["opening"][1]) / 2
    half = (PAD["outer"][0] - PAD["opening"][0]) / 4
    th = PAD["thickness"]
    outer_s, inner_s = [], []
    for i in range(levels):
        u = -1 + 2 * i / (levels - 1)
        w = max(half * (1 - abs(u) ** n) ** (1 / n), 0.6)
        z = Z_SEAT + th / 2 * (1 + u * 0.999)
        outer_s.append((cw + 2 * w, ch + 2 * w, z, 0.0))
        inner_s.append((cw - 2 * w, ch - 2 * w, z, 0.0))
    return loft_ellipses(outer_s).cut(loft_ellipses(inner_s))


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
            "inlet_area_mm2": round(INLET_AREA, 1),
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
    if hasattr(b, "solids") and b.solids().size() == 0:
        return float("inf")
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
    ws = build_windscreen().cut(grow(front.intersect(box(-70, 70, -70, 70, Z_SEAT - SEAT_PLATE - 0.01, Z_SEAT + 1)), 0.0)).cut(front).cut(insert)

    # au-dessus de l'appui, la bonnette ne reste que dans l'ouverture du col (pas dans le coussin)
    ws = ws.intersect(box(-70, 70, -70, 70, -60, Z_SEAT - 0.1).union(eprism(*COLLAR_INNER, Z_SEAT - 1, Z_SEAT + COLLAR_HEIGHT)))
    refs["windscreen"] = ws
    refs["foam-disc"] = build_foam_disc(rear)
    refs["foam-liner-rear"] = build_rear_liner(rear)
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
    foam = {k: vol(refs[k]) / 1000 for k in ("foam-disc", "foam-liner", "foam-liner-rear", "windscreen")}
    v_foam = sum(foam.values())
    m["cavity_air_plus_foam_cm3"] = round(v_cav, 1)
    m["cavity_air_only_cm3"] = round(v_cav - v_foam, 1)
    m["foam_cm3"] = {k: round(v, 1) for k, v in foam.items()} | {"total": round(v_foam, 1)}
    pad_zone = vol(eprism(*PAD["opening"], Z_SEAT, Z_SEAT + PAD["thickness"]).cut(insert)) / 1000
    m["pad_zone_above_collar_info_cm3"] = round(pad_zone - math.pi / 4 * COLLAR_INNER[0] * COLLAR_INNER[1] * COLLAR_HEIGHT / 1000, 1)
    assert v_cav >= 185.0, f"cavite {v_cav:.1f} cm3 < 185"
    assert cav.solids().size() >= 1
    # section d'air libre (sans mousse ni pieces) le long de l'axe, de l'entree du conduit au coussin
    air = cav.cut(union_all([refs[k] for k in ("foam-disc", "foam-liner", "foam-liner-rear", "windscreen")]))
    z, passage = disc_top() + 0.3, []  # au-dessus du disque ; l'entree reste ouverte par l'entaille du disque
    while z < Z_SEAT - 4.0:
        area_ = 0.0
        for dz in (0.0, 0.07, 0.13):  # une tranche qui frole une face plane peut faire echouer le booleen
            area_ = vol(air.intersect(box(-70, 70, -70, 70, z + dz, z + dz + 0.2))) / 0.2
            if area_ > 0:
                break
        passage.append((round(z, 1), round(area_)))
        z += 1.5
    zmin, amin = min(passage, key=lambda q: q[1])
    m["free_passage_min_mm2"] = {"area": amin, "z": zmin}
    assert amin >= MIN_PASSAGE, (amin, zmin)
    log("cavite et passage libre", t)

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
    # zone d'appui : les butees et le plateau de 1.5 mm de la tete qui porte le disque
    seat_disc = wp(cq.Solid.makeCylinder(v0.MIC_STEEL_DISC_DIAMETER / 2 + 0.6, 1.62,
                                         cq.Vector(MIC_XC, MIC_YC, MIC_DISC_TOP - 1.6), cq.Vector(0, 0, 1)))
    nest_zone = grow(build_mic_nest(), 0.01).union(seat_disc)
    clear = {"front": min_distance(mic, front), "insert": min_distance(mic, insert),
             "rear_hors_nid_et_disque": min_distance(mic, rear.cut(nest_zone)),
             "nid": min_distance(mic, build_mic_nest()), "disque": min_distance(mic, refs["mic-disc"]),
             "liner": min_distance(mic, refs["foam-liner"])}
    # surepaisseur admissible sous le boitier (clip, aimant) avant de passer sous 1.0 mm d'une piece imprimee
    lo, hi = 0.0, 6.0
    for _ in range(9):
        mid = (lo + hi) / 2
        mb = mic_box(MIC_STACK_EXTRA + mid)
        ok = min(min_distance(mb, front), min_distance(mb, insert), min_distance(mb, rear.cut(nest_zone))) >= MIC_CLEARANCE
        lo, hi = (mid, hi) if ok else (lo, mid)
    # doigts : de chaque cote, une bande de 15 mm au-dessus des butees jusqu'au haut du boitier, capot avant retire
    bbm = mic.val().BoundingBox()
    zf0 = MIC_BOTTOM + NEST_H
    sides = {"-x": box(bbm.xmin - FINGER, bbm.xmin - 0.01, bbm.ymin, bbm.ymax, zf0, bbm.zmax),
             "+x": box(bbm.xmax + 0.01, bbm.xmax + FINGER, bbm.ymin, bbm.ymax, zf0, bbm.zmax),
             "-y": box(bbm.xmin, bbm.xmax, bbm.ymin - FINGER, bbm.ymin - 0.01, zf0, bbm.zmax),
             "+y": box(bbm.xmin, bbm.xmax, bbm.ymax + 0.01, bbm.ymax + FINGER, zf0, bbm.zmax)}
    fingers = {k: {"hauteur_libre_mm": round(bbm.zmax - zf0, 1), "obstacle_mm3": round(vol(b.intersect(rear.union(ring_))), 1)}
               for k, b in sides.items()}
    m["mic"] = {"centre": [MIC_XC, MIC_YC, MIC_ZC], "cone_min_deg": round(ang, 1), "clearance_mm": {k: round(v, 2) for k, v in clear.items()},
                "mouth_assumed_above_seat_mm": MOUTH_ABOVE_SEAT, "stack_extra_mm": MIC_STACK_EXTRA,
                "stack_extra_max_mm": round(lo, 2), "nest": {"jeu_par_cote_mm": NEST_GAP, "hauteur_butees_mm": NEST_H},
                "acces_doigts_capot_retire": fingers, "bonnette_disponible": windscreen_room(),
                "bonnette_volume_cm3": round(vol(ws) / 1000, 2)}
    assert clear["front"] >= MIC_CLEARANCE - 0.01 and clear["insert"] >= MIC_CLEARANCE - 0.01, clear
    assert clear["rear_hors_nid_et_disque"] >= MIC_CLEARANCE - 0.01, clear
    assert NEST_GAP - 0.01 <= clear["nid"] <= 0.5 + 0.01, clear
    assert all(f["obstacle_mm3"] < 0.01 and f["hauteur_libre_mm"] >= 9.0 for f in fingers.values()), fingers
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
            if v > 0.1:  # mm3 : en dessous, bruit des faces en contact (plan de joint)
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
    # eclate = ordre de montage : baie par l'arriere, puis tout le reste par le plan de joint
    roles = {"front": ("Capot avant", "black", (0, 0, 135)), "rear": ("Coque arriere", "black", (0, 0, 0)),
             "cover": ("Couvercle de la baie", "black", (0, 0, -62)), "ring": ("Anneau lumineux", "translucent", (0, 0, 10)),
             "collar-insert-14mm": ("Collier amovible 14 mm", "black", (0, 0, 150)),
             "mic": ("DJI Mic Mini 2", "electronics", (0, 0, 66)), "mic-disc": ("Disque acier 30 mm", "metal", (0, 0, 62)),
             "earpad": ("Coussin Brainwavz", "soft", (0, 0, 175)), "gasket": ("Joint mousse 3 x 2", "soft", (0, 0, 128)),
             "led-filament": ("Filament LED", "electronics", (0, 0, 5)), "foam-disc": ("Disque de mousse 20 mm", "foam", (0, 0, 45)),
             "foam-liner": ("Manchon de mousse 9 mm", "foam", (0, 0, 100)), "foam-liner-rear": ("Mousse des flancs arriere 8 mm", "foam", (0, 0, 58)),
             "windscreen": ("Bonnette 5 mm", "foam", (0, 0, 72)),
             "battery": ("LiPo 30 x 20 x 5", "electronics", (0, 0, -26)), "charger": ("Chargeur USB-C TP4056", "electronics", (0, 0, -44)),
             "switch": ("Interrupteur", "electronics", (0, 0, -44)), "joint-magnets": ("Aimants du joint 6 x 2", "metal", (0, 0, 3)),
             "joint-steel-discs": ("Pastilles acier du joint", "metal", (0, 0, 131)), "cover-magnets": ("Aimants du couvercle", "metal", (0, 0, -5)),
             "cover-steel-discs": ("Pastilles acier du couvercle", "metal", (0, 0, -57))}
    manifest = []
    shown = dict(parts) | refs | {"earpad": web_earpad()}
    for n, p in shown.items():
        f = web / f"{n}.stl"
        tol = WEB_TOL_FINE if n in ("front", "rear", "cover", "collar-insert-14mm") else WEB_TOL
        cq.exporters.export(p, str(f), tolerance=tol[0], angularTolerance=tol[1])
        assert f.stat().st_size < 1.5e6, (n, f.stat().st_size)
        label, role, ex = roles[n]
        manifest.append({"file": f.name, "label": label, "role": role, "explode": list(ex)})
    cq.exporters.export(air, str(web / "air-volume.stl"), tolerance=WEB_TOL[0], angularTolerance=WEB_TOL[1])
    manifest.append({"file": "air-volume.stl", "label": "Air : cavite et conduit", "role": "air", "explode": [0, 0, 0]})
    (web / "manifest.json").write_text(json.dumps({"units": "mm", "axes": "x lateral, y haut, z vers le visage, z=0 plan de joint",
                                                   "parts": manifest}, indent=2, ensure_ascii=False))
    (out / "metrics.json").write_text(json.dumps(m, indent=2, ensure_ascii=False))
    log("web", t)
    print(json.dumps({k: v for k, v in m.items() if k not in ("curvature",)}, indent=1, ensure_ascii=False))
    print(f"total {time.perf_counter() - t0:.1f} s")
    if fail:
        raise SystemExit("ECHEC : " + " ; ".join(fail))
    return m


if __name__ == "__main__":
    export()
