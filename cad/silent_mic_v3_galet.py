# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright 2026 Clement Barberousse
"""Silent Mic v3 galet : coque en galet tenue en main, coussin d'oreillette sur un
collier amovible, conduit annulaire d'un seul tour, joint visse (4 vis M3 par la bouche).

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
import tempfile
import time

import cadquery as cq
import numpy as np


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import whisper_mask_v0 as v0
import silent_mic_v3_coupons as cp
from whisper_mask_v2_screwed import loft_ellipses


# ---------- silhouette : une seule fonction a changer (outer_profile) ----------
PROFILE = os.environ.get("SILENT_MIC_PROFILE", "evase")
JOINT_S = 61.0  # plan de joint ; l'anneau lumineux loge juste derriere
# appui du coussin a s = 35 : capot avant raccourci de 5 mm le 23 nov. 2026 (decision de Clement, environ 1 dB(A) de
# moins au modele contre 5 mm de compacite) ; le corps garde son evasement, decale d'autant
S_SEAT, S_REAR = 35.0, 116.0
S_COVER = 108.0  # face arriere plane de la coque, fermee par le couvercle


def smoothstep(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def outer_profile(s):
    """Demi-axes (a, b) de la section exterieure a l'abscisse s (sections elliptiques)."""
    if PROFILE == "evase":
        if s < 60:
            k = 1 - smoothstep((s - S_SEAT) / 18)
            return 42 + 10 * k, 33 + 5.5 * k  # appui 104 x 77 (cp.SEAT), 2 mm sous le coussin mesure
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
GROOVE_DEPTH, BOSS_R = cp.GROOVE_DEPTH, cp.BOSS_R
REBATE, SCREW_OFFSET = cp.REBATE, cp.SCREW_OFFSET
FLANGE_TOP = GROOVE_DEPTH + 1.0
CAV_JOINT = 10.7  # offset de la cavite au joint et dans la bande du conduit
CORBEL = 9.5  # chanfrein sous le conduit (arriere) : 7.5 mm sur 9.5, 38 deg ; 45 deg pile est refuse par Orca
CORBEL_FRONT = 8.0  # sous la bride du capot : 43 deg, compromis avec l'angle du micro
# 4 vis M3 (cp.SCREW) serrent le joint, tetes dans la chambre ; rien en bas (barrage, tunnel des fils, entree)
# angles parametriques : en haut, les nervures des bossages restent hors du passage des doigts ; en bas, les
# bossages restent a plus de 1.5 mm de la plaque du micro
SCREW_T_DEG = (45, 135, 223, 317)

# ---------- coussin et collier amovible ----------
PAD = cp.PAD
# assise courbe et col d'une piece, posee sur l'appui plat (cp.saddle_collar) ; hauteur du col au-dessus du fond
# du coussin, au centre : 10 mm retenus avec Clement le 23 nov. 2026, puis assise des essais du 24 nov. (cp.BODY_SEAT :
# 20 mm au centre, dessus au rayon 53, bords 24 mm plus haut que l'assise R85)
COLLAR_HEIGHT, SEAT_RADIUS, RIM_RADIUS = cp.BODY_SEAT
COLLAR_INNER = cp.collar_inner()
# Le col repose sur 4 diamants (COL_DIAMOND), 0.5 mm au-dessus de l'appui : la place de l'anneau de mousse ecrase
SADDLE_GAP = 0.5
PAD_BASE = Z_SEAT + SADDLE_GAP + cp.SADDLE_T0  # fond du coussin au centre, sur l'assise
LEDGE = 1.5  # appui de la bride du collier (seul porte-a-faux au-dessus du plateau)
SEAT_OPENING = tuple(f - 2 * LEDGE for f in cp.flange_outer())

# ---------- conduit annulaire ----------
# Conduit de 42 mm2, decale vers l'exterieur (Clement, 25 nov. 2026) : paroi vers la chambre du micro de 3.7 mm au lieu
# de 1.6, paroi exterieure de 3 mm comme autour de la chambre (3.15 dans le plan de la section, 3.1 en normale a la
# peau qui penche). 42 mm2 : la plus petite section qui reste sous 50 Pa a
# 0.2 L/s (docs/v3-simulation.md) ; bosses, chicanes et garnissage coutent plus qu'ils ne rapportent.
DUCT = (3.15, 7.01)  # offsets radiaux : 3.86 mm
DUCT_H = 12.13  # 9.62 de flanc droit + toit en pointe 2.51 (faite vif) : 42 mm2, imprimable sans support
DUCT_TOP = -5.2  # 3 mm sous la rainure LED (exterieur)
DUCT_BOTTOM = DUCT_TOP - DUCT_H
DUCT_APEX = 0.0  # faite vif : un plat, meme de 0.3 mm, est un plafond qu'Orca supporte
STEEP = 1.3  # pente des surplombs internes : 1.3 en hauteur pour 1 en largeur (38 deg)
DUCT_ROOF_H = STEEP * ((DUCT[1] - DUCT[0]) - DUCT_APEX) / 2
DAM = 9.4  # barrage a 6 h, porte aussi le tunnel des fils : 3.1 mm de paroi de chaque cote du tunnel (2.9 a 9.0)
INLET_D = 8.0  # largeur de l'entree (voir INLET_W)
INLET_Z = DUCT_BOTTOM + 4.5  # repere de hauteur de l'entree (debut du controle de passage)
# Sortie de l'event en goulottes (Clement, 25 nov. 2026) : sous chaque ouverture, le plancher du conduit s'ouvre et le
# conduit continue, toute sa largeur, en pente a 52 deg (STEEP) jusqu'a la peau. Pose debout sur le dos, ce qui y tombe
# ressort seul ; plus de gorge d'ombre ni de rebord. Les nervures entre ouvertures portent la levre du haut : une
# ouverture unique de 42 mm l'imprimerait en pont courbe de 42 mm sans appui (supports "sur plateau uniquement"). Bouts
# arrondis, levre du haut arrondie en quart de cercle (OUTLET_NOSE) : rien de tranchant.
# Ligne fine (Clement, 26 nov. 2026 : les 4 goulottes de toute la largeur du conduit faisaient de gros trous de 6 a 7 mm
# de haut) : 5 goulottes etroites, 2.6 mm de haut a la peau, alignees de 6 h a 9 h, au ras du bord du conduit. Section
# droite d'environ 60 mm2 au lieu de 114 : 3 m/s a 0,2 L/s ; le conduit (42 mm2) garde la masse acoustique.
OUTLET_LEN, OUTLET_RIB, OUTLET_COUNT = 8.2, 1.2, 5
OUTLET_W = 1.6  # largeur horizontale de la goulotte au plancher du conduit, cote peau (hors OUTLET_WIDEN)
OUTLET_NOSE = 0.5
# goulotte elargie de 0.2 mm de chaque cote : ses faces croisent franchement les parois du conduit (aretes communes au
# plancher, la coque n'etait plus un solide valide avec le conduit a 3.15 mm)
OUTLET_WIDEN = 0.2
OUTLET_SIN = STEEP / math.hypot(1.0, STEEP)  # section droite de la goulotte = largeur horizontale x OUTLET_SIN
CORBEL_TOP = DUCT_BOTTOM - 1.6  # plancher du conduit garde 1.6 mm
CORBEL_BOTTOM = CORBEL_TOP - CORBEL

# ---------- arriere, baie, couvercle ----------
BAY_DEPTH = 10.5
FLOOR_TOP = Z_RF + BAY_DEPTH + WALL
FLOOR_RIB = 1.5
FOAM_LAYER = 10.0  # plaque du commerce de 10 mm (fond, manchon)
FOAM_DISC_T = 2 * FOAM_LAYER
LINER_T = 10.0
# section d'air libre le long de l'axe, de l'entree au coussin : 20 fois celle du conduit. Le seuil etait a
# 1200 avec le micro a plat ; debout au centre, il traverse la zone du manchon (1130 mm2 libres autour de lui)
MIN_PASSAGE = 1000.0
# 3.2 depuis le 24 nov. 2026 (2.6 avant) : le filament LED nOOds fait 1.7 x 1.9 mm (guide Adafruit) et doit pouvoir
# descendre lui-meme a la baie, vrille d'un quart de tour au coude (il ne plie pas sur sa largeur)
TUNNEL_D = 3.2
TUNNEL_OFFSET = 3.8
# vis de la trappe : entre les logements de la baie et le flanc bombe de la trappe ; controle dans export()
COVER_SCREW_XY = ((-19.6, -4.0), (19.6, -4.0))
COVER_HEAD_Z = Z_RF - 4.0  # portee plate de la tete cylindrique (v09, vis M3 x 12 de la boite), au fond d'un puits ouvert au dos
LIPO = (30.0, 20.0, 5.0)
CHARGER = (17.5, 28.0, 4.0)  # x, y, z ; USB-C vers le bas
SWITCH = (8.6, 3.6, 3.5)
# Le corps s'affine vers l'arriere : places a Z_RF + 4.5, chargeur et interrupteur laissaient leurs logements percer la
# peau au ras de la trappe (cad/light_check.py, 25 nov. 2026 : lumiere de la baie visible dehors). Recul vers
# l'interieur et jeu reduit cote peau, pour 1 mm de plastique noir au moins a la face arriere.
CHARGER_BACK, SWITCH_BACK = 0.8, 1.5

# ---------- micro : debout contre une plaque dressee au centre du fond, haut du boitier vers la bouche ----------
# Disposition du v2 (cad/whisper_mask_v0.py, memes cotes de plaque et de disque), reprise le 21 nov. 2026 sur
# decision de Clement : bonnette DJI en place, micro dans le souffle accepte. A plat sur un pied pres de la
# paroi basse, le micro et la tete du pied debordaient de 4 a 5.5 mm sous le rebord interieur du capot
# avant, qui ne pouvait ni se poser ni se retirer.
MIC_XC, MIC_YC = 0.0, 0.0  # boitier centre sur l'axe : la bonnette est centree dans le col
MOUNT_W, MOUNT_T = v0.MOUNT_WIDTH, v0.MOUNT_THICKNESS
MIC_CLEARANCE = 1.0
MIC_STACK_EXTRA = float(os.environ.get("SILENT_MIC_STACK_EXTRA", 0.0))  # clip ou aimant entre disque et boitier, a mesurer
BONNET = (36.0, 26.0, 9.0, 20.0)  # bonnette DJI : largeur, epaisseur, recouvrement du boitier, depassement. Depassement mesure par Clement (48 mm du bas du micro au haut des poils, 23 nov. 2026) ; largeur et epaisseur estimees
FINGER = 11.0  # largeur de doigt controlee de chaque cote de la bonnette, prise par la bouche (capot visse) ; le col elliptique laisse 11 mm sur toute l'epaisseur du boitier
# regle du v2 (AIR_GAP_TARGET) : 8 mm d'air entre le fond du coussin et ce qui depasse du micro. Clement a constate
# le 23 nov. 2026 sur le v2 imprime que ses levres descendent un peu sous le fond du coussin
AIR_GAP = v0.AIR_GAP_TARGET
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

FRONT_SMOOTH = tuple(S_SEAT + d for d in (0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0))  # l'evasement, 18 mm
FRONT_RULED = (S_SEAT + 18.0, 60.0, JOINT_S)
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
    # sous le pied du siege, l'ouverture s'evase a la pente STEEP, parallele a seat_corbel() et 0.1 mm devant lui :
    # droite (prisme), elle laissait 0.9 a 1.2 mm de plaque dans le vide sur tout le tour (capot v05 imprime le 26 nov.)
    z_bot = Z_SEAT - SEAT_PLATE - 1.0
    grow = 2 * (z_low - z_bot) / STEEP
    opening = wp(cq.Solid.makeLoft([ell(SEAT_OPENING[0] + grow, SEAT_OPENING[1] + grow, z_bot),
                                    ell(SEAT_OPENING[0] - 0.1, SEAT_OPENING[1] - 0.1, z_low + 0.05 * STEEP)], True))
    cone_ = wp(cq.Solid.makeLoft([ell(*SEAT_OPENING, z_low), ell(*top, Z_SEAT), ell(top[0] + 0.02, top[1] + 0.02, Z_SEAT + 1)], True))
    # le chanfrein sous le bord de l'ouverture (le coin haut du micro voyait l'arete de la plaque a 1.25 mm) est retire le
    # 26 nov. 2026 : capot retourne, il faisait un surplomb de 2,5 mm tout autour ; seat_corbel() degage le dessous de l'appui
    return joint.union(corbel).union(main).union(opening).union(cone_)


def section_point(t, d, z):
    """Point a l'offset d de la section locale a z, angle parametrique t."""
    a, b = outer_profile(s_of(z))
    n = (b * math.cos(t), a * math.sin(t))
    k = math.hypot(*n)
    return a * math.cos(t) - d * n[0] / k, b * math.sin(t) - d * n[1] / k


# ---------- col visse sur l'appui (Clement, 25-26 nov. 2026) ----------
# L'assise et son col se vissent sur l'appui du capot au lieu d'y etre colles : un joint colle juste devant la bouche
# ne se controle ni ne se rouvre. 4 vis M3 x 12 a tete cylindrique sur rondelle, posees par le dessus du col (sous le coussin, seul colle),
# serrent un anneau de mousse a cellules fermees de 1 mm entre le col et l'appui. Par en dessous, aucun outil
# n'atteindrait la plaque : le capot se resserre en entonnoir jusqu'au joint. Ecrou prisonnier dans la plaque, comme
# a la coque arriere : il tire vers le col. Mais le col reste sur ses diamants, 0.5 mm au-dessus, sur de la mousse :
# la peau au-dessus de l'ecrou travaille en poinconnement, pas en compression comme a la coque (ou les bossages se touchent).
COL_SCREW_T_DEG = (45, 135, 225, 315)
# dans la bande d'appui, du bord de l'ouverture (0) a la peau (1) ; 0.3 jusqu'a la v06, 0.25 depuis la rondelle d'ecrou
# (27 nov. 2026), qui descend l'ecrou de 0.5 mm la ou la peau se resserre : logement a 1.4 mm de la peau (controle)
COL_SCREW_FRAC = 0.22  # 0.22 depuis la v14 : logement d'ecrou de 3.0 x 6.0, plus grand, a 1 mm au moins de la peau
COL_NUT_SKIN = 2.0  # serrage ferme demande (Clement, 26 nov. 2026) ; FEM (mechanics/fem) : rupture de la peau vers 650-810 N par vis au lieu de 480-600 avec 1.2 mm
# portee plate de la rondelle au-dessus du dos du col : 4.5 mm de col sous la rondelle depuis la v09 (M3 x 12 au lieu
# de 10 : la portee monte de 2 mm, la pointe reste ou elle etait, 1.6 mm sous l'ecrou serre et sa rondelle ; plus bas,
# le percage crevait la peau en entonnoir du capot). Controle dans export()
COL_SEAT_Z = 2.5 + (cp.SCREW_LEN - 10.0)


def col_screw_xy():
    fo, sk = cp.flange_outer(), outer_profile(S_SEAT)
    a, b = (fo[i] / 2 + cp.FLANGE_GAP + COL_SCREW_FRAC * (sk[i] - fo[i] / 2 - cp.FLANGE_GAP) for i in (0, 1))
    return [(a * math.cos(math.radians(t)), b * math.sin(math.radians(t))) for t in COL_SCREW_T_DEG]


def col_screw_tip_z():
    """Pointe d'une M3 x 12 serree, rondelle sous la tete, col pose sur ses diamants."""
    return Z_SEAT + SADDLE_GAP + COL_SEAT_Z + cp.WASHER[1] - cp.SCREW_LEN


def col_nut_z():
    """Bas du logement (niveau de l'ecrou) et plafond (sous la peau) ; le niveau de la rondelle est en haut."""
    z1 = Z_SEAT - COL_NUT_SKIN
    return z1 - cp.WASHER_LEVEL - cp.NUT[1], z1


def build_col_bosses():
    """Sous la plaque d'appui : de quoi loger l'ecrou (il depasse de la plaque de 1 mm) et guider la vis."""
    z0 = col_nut_z()[0] - 3.0
    # pied conique a la pente STEEP : a plat, le dessous du bossage s'imprimait a moitie dans le vide (capot v05, couche 19.2)
    h = (cp.BOSS_R - 0.8) * STEEP
    return union_all(cq.Workplane("XY", origin=(x, y, z0)).circle(cp.BOSS_R).extrude(Z_SEAT - SEAT_PLATE + 0.5 - z0)
                     .union(wp(cq.Solid.makeCone(0.8, cp.BOSS_R, h + 0.01, cq.Vector(x, y, z0 - h), cq.Vector(0, 0, 1))))
                     for x, y in col_screw_xy())


def col_screw_cut_front():
    """Passage de la vis, logement d'ecrou et, au-dessus, niveau de la rondelle, ouverts vers le centre pour y glisser
    l'ecrou puis la rondelle par l'ouverture du capot ; un plat de l'ecrou face a la peau, qui se resserre sous l'appui.
    Capot imprime joint au plateau : le plafond du niveau de la rondelle est un pont, dont la premiere couche
    (cp.MEMBRANE) reste pleine pour que la rondelle porte sur toute sa surface : elle n'est que dans le STL d'impression
    (print_membranes), on la perce au montage."""
    z0, z1 = col_nut_z()
    zw = z0 + cp.NUT[1]
    r, rw, half = cp.SCREW[0] / 2, cp.WASHER_WELL_R, cp.NUT[0] * math.cos(math.radians(30)) / 2
    out = []
    for x, y in col_screw_xy():
        # passage borgne, 0.8 mm sous la pointe : traversant (3.5 sous l'ecrou), il passait a 0.6 mm de la peau en entonnoir
        zb = col_screw_tip_z() - 0.8
        local = (cq.Workplane("XY", origin=(0, 0, zb)).circle(r).extrude(Z_SEAT + 0.5 - zb)
                 .union(cq.Workplane("XY", origin=(0, 0, z0)).polygon(6, cp.NUT[0]).extrude(cp.NUT[1]).rotate((0, 0, 0), (0, 0, 1), 30))
                 .union(cp._lbox(0, cp.BOSS_R + 6.0, half, z0, zw))
                 .union(cq.Workplane("XY", origin=(0, 0, zw)).circle(rw).extrude(z1 - zw)).union(cp._lbox(0, cp.BOSS_R + 6.0, rw, zw, z1)))
        out.append(local.rotate((0, 0, 0), (0, 0, 1), math.degrees(math.atan2(-y, -x))).translate((x, y, 0)))
    return union_all(out)


def print_membranes():
    """Membranes des logements de rondelle d'ecrou (cp.nut_membrane), pour les STL d'impression : capot (col), coque (joint)."""
    return {"front": union_all(cp.nut_membrane(x, y, col_nut_z()[1]) for x, y in col_screw_xy()),
            "rear": union_all(cp.nut_membrane(x, y, -cp.NUT_SKIN) for x, y in screw_xy())}


def col_screw_cut_saddle():
    """Dans le col (repere du col, dos a z = 0, imprime dos au plateau) : passage, portee plate de la rondelle,
    puits de la rondelle et de la tete jusqu'au-dessus."""
    r = cp.SCREW[0] / 2
    return union_all(cq.Workplane("XY", origin=(x, y, -0.5)).circle(r).extrude(COL_SEAT_Z + 0.5)
                     .union(cq.Workplane("XY", origin=(x, y, COL_SEAT_Z - 0.01)).circle(cp.WASHER_WELL_R).extrude(60))
                     for x, y in col_screw_xy())


# Centrage du col par 4 diamants (Clement, 26 nov. 2026) : pyramides tronquees sur l'appui du capot, aux bouts des axes,
# dans des logements de meme pente sous le col. Les vis tirent le col : les pentes le centrent sans jeu a chaque remontage,
# rien ne s'use ni ne travaille en ressort ; un ecart d'impression fait juste asseoir le col un peu plus haut ou plus bas,
# la mousse rattrape. Tenons a nervures ecartes (rabotees au premier montage), crochets souples ecartes (fluage du PLA).
# Temoin du 26 nov. 2026 : centrage parfait, mais 1 a 2 mm de jour au lieu de 0.5. A 30 deg, 0.1 mm de trop en largeur
# souleve le col de 0.17 mm : aretes vives des pyramides dans les coins arrondis du logement, premiere couche ecrasee qui
# retrecit son entree, trous imprimes plus petits. D'ou des cones (pas d'aretes), une entree chanfreinee a 45 deg, 0.15 mm
# de compensation et un fond plus profond. Second temoin (meme jour) : le G-code reproduit les cotes a 0.01 mm pres et
# predit 0.4 mm de jour (marches de couche emboitees) ; le reste vient de l'impression (trous plus petits, cones plus
# gros), environ 0.3 a 0.4 mm par cote. Compensation portee a 0.35 : environ 0.2 mm de jour de moins, plus de temoin.
COL_DIAMOND = (5.0, 2.25)  # diametre a la base, hauteur
COL_DIAMOND_SLOPE = math.tan(math.radians(30))  # flancs, depuis la verticale
COL_DIAMOND_FIT = 0.35  # compensation d'impression du logement, par cote
COL_DIAMOND_ROOF = 1.0  # le sommet du cone reste a cette distance du fond du logement


def col_diamond_xy():
    """Bouts des axes, au milieu de la bande d'appui."""
    fo, sk = cp.flange_outer(), outer_profile(S_SEAT)
    a, b = ((fo[i] / 2 + cp.FLANGE_GAP + sk[i]) / 2 for i in (0, 1))
    return [(a, 0.0), (-a, 0.0), (0.0, b), (0.0, -b)]


def _cone(r0, r1, z0, z1, x, y):
    return wp(cq.Solid.makeCone(r0, r1, z1 - z0, cq.Vector(x, y, z0), cq.Vector(0, 0, 1)))


def build_col_diamonds():
    d, h = COL_DIAMOND
    r0 = d / 2
    return union_all(_cone(r0, r0 - h * COL_DIAMOND_SLOPE, Z_SEAT, Z_SEAT + h, x, y)
                     .union(wp(cq.Solid.makeCylinder(r0, 0.3, cq.Vector(x, y, Z_SEAT - 0.3)))) for x, y in col_diamond_xy())


def col_diamond_pockets():
    """Logements sous le col (repere du col, dos a z = 0) : meme pente, prise a SADDLE_GAP au-dessus de l'appui, plus
    COL_DIAMOND_FIT ; entree chanfreinee de 0.4 mm a 45 deg ; fond a COL_DIAMOND_ROOF au-dessus du sommet du cone."""
    d, h = COL_DIAMOND
    depth = h - SADDLE_GAP + COL_DIAMOND_ROOF
    rm = d / 2 - SADDLE_GAP * COL_DIAMOND_SLOPE + COL_DIAMOND_FIT
    return union_all(_cone(rm, rm - depth * COL_DIAMOND_SLOPE, -0.01, depth, x, y).union(_cone(rm + 0.41, rm, -0.01, 0.4, x, y))
                     for x, y in col_diamond_xy())


def col_diamond_pocket_depth():
    return COL_DIAMOND[1] - SADDLE_GAP + COL_DIAMOND_ROOF


def col_piece():
    return cp.body_saddle().cut(col_screw_cut_saddle()).cut(col_diamond_pockets())


def temoin_pieces(front):
    """Temoin du col (26 nov. 2026) : les 4 diamants et leurs logements, decoupes dans les vraies pieces. Plaque d'appui
    du capot sur 1.6 mm et bas du col jusqu'a 0.6 mm au-dessus du fond des logements, reduit a la bande d'appui :
    environ 30 min d'impression. Il se monte a la main, sans vis ni ecrous (deja eprouves sur le joint) : on y juge le
    centrage par les pentes et le jeu, et on le demonte et remonte plusieurs fois."""
    return {"capot": front.intersect(box(-80, 80, -80, 80, Z_SEAT - 1.6, Z_SEAT + 5.0)),
            "col": col_piece().intersect(box(-80, 80, -80, 80, 0.0, col_diamond_pocket_depth() + 0.6)).cut(eprism(*(o + 2.0 for o in SEAT_OPENING), -1.0, 10.0))}


def seat_corbel():
    """Chanfrein sous l'appui du coussin : le capot s'imprime retourne, joint sur le plateau (26 nov. 2026), pour que les
    diamants sortent par le haut ; sans lui, le dessous de l'appui (5 a 7 mm de rebord) et les bossages d'ecrou du col
    seraient imprimes dans le vide. Il part du bord de l'ouverture (passage du micro inchange) et descend a 52 deg."""
    # il monte jusqu'au pied du siege conique de l'ouverture, 0.1 mm en retrait de lui et de son evasement (pas d'arete
    # commune) ; 0.3 laissait 0.45 mm de marche au G-code sous la plaque (une ligne dans le vide), 0.1 en laisse 0.25
    top = tuple(f + 2 * cp.FLANGE_GAP for f in cp.flange_outer())
    zt, drop = Z_SEAT - STEEP * (top[0] - SEAT_OPENING[0]) / 2, 10.0
    w, h = (o + 0.2 for o in SEAT_OPENING)
    cone = wp(cq.Solid.makeLoft([ell(w, h, zt + 0.01), ell(w + 2 * drop / STEEP, h + 2 * drop / STEEP, zt - drop)], True))
    return box(-80, 80, -80, 80, zt - drop + 0.01, zt).cut(cone)


def build_front_bosses():
    """Bossages des vis du capot (imprime appui du coussin en bas, joint en haut) : un pave au-dessus du joint,
    tenu par deux nervures de 1.3 mm qui montent a 38 deg jusqu'a la paroi et a la plaque d'appui. Entre les
    nervures, le puits de la tete reste ouvert vers la chambre (voir cp.screw_hole_front)."""
    h, far, half, rw = cp.BOSS_FRONT_H, cp.BOSS_FAR, cp.BOSS_HALF, cp.WASHER_WELL_R
    z_end = Z_SEAT - SEAT_PLATE + 0.5
    prof = [(-40.0, h - 0.01), (far, h - 0.01), (far - (z_end - h) / STEEP, z_end), (-40.0, z_end)]
    local = box(-(SCREW_OFFSET - 9.0), far, -half, half, 0, h)
    for yc in (-(rw + half) / 2, (rw + half) / 2):
        local = local.union(cq.Workplane("XZ", origin=(0, yc, 0)).polyline(prof).close().extrude((half - rw) / 2, both=True))
    # cote chambre, arrondi au cercle du bossage de la coque (BOSS_R) : ses coins depassaient de 1.25 mm en diagonale
    # (Clement, 27 nov. 2026, v12). Jamais plus large qu'avant : le jeu au pouce qui sort le micro ne peut que croitre
    keep = cq.Workplane("XY", origin=(0, 0, -1)).circle(cp.BOSS_R).extrude(100).union(box(-40, 0, -half - 1, half + 1, -1, 99))
    local = local.intersect(keep)
    # et complete au cercle entier sur sa hauteur (v13) : a 4.6 de demi-largeur, il laissait de part et d'autre deux
    # croissants de 0.4 mm du dessus du bossage de la coque sans rien en face (controle des faces du plan de joint)
    # 0.02 mm sous BOSS_R : deux cylindres identiques face a face font echouer les booleens d'OCCT (passage d'air)
    local = local.union(cq.Workplane("XY").circle(cp.BOSS_R - 0.02).extrude(h))
    return union_all(local.rotate((0, 0, 0), (0, 0, 1), ang).translate((x, y, 0)) for x, y, ang in screw_frames())


def build_front(front_env):
    t = time.perf_counter()
    shell = front_env.cut(front_cavity_tool())
    log("  cavite avant", t)
    shell = shell.union(build_front_bosses().intersect(front_env)).union(build_col_bosses().intersect(front_env))
    shell = shell.union(seat_corbel().intersect(front_env)).union(build_col_diamonds())
    log("  bossages", t)
    shell = shell.cut(ring(GROOVE[0], GROOVE[1], -1, GROOVE_DEPTH)).cut(front_screw_cut()).cut(col_screw_cut_front())
    for w, z in cp.GROOVE_CHAMFER:  # entree de la rainure en escalier a 45 deg (v10)
        shell = shell.cut(ring(GROOVE[0] - w, GROOVE[1] + w, -1, z))
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
OUTLET_S = [-(DAM / 2 + 1.0 + OUTLET_LEN / 2 + i * (OUTLET_LEN + OUTLET_RIB)) for i in range(OUTLET_COUNT)]


INLET_W, INLET_RECT = 8.0, 3.5
INLET_BOTTOM = DUCT_BOTTOM + 0.33
INLET_AREA = INLET_W * INLET_RECT + INLET_W * STEEP * INLET_W / 4


def skin_inset(t, z):
    """Retrait de la peau a z par rapport a la section du joint, le long de la normale au point t.
    La coque s'affine vers l'arriere : conduit, gorge et chambre suivent la peau locale, alors que
    place() pose ses outils sur la section du joint. Sans ce retrait, fentes et entree s'arretaient
    dans la paroi (0.2 a 0.9 mm de plastique restaient au bout)."""
    a, b = EJ
    az, bz = outer_profile(s_of(z))
    n = (b * math.cos(t), a * math.sin(t))
    return ((a - az) * n[0] * math.cos(t) + (b - bz) * n[1] * math.sin(t)) / math.hypot(*n)


def build_inlet():
    """Entree en pentagone : flancs verticaux, toit a 38 deg dont le faite reste sous le toit
    interieur du conduit (sinon poche dans le toit, qu'Orca supporte)."""
    zb, zr = INLET_BOTTOM, INLET_BOTTOM + INLET_RECT
    t = t_at(CENTER_TABLE, INLET_S)
    y0 = DUCT[1] - 0.6  # dans le vide du conduit
    y1 = CAV_JOINT + skin_inset(t, CORBEL_TOP) + 1.0  # 1 mm dans le vide de la chambre, au plus loin de la cloison
    port = (cq.Workplane("XZ", origin=(0, y0, 0))
            .polyline([(-INLET_W / 2, zb), (INLET_W / 2, zb), (INLET_W / 2, zr), (0, zr + STEEP * INLET_W / 2), (-INLET_W / 2, zr)])
            .close().extrude(-(y1 - y0)))
    return place(port, t)


def chute_edges():
    """Plafond et plancher de la goulotte au plancher du conduit, en offsets depuis la peau."""
    return DUCT[0] - OUTLET_WIDEN, DUCT[0] + OUTLET_W + OUTLET_WIDEN


def outlet_lip():
    """Hauteurs de la levre haute : arete vive d'origine, bas du nez, haut du nez sur la peau."""
    z_lip = DUCT_BOTTOM - STEEP * chute_edges()[0]
    return z_lip, z_lip + STEEP * OUTLET_NOSE, z_lip + (STEEP + 1.0) * OUTLET_NOSE


def outlet_profile():
    """Goulotte et nez de la levre haute, tout le tour (offsets depuis la peau locale) ; build_outlet() en garde
    les ouvertures. Goulotte : entre le plafond U(z) = c0 + (z - DUCT_BOTTOM) / STEEP et le plancher
    L(z) = c1 + (z - DUCT_BOTTOM) / STEEP (chute_edges), du plancher du conduit jusqu'au-dela de la peau. Nez : la levre haute (un coin de 38 deg entre peau et plafond) devient un quart de cercle, vertical sur la
    peau, horizontal au plafond."""
    (o0, o1), zb, k = chute_edges(), DUCT_BOTTOM, STEEP
    z_lo = zb - k * (o1 + 1.0)
    # droites prolongees de 0.5 mm au-dessus du plancher, dans l'air du conduit : elles le croisent franchement
    ceil = loft_wires([(z_lo, o0 - o1 - 1.0), (zb + 0.5, o0 + 0.5 / k)])
    floor = loft_wires([(z_lo - 1.0, -1.0 - 1.0 / k), (zb + 1.0, o1 + 1.0 / k)])
    chute = ceil.cut(floor)
    r = OUTLET_NOSE
    z_lip, z_t, z_s = outlet_lip()
    # le nez deborde de 0.3 mm dans la goulotte sous son point bas : aucune face commune avec le plafond ; il finit 0.08 mm
    # hors de la peau, qu'il croise a 23 deg : tangent a la peau, le maillage de la coque s'ouvrait a son bord
    arc = [(z_s - r * math.sin(a), r * (1 - math.cos(a)) - 0.08) for a in (math.pi / 2 * i / 8 for i in range(8, -1, -1))]
    keep = loft_wires([(z_lip - 1.6, -1.1), (z_lip - 0.6, -1.1), (z_lip, 0.3), (z_t - 0.25, r - 0.25 / k + 0.3)] + arc
                      + [(z_s + 0.6, -1.1), (z_s + 1.6, -1.1)])
    nose = loft_wires([(z_lip - 0.6, -1.0), (z_s + 0.6, -1.0)]).cut(keep)
    return chute.union(nose)


def outlet_frames():
    """Axe de chaque goulotte (de la peau au plancher du conduit) et sa tangente, en coordonnees globales."""
    o_mid, zb = sum(chute_edges()) / 2, DUCT_BOTTOM
    out = []
    for s in OUTLET_S:
        t = t_at(CENTER_TABLE, s)
        p = cq.Vector(*section_point(t, 0.0, zb - STEEP * o_mid), zb - STEEP * o_mid)
        q = cq.Vector(*section_point(t, o_mid, zb), zb)
        tx, ty = eq_point(t, 0.0)[1]
        out.append((p, q, cq.Vector(tx, ty, 0.0)))
    return out


def build_outlet():
    """Ouvertures de la sortie : la goulotte et le nez gardes dans un stade incline le long de la goulotte (bouts
    arrondis), plus large que la goulotte cote plafond pour garder le nez."""
    c0, c1 = chute_edges()
    h = (c1 - c0) * OUTLET_SIN / 2  # demi-epaisseur droite de la goulotte
    z_lip, _, z_s = outlet_lip()
    nose = (z_s - z_lip) * math.cos(math.atan(STEEP))  # le nez depasse du plafond de cette distance, en section droite
    margin = 0.3
    width = 2 * h + nose + 2 * margin
    prof = outlet_profile().intersect(box(-70, 70, -70, 4, z_lip - 10, DUCT_BOTTOM + 2))
    out = []
    for p, q, tan in outlet_frames():
        axis = (q - p).normalized()
        x_dir = (tan - axis * tan.dot(axis)).normalized()
        v = axis.cross(x_dir)
        v = v if v.z > 0 else -v  # vers le plafond
        origin = (p + q) * 0.5 + v * (nose / 2)
        plane = cq.Plane(origin=origin, xDir=x_dir, normal=axis)
        stadium = cq.Workplane(plane).slot2D(OUTLET_LEN, width).extrude((q - p).Length / 2 + 3.0, both=True)
        out.append(prof.intersect(stadium))
    return union_all(out)


def wall_section(tool, d, z0, z1, t=0.1):
    """Section d'un outil (fentes, entree) la ou il traverse la surface a l'offset d de la peau locale :
    aire sur une surface verticale, mesuree dans une bande d'epaisseur t. Les deux bornes sont reglees
    sur la meme hauteur que la paroi mesuree : ring() les regle sur deux hauteurs et fausse l'epaisseur."""
    return (vol(tool.intersect(band(d, z0, z1))) - vol(tool.intersect(band(d + t, z0, z1)))) / t


# ================= joint, vis, tunnel =================

def screw_xy():
    return [eq_point(math.radians(t), SCREW_OFFSET)[0] for t in SCREW_T_DEG]


def screw_frames():
    """Par vis : x, y et direction (degres) de la normale a la paroi, vers l'interieur de la chambre."""
    out = []
    for t in SCREW_T_DEG:
        (x, y), (tx, ty) = eq_point(math.radians(t), SCREW_OFFSET)
        out.append((x, y, math.degrees(math.atan2(tx, -ty))))
    return out


def front_screw_cut():
    """Capot : passages, fraisures et puits des tetes, ouverts vers la bouche. Les vis se serrent par
    l'ouverture de l'appui du coussin, col retire ; le manchon de mousse a une encoche a chaque puits."""
    return union_all(cp.screw_hole_front(x, y, Z_SEAT + 1.0, ang) for x, y, ang in screw_frames())


def rear_screw_cut():
    """Coque arriere : passages des vis et logements d'ecrou, fentes tournees vers le plan y = 0 (loin de la
    plaque du micro). Tout reste a l'interieur de la rainure du joint : aucun chemin de fuite ajoute."""
    return union_all(cp.screw_hole_rear(x, y, -90 if y > 0 else 90) for x, y in screw_xy())


def cap_screw_solid(x, y, z_seat):
    """Vis M3 x 12 a tete cylindrique (ISO 4762) sur sa rondelle, posee sur une portee plate a z_seat, tige vers -z."""
    wt, (dh, hh) = cp.WASHER[1], cp.CAP_HEAD
    washer = cq.Workplane("XY", origin=(x, y, z_seat)).circle(cp.WASHER[0] / 2).circle(1.6).extrude(wt)
    head = cq.Workplane("XY", origin=(x, y, z_seat + wt)).circle(dh / 2).extrude(hh)
    shank = cq.Workplane("XY", origin=(x, y, z_seat + wt - cp.SCREW_LEN)).circle(1.5).extrude(cp.SCREW_LEN + 0.01)
    return washer.union(head).union(shank)


def cover_screw_solid(x, y, z_seat, shank_r):
    """Vis de la trappe (M3 a tete cylindrique) : dessous de la tete a z_seat, tete vers le dos (-z), tige vers +z."""
    dh, hh = cp.CAP_HEAD
    head = cq.Workplane("XY", origin=(x, y, z_seat - hh)).circle(dh / 2).extrude(hh)
    return head.union(cq.Workplane("XY", origin=(x, y, z_seat)).circle(shank_r).extrude(cp.SCREW_LEN))


def build_rear_bosses():
    """Bossages des ecrous, prolonges par un contrefort a 38 deg qui finit dans la paroi
    interieure du conduit (coque imprimee z vers le haut : pas de pointe pendante)."""
    h, R = cp.BOSS_REAR_H, BOSS_R
    r_end, d_end = 0.8, 10.0
    out = []
    for t in SCREW_T_DEG:
        x, y = eq_point(math.radians(t), SCREW_OFFSET)[0]
        z_end = -h - STEEP * ((SCREW_OFFSET + R) - (d_end + r_end))
        xe, ye = section_point(math.radians(t), d_end, z_end)
        cyl = cq.Workplane("XY", origin=(x, y, -h)).circle(R).extrude(h)
        but = wp(cq.Solid.makeLoft([cq.Workplane("XY", origin=(xe, ye, z_end)).circle(r_end).wire().val(),
                                    cq.Workplane("XY", origin=(x, y, -h)).circle(R).wire().val()], True))
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
    # nervure entaillee devant la plaque : depuis que le micro est abaisse, le bas du disque d'acier passe au ras du fond
    ribs = ribs.cut(box(-16, 16, MOUNT_FACE_Y - 0.1, MOUNT_FACE_Y + 1.0, FLOOR_TOP - 1, zt + 1))
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
    yb = -(b - 2.5) * math.sqrt(1 - (CHARGER[0] / 2 / (a - 2.5)) ** 2) + 0.7 + CHARGER_BACK
    charger = box(-CHARGER[0] / 2, CHARGER[0] / 2, yb, yb + CHARGER[1], zr + 0.4, zr + 0.4 + CHARGER[2])
    sx = 15.3
    ys = -(b - 2.5) * math.sqrt(1 - ((sx + SWITCH[0] / 2) / (a - 2.5)) ** 2) + 0.7 + SWITCH_BACK
    switch = box(sx - SWITCH[0] / 2, sx + SWITCH[0] / 2, ys, ys + SWITCH[1], zr + 0.4, zr + 0.4 + SWITCH[2])
    return lipo, charger, switch


def grow(b, m):
    bb = b.val().BoundingBox()
    return box(bb.xmin - m, bb.xmax + m, bb.ymin - m, bb.ymax + m, bb.zmin - m, bb.zmax + m)


def bay_cut():
    lipo, charger, switch = bay_boxes()
    # un seul plafond de baie (pont unique) : chaque logement monte jusqu'au plafond
    # jeux (x-, x+, y-, y+) : 0.5 partout sauf cote peau ; la carte du chargeur fait 16.5 mm de large pour 17.5 dessines.
    # Plus de degagement sous le chargeur jusqu'a y = -40 : il traversait la paroi (fentes de part et d'autre de la prise)
    def full(b, mx0=0.5, mx1=0.5, my0=0.5, my1=0.5):
        q = b.val().BoundingBox()
        return box(q.xmin - mx0, q.xmax + mx1, q.ymin - my0, q.ymax + my1, Z_RF - 1, Z_RF + BAY_DEPTH)
    bay = union_all([full(lipo), full(charger, 0.0, 0.0, 0.2), full(switch, 0.5, 0.3, 0.2)])
    cb = charger.val().BoundingBox()
    # stade de 12 x 6 pour le surmoulage de la fiche ; sans toit en pointe (Clement, 26 nov. 2026 : il la faisait paraitre
    # deux fois trop haute) : son plafond, 3 mm de paroi, s'imprime en pont de 12 mm
    usb = cq.Workplane("XZ", origin=(0, cb.ymin + 2, Z_RF + 2.6)).slot2D(12.0, 6.0).extrude(20)
    sb = switch.val().BoundingBox()
    lever = box(15.3 - 2.0, 15.3 + 2.0, -45, sb.ymin + 0.1, Z_RF + 1.2, Z_RF + 3.4)
    return bay.union(usb).union(lever)


def cover_screw_cut():
    """Trappe : passage et puits de tete des 2 vis, ouverts au dos ; la tete cylindrique porte sur le fond plat du
    puits (trappe imprimee face plane sur le plateau : le fond s'imprime en dessus, sans surplomb). Fraisure jusqu'a
    la v08, pour des vis fraisees que la boite de Clement n'a pas."""
    r = cp.SCREW[0] / 2
    out = []
    for x, y in COVER_SCREW_XY:
        hole = cq.Workplane("XY", origin=(x, y, COVER_HEAD_Z)).circle(r).extrude(Z_RF - COVER_HEAD_Z + 0.5)
        well = cq.Workplane("XY", origin=(x, y, Z_END - 1.0)).circle(cp.HEAD_WELL_R).extrude(COVER_HEAD_Z - Z_END + 1.0)
        out.append(hole.union(well))
    return union_all(out)


# plancher du logement d'ecrou de la trappe : 4.5 mm de coque sous l'ecrou, sur lesquels il tire ; logement de
# NUT[1] + 1.0 de haut pour que la pointe serree (Z_RF + 8) reste 0.5 mm sous son plafond, sans percer le pont
COVER_NUT_Z = Z_RF + 4.5
COVER_NUT_H = cp.NUT[1] + 1.0


def cover_nut_cut():
    """Trappe sur ecrous prisonniers depuis la v15 (Clement, 28 nov. 2026 : la trappe s'ouvrira pendant les essais de
    l'electronique, un filet taille dans le PLA s'use a chaque remontage). Passage de la vis depuis le dos, puis
    logement d'ecrou M3 ouvert vers le centre, ou la baie est a 4 mm de l'axe : l'ecrou s'y glisse, trappe ouverte,
    avant la batterie et le chargeur. Le serrage tire l'ecrou vers le dos, sur le plancher imprime plein."""
    r, half = cp.SCREW[0] / 2, cp.NUT[0] * math.cos(math.radians(30)) / 2
    out = []
    for x, y in COVER_SCREW_XY:
        local = (cq.Workplane("XY", origin=(0, 0, Z_RF - 0.5)).circle(r).extrude(COVER_NUT_Z - Z_RF + 0.6)
                 .union(cq.Workplane("XY", origin=(0, 0, COVER_NUT_Z)).polygon(6, cp.NUT[0]).extrude(COVER_NUT_H))  # un angle vers la fente
                 .union(cp._lbox(0, 8.0, half, COVER_NUT_Z, COVER_NUT_Z + COVER_NUT_H)))
        out.append(local.rotate((0, 0, 0), (0, 0, 1), 180 if x > 0 else 0).translate((x, y, 0)))
    return union_all(out)


def build_rear(rear_env):
    t = time.perf_counter()
    env = rear_env.intersect(box(-70, 70, -70, 70, Z_RF, 0))
    log("  enveloppe arriere", t)
    shell = env.cut(rear_cavity_tool())
    log("  cavite arriere", t)
    shell = shell.union(build_rear_bosses()).union(build_tunnel_rib().intersect(env))
    # le disque de mousse est retenu par le chanfrein a 45 deg sous le conduit (pas de taquets)
    shell = shell.union(build_floor_features()).union(build_mic_mount())
    shell = shell.union(ring(TONGUE[0], TONGUE[1], -0.5, TONGUE[2]))
    log("  ajouts arriere", t)
    shell = shell.cut(build_duct()).cut(build_inlet()).cut(build_outlet())
    log("  conduit, entree, sortie", t)
    shell = shell.cut(ring(-1.0, REBATE, -RING_H, 1)).cut(ring(LED_CH[0], LED_CH[1], -LED_CH[2], 1))
    shell = shell.cut(rear_screw_cut()).cut(build_tunnel())
    shell = shell.cut(bay_cut()).cut(cover_nut_cut())
    log("coque arriere", t)
    return shell


def build_cover(rear_env, holes=True):
    t = time.perf_counter()
    cover = rear_env.intersect(box(-70, 70, -70, 70, Z_END - 1, Z_RF))
    try:
        cover = cover.faces("<Z").edges().fillet(REAR_FILLET)
    except Exception as exc:  # shortcut: sans conge si OCCT refuse ; a reprendre a la main
        print(f"conge du dos refuse : {exc}")
    if holes:
        cover = cover.cut(cover_screw_cut())
        if not cover.val().isValid():  # les puits croisent le conge du dos : forme a reparer, volume inchange
            v = vol(cover)
            cover = wp(cover.val().fix())
            assert abs(vol(cover) - v) < 1e-3 * v
    log("couvercle", t)
    return cover


# Anneau tenu sans colle (Clement, 25 nov. 2026) : boucle fermee dans sa feuillure, il ne peut sortir qu'en montant et
# le capot l'en empeche une fois ferme. Il est plaque contre le capot : pas de jour au ras du capot, donc ni ligne visible
# ni filet de lumiere directe venu de la rainure LED. Pour cela son corps fait RING_BODY (12 couches de 0.2 mm, sans
# arrondi du trancheur) et laisse RING_LIFT sous lui, rattrape par RING_BUMPS plots imprimes RING_BUMP_H de haut, qui
# s'ecrasent de RING_BUMP_H - RING_LIFT sur le fond de la feuillure au serrage (petits : environ 30 N chacun). Au jeu
# de 0.2 mm sous l'anneau, la marche de 0.4 mm au fond de la rainure LED barre la lumiere. Modele : 0.02 mm de jeu
# partout, pour les controles d'interference. L'epaisseur traversee par la lumiere (RING_LIGHT) se regle par une gorge
# au dos, cote LED, entre deux rebords fixes : faces de serrage inchangees (controle dans export()).
RING_BODY, RING_LIFT = 2.4, 0.2
RING_BUMPS, RING_BUMP, RING_BUMP_H = 8, (1.2, 0.45), 0.4  # nombre, longueur et largeur (une ligne), hauteur imprimee
RING_LIGHT = cp.RING_DEPTH  # epaisseur traversee par la lumiere ; plus fine, la gorge du dos se creuse
RING_LIP = 0.6  # rebords haut et bas conserves de part et d'autre de la gorge
assert abs(RING_BODY + RING_LIFT - RING_H) < 1e-9 and RING_BUMP_H > RING_LIFT


def build_ring(printed=False, light=None):
    light = RING_LIGHT if light is None else light
    z0, z1 = -RING_H + RING_LIFT, -0.02  # corps
    out = ring(0.0, cp.RING_DEPTH, z0, z1)
    if light < cp.RING_DEPTH - 1e-9:
        assert light >= 0.8, "paroi lumineuse de moins de deux lignes d'extrusion"
        out = out.cut(ring(light, cp.RING_DEPTH + 1, z0 + RING_LIP, z1 - RING_LIP))
    bottom = z0 - RING_BUMP_H if printed else -RING_H + 0.02
    bumps = []
    for i in range(RING_BUMPS):
        (x, y), (tx, ty) = eq_point(2 * math.pi * (i + 0.5) / RING_BUMPS, cp.RING_DEPTH / 2)
        bump = box(-RING_BUMP[0] / 2, RING_BUMP[0] / 2, -RING_BUMP[1] / 2, RING_BUMP[1] / 2, bottom, z0 + 0.05)
        bumps.append(bump.rotate((0, 0, 0), (0, 0, 1), math.degrees(math.atan2(ty, tx))).translate((x, y, 0)))
    return union_all([out] + bumps)


def saddle_placed():
    return col_piece().translate((0, 0, Z_SEAT + SADDLE_GAP))  # dos plat sur l'appui plat du capot


# ================= corps de reference =================

# bas du boitier juste au-dessus des nervures du fond : les deux couches de mousse sont entaillees autour du micro.
# Abaisse de 20 mm le 23 nov. 2026, pour eloigner la bonnette des levres sans allonger le corps (voir AIR_GAP). Le
# disque d'acier est recoupe sous le micro (mic_disc) : la partie qui porte l'aimant ne change pas
MIC_Z0 = FLOOR_TOP + FLOOR_RIB + MIC_CLEARANCE  # 1 mm au-dessus des nervures, comme partout ailleurs
MIC_ZC = MIC_Z0 + v0.MIC_SIZE[1] / 2
MOUNT_FACE_Y = MIC_YC - v0.MIC_SIZE[2] / 2 - v0.MIC_STEEL_DISC_THICKNESS  # face de la plaque qui porte le disque


def mic_box(extra=None):
    """Boitier DJI (cotes de la fiche officielle, 28.58 x 28.04 x 13.52) debout contre le disque, par sa face opposee au
    logo DJI blanc, qui porte l'aimant (Clement, 24 nov. 2026 ; DJI ne publie pas sa position exacte) ; extra = epaisseur d'un clip
    ou d'un aimant entre disque et boitier, qui ecarte le micro de la plaque."""
    e = MIC_STACK_EXTRA if extra is None else extra
    sx, sz, sy = v0.MIC_SIZE
    y0 = MOUNT_FACE_Y + v0.MIC_STEEL_DISC_THICKNESS + e
    return box(MIC_XC - sx / 2, MIC_XC + sx / 2, y0, y0 + sy, MIC_Z0, MIC_Z0 + sz)


def mount_top():
    """Haut de la plaque et du disque : juste sous la jupe de la bonnette, qui coiffe le haut du boitier sur ses
    quatre faces. Montes jusqu'en haut du micro (comme sur le v2), ils empechaient de la mettre en place."""
    return MIC_Z0 + v0.MIC_SIZE[1] - BONNET[2] - 0.5


DISC_CUT_Z = FLOOR_TOP + 0.5  # le disque de 30 mm est recoupe a la cisaille : 0.5 mm au-dessus du fond


def mic_disc():
    """Disque d'acier colle au ras du haut de la plaque, recoupe en bas a DISC_CUT_Z : la bande retiree est toute
    sous le bas du micro, la surface sous l'aimant ne change pas."""
    r = v0.MIC_STEEL_DISC_DIAMETER / 2
    disc = wp(cq.Solid.makeCylinder(r, v0.MIC_STEEL_DISC_THICKNESS, cq.Vector(MIC_XC, MOUNT_FACE_Y, mount_top() - r), cq.Vector(0, 1, 0)))
    return disc.intersect(box(-40, 40, -40, 40, DISC_CUT_Z, 40))


def build_mic_mount():
    """Plaque dressee sur le fond de la chambre (28 x 4 mm, comme le v2), imprimee avec la coque sans support.
    Le disque d'acier se colle sur sa face avant, le micro y tient par son aimant. Tout reste dans
    l'ouverture du capot avant, qui se pose et se retire droit. Pied evase de 2 mm au dos sur 3 mm :
    decoller le micro fait travailler la plaque en flexion, a travers ses couches."""
    y0, y1, zf = MOUNT_FACE_Y - MOUNT_T, MOUNT_FACE_Y, FLOOR_TOP - 0.5
    # evasement au dos seulement : depuis que le micro est abaisse, le disque descend jusqu'au pied cote micro
    prof = [(y0 - 2.0, zf), (y1, zf), (y1, mount_top()),
            (y0, mount_top()), (y0, FLOOR_TOP + 3.0), (y0 - 2.0, FLOOR_TOP)]
    plate = cq.Workplane("YZ", origin=(MIC_XC - MOUNT_W / 2, 0, 0)).polyline(prof).close().extrude(MOUNT_W)
    return plate.edges("|Y and >Z").fillet(v0.MOUNT_EDGE_FILLET)


FINGER_R = {"index": 7.0, "pouce": 8.5}  # demi-epaisseur du bout de doigt d'un adulte (index 14 mm, pouce 17 mm)


def finger(tip, r, length=70.0):
    """Doigt droit et vertical (capsule), bout spherique centre en tip, vers le haut (la main au-dessus du col)."""
    cyl = cq.Solid.makeCylinder(r, length, cq.Vector(*tip), cq.Vector(0, 0, 1))
    ball = cq.Solid.makeSphere(r, cq.Vector(*tip), angleDegrees1=-90, angleDegrees2=90)  # sphere entiere (defaut : moitie)
    return cq.Workplane("XY").newObject([cyl.fuse(ball)])


def bonnet_pinch(squeeze=3.0, below_top=5.0):
    """Pouce et index qui pincent la bonnette par ses flancs x, fourrure ecrasee de `squeeze` mm de chaque cote, a
    `below_top` mm sous le haut des poils. Essai de Clement du 24 nov. 2026 : on tire le micro par sa bonnette, l'aimant
    ne la declipse pas."""
    bb = bonnet_envelope().val().BoundingBox()
    z = bb.zmax - below_top
    return {"pouce": finger((bb.xmin + squeeze - FINGER_R["pouce"], MIC_YC, z), FINGER_R["pouce"]),
            "index": finger((bb.xmax - squeeze + FINGER_R["index"], MIC_YC, z), FINGER_R["index"])}


def bonnet_envelope():
    """Encombrement de la bonnette DJI clipsee sur le haut du boitier (estimation), sans le boitier."""
    w, d, lap, over = BONNET
    bb = mic_box().val().BoundingBox()
    yc = (bb.ymin + bb.ymax) / 2
    # contour ovale : en boite, ses coins fictifs accrochaient deux bossages d'aimant du capot au demontage
    env = eprism(w, d, bb.zmax - lap, bb.zmax + over).translate((MIC_XC, yc, 0))
    return env.cut(mic_box())


def build_liner():
    """Manchon de mousse 9 mm sur les flancs de la chambre avant, piege entre la plaque
    d'appui et le chanfrein du joint. Le micro, au centre, ne le touche plus : bande complete."""
    z0, z1 = FLANGE_TOP + CORBEL_FRONT + 0.3, Z_SEAT - SEAT_PLATE - 0.3
    zs = [s_of(z0)] + [s for s in FRONT_SMOOTH if z0 < z_of(s) < z1] + [s_of(z1)]
    outer = loft_ellipses(sections(sorted(zs, reverse=True), WALL + 0.2))
    inner = loft_ellipses(sections(sorted(zs, reverse=True), WALL + 0.2 + LINER_T))
    # bande d'epaisseur constante (une plaque de 10 mm), sans rognage a l'ouverture : le passage libre est controle
    liner = outer.cut(inner)
    # la couche de 5 mm sur le chanfrein du joint est abandonnee : 8 encoches pour 4 cm3 (0.05 dB(A) au modele)
    return liner.cut(build_front_bosses()).cut(front_screw_cut()).cut(build_col_bosses()).cut(seat_corbel())


def liner_z():
    return FLANGE_TOP + CORBEL_FRONT + 0.3, Z_SEAT - SEAT_PLATE - 0.3


def inlet_notch():
    bb = build_inlet().val().BoundingBox()
    return box(bb.xmin - 3, bb.xmax + 3, -60, bb.ymax + 4, DUCT_BOTTOM - 2, 1)


def disc_layer_shape():
    """Contour d'une couche du fond (decoupe dans une plaque de 10 mm) : ellipse de la cavite a la
    jonction des deux couches, moins 0.5 mm, et une seule encoche droite a 6 h qui degage la plaque
    du micro, le micro lui-meme, le tunnel des fils et l'entree du conduit. Les deux couches sont identiques."""
    zj = FLOOR_TOP + FLOOR_RIB + FOAM_LAYER
    a, b = cavity_half_axes(zj)
    ib = build_inlet().val().BoundingBox()
    half = max(MOUNT_W, v0.MIC_STEEL_DISC_DIAMETER) / 2 + 0.3  # le disque de 30 mm deborde de la plaque de 28
    # l'encoche va jusque devant le micro, qui traverse les deux couches jusqu'aux nervures du fond
    notch = (MIC_XC - half, max(ib.xmax + 1.0, MIC_XC + half), mic_box().val().BoundingBox().ymax + 0.5)
    return a - 0.5, b - 0.5, notch


def disc_layer(z0, h=FOAM_LAYER):
    a, b, (nx0, nx1, ny) = disc_layer_shape()
    return eprism(2 * a, 2 * b, z0, z0 + h).cut(box(nx0, nx1, -60, ny, z0 - 1, z0 + h + 1))


def build_foam_disc(rear=None):
    """Fond en deux couches de 10 mm identiques, entaillees autour du micro ; le corps de reference est la forme posee
    (retaillee par le chanfrein sous le conduit, qui la retient)."""
    z0 = FLOOR_TOP + FLOOR_RIB
    disc = disc_layer(z0).union(disc_layer(z0 + FOAM_LAYER)).intersect(rear_cavity_tool())
    return disc if rear is None else disc.cut(rear)


def build_refs():
    lipo, charger, switch = bay_boxes()
    # shortcut: coussin retaille au contour de l'assise (2 mm de moins par cote), le cylindre de 53 mm ne couvre pas
    # ses 108 mm ; a reprendre si un controle porte un jour sur le bord du coussin
    ring_pad = eprism(*cp.SEAT, Z_SEAT, Z_SEAT + 80).cut(eprism(*PAD["opening"], Z_SEAT - 1, Z_SEAT + 81))
    pad = ring_pad.intersect(cp.below_face(PAD_BASE + PAD["thickness"], SEAT_RADIUS)).cut(cp.below_face(PAD_BASE + SADDLE_GAP, SEAT_RADIUS))
    # rondelle 0.05 mm au-dessus de sa portee, ecrou 0.05 mm sous son plafond (position serree)
    jscrews = union_all(cap_screw_solid(x, y, cp.FRONT_SEAT_Z + 0.05) for x, y in screw_xy())
    wz = -cp.NUT_SKIN - 0.05  # ecrou du joint sans rondelle depuis la v09
    jnuts = union_all(cq.Workplane("XY", origin=(x, y, wz - 2.4)).polygon(6, 6.35).extrude(2.4).rotate((x, y, 0), (x, y, 1), 90)
                      for x, y in screw_xy()).cut(jscrews)
    cscrews = union_all(cover_screw_solid(x, y, COVER_HEAD_Z - 0.05, 1.5) for x, y in COVER_SCREW_XY)
    cnuts = union_all(cq.Workplane("XY", origin=(x, y, COVER_NUT_Z + 0.05)).polygon(6, 6.35).extrude(2.4)
                      for x, y in COVER_SCREW_XY).cut(cscrews)
    return {
        "mic": mic_box(), "mic-disc": mic_disc(), "bonnette": bonnet_envelope(), "earpad": pad,
        "gasket": ring(GROOVE[0] + 0.1, GROOVE[1] - 0.1, TONGUE[2], GROOVE_DEPTH),
        "led-filament": ring(LED_CH[0] + 0.2, LED_CH[1] - 0.2, -LED_CH[2] + 0.1, -0.1),
        "foam-disc": build_foam_disc(), "foam-liner": build_liner(),
        "battery": lipo, "charger": charger, "switch": switch,
        "joint-screws": jscrews, "joint-nuts": jnuts, "cover-screws": cscrews, "cover-nuts": cnuts,
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


def bend_stl(path, dz):
    """Deplace en z chaque sommet d'un STL binaire de dz(x)."""
    raw = path.read_bytes()
    rec = np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    tri = np.frombuffer(raw[84:], dtype=rec).copy()
    tri["v"][..., 2] += dz(tri["v"][..., 0].astype(float))
    path.write_bytes(raw[:84] + tri.tobytes())


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


def duct_metrics(duct, outlet):
    zm = (DUCT_TOP + DUCT_BOTTOM) / 2
    a, b = outer_profile(s_of(zm))
    lap = ellipse_arc_length(a, b, sum(DUCT) / 2)
    channel = lap - DAM
    # entree et sorties reperees en abscisse sur la section du joint, ramenees au tour moyen
    k = lap / CENTER_TABLE[-1][0]
    out_c = sum(OUTLET_S) / len(OUTLET_S)
    inlet_to_first = lap - k * (INLET_S - OUTLET_S[0])
    inlet_to_centroid = lap - k * (INLET_S - out_c)
    area = vol(duct.intersect(box(-0.5, 0.5, 0, 60, -40, 5))) / 1.0
    # section droite des goulottes : coupe horizontale juste sous le plancher du conduit, ramenee a la normale de la pente
    floor_cut = vol(outlet.intersect(box(-70, 70, -70, 0, DUCT_BOTTOM - 0.25, DUCT_BOTTOM - 0.15))) / 0.1
    return {"section_mm2": round(area, 2), "lap_mm": round(lap, 1), "channel_dam_to_dam_mm": round(channel, 1),
            "inlet_to_first_outlet_mm": round(inlet_to_first, 1), "inlet_to_outlet_centroid_mm": round(inlet_to_centroid, 1),
            "inlet_area_mm2": round(INLET_AREA, 1), "outlet_count": OUTLET_COUNT,
            "outlet_floor_opening_mm2": round(floor_cut, 1), "outlet_min_section_mm2": round(floor_cut * OUTLET_SIN, 1),
            "outlet_path_mm": round(sum(chute_edges()) / 2 / math.cos(math.atan(STEEP)), 2), "dam_mm": DAM}


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
    ring_, insert = build_ring(), saddle_placed()
    parts = {"front": front, "rear": rear, "cover": cover, "ring": ring_, "assise-col": insert}
    for n, p in parts.items():
        assert p.val().isValid() and p.solids().size() == 1, n
    # anneau : amincir la paroi lumineuse ne change aucune face de serrage (face haute et nervures, face basse, face
    # exterieure jusqu'a la paroi la plus fine permise)
    thin = build_ring(light=0.8)
    for name, zone in (("haut", box(-90, 90, -90, 90, -0.02 - RING_LIP + 0.05, 1)), ("bas", box(-90, 90, -90, 90, -RING_H - 1, -RING_H + RING_LIFT + RING_LIP - 0.05)),
                       ("exterieur", ring(-1.0, 0.75, -RING_H - 1, 1))):
        assert abs(vol(ring_.intersect(zone)) - vol(thin.intersect(zone))) < 1e-3, f"anneau aminci : face de serrage {name} modifiee"
    t = time.perf_counter()
    refs = build_refs()
    refs["foam-disc"] = build_foam_disc(rear)
    log("corps de reference", t)

    # --- enveloppe et longueur
    body = front.union(rear).union(cover).union(ring_)
    bb = body.val().BoundingBox()
    m = {"profile": PROFILE, "joint_s": JOINT_S,
         "envelope_mm": [round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1)],
         "length_with_collar_mm": round(insert.val().BoundingBox().zmax - bb.zmin, 1),  # crete du col sur les cotes comprise
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
    cav = cav.union(eprism(*COLLAR_INNER, Z_SEAT - cp.FLANGE_T - 0.2, PAD_BASE + COLLAR_HEIGHT))
    # les passages des vis sont exclus du volume d'air : les deux percages coaxiaux de meme rayon (capot, coque)
    # y laissaient une face invalide dans le STEP du volume d'air, refuse par cad/check_exports.py (0.4 cm3 en moins)
    plugs = union_all(cq.Workplane("XY", origin=(x, y, -(cp.SCREW_LEN - cp.BOSS_FRONT_H + 1.1))).circle(cp.SCREW[0] / 2 + 0.05)
                      .extrude(cp.SCREW_LEN - cp.BOSS_FRONT_H + 1.1 + cp.FRONT_SEAT_Z - 0.35) for x, y in screw_xy())
    cav = cav.cut(front).cut(rear).cut(insert).cut(build_tunnel()).cut(refs["mic"]).cut(refs["mic-disc"]).cut(plugs)
    v_cav = vol(cav) / 1000
    foam = {k: vol(refs[k]) / 1000 for k in ("foam-disc", "foam-liner")}
    v_foam = sum(foam.values())
    m["cavity_air_plus_foam_cm3"] = round(v_cav, 1)
    m["cavity_air_only_cm3"] = round(v_cav - v_foam, 1)
    m["foam_cm3"] = {k: round(v, 1) for k, v in foam.items()} | {"total": round(v_foam, 1)}
    assert v_cav >= 170.0, f"cavite {v_cav:.1f} cm3 < 170"  # 185 avant le raccourcissement de 5 mm du 23 nov. 2026
    assert cav.solids().size() >= 1
    # section d'air libre (sans mousse ni pieces) le long de l'axe, de l'entree du conduit au coussin ;
    # la bonnette, en fourrure, laisse passer l'air : elle n'est pas comptee
    air = cav.cut(union_all([refs[k] for k in ("foam-disc", "foam-liner")]))
    z, passage = disc_top() + 0.3, []  # au-dessus du disque ; l'entree reste ouverte par l'entaille du disque
    while z < Z_SEAT - 4.0:
        area_ = 0.0
        for dz in (0.0, 0.07, 0.13):  # une tranche qui frole une face plane peut faire echouer le booleen
            area_ = vol(air.intersect(box(-70, 70, -70, 70, z + dz, z + dz + 0.2))) / 0.2
            if area_ > 0.5 * (passage[-1][1] if passage else MIN_PASSAGE):  # un echec donne une section quasi nulle
                break
        passage.append((round(z, 1), round(area_)))
        z += 1.5
    zmin, amin = min(passage, key=lambda q: q[1])
    m["free_passage_min_mm2"] = {"area": amin, "z": zmin}
    assert amin >= MIN_PASSAGE, (amin, zmin)
    log("cavite et passage libre", t)

    # --- conduit
    t = time.perf_counter()
    duct, outlet = build_duct(), build_outlet()
    dm = duct_metrics(duct, outlet)
    m["duct"] = dm
    print("conduit", dm, flush=True)
    assert 40.0 <= dm["section_mm2"] <= 44.0, dm
    assert dm["channel_dam_to_dam_mm"] >= 175.0, dm
    assert dm["inlet_area_mm2"] >= 48.0 and DAM >= 5.0
    # sortie plus large que le conduit : la masse acoustique reste portee par le conduit, l'air y ralentit
    assert dm["outlet_min_section_mm2"] >= 1.25 * dm["section_mm2"], dm
    # ouvertures reelles : les outils doivent traverser les parois, mesure sur les surfaces qu'ils percent
    z_flat = DUCT_TOP - DUCT_ROOF_H
    inlet = build_inlet()
    z_lip, _, z_s = outlet_lip()
    op = {"sortie_a_la_peau": wall_section(outlet, 0.0, z_lip - 8.0, z_s + 1.0),
          "sortie_au_plancher_du_conduit": dm["outlet_floor_opening_mm2"],
          "entree_a_la_paroi_du_conduit": wall_section(inlet, DUCT[1], DUCT_BOTTOM - 1.0, z_flat),
          "entree_a_la_paroi_de_la_chambre": wall_section(inlet, CAV_JOINT - 0.1, CORBEL_TOP, 0.5)}
    dm["wall_openings_mm2"] = {k: round(v, 1) for k, v in op.items()}
    print("ouvertures", dm["wall_openings_mm2"], flush=True)
    # a la peau, la goulotte coupee en biais et le nez donnent une ouverture plus grande que sa section droite
    assert op["sortie_a_la_peau"] >= 1.2 * dm["outlet_min_section_mm2"], op
    assert all(abs(op[k] / dm["inlet_area_mm2"] - 1) < 0.05 for k in ("entree_a_la_paroi_du_conduit", "entree_a_la_paroi_de_la_chambre")), op
    # et ils debouchent dans les vides : un volume commun franc avec le conduit et la chambre
    assert vol(outlet.intersect(duct)) > 20.0, "sortie borgne"
    assert vol(inlet.intersect(duct)) > 20.0 and vol(inlet.intersect(rear_cavity_tool())) > 20.0, "entree borgne"
    assert vol(duct.intersect(box(-DAM / 2 + 0.01, DAM / 2 - 0.01, -60, 0, -30, 5))) < 1e-6, "barrage"
    if dm["inlet_to_outlet_centroid_mm"] < 175.0:
        warn.append(f"longueur entree -> centre de la sortie {dm['inlet_to_outlet_centroid_mm']} mm < 175 (canal barrage a barrage {dm['channel_dam_to_dam_mm']})")
    log("conduit", t)

    # --- parois minimales (distances 3D entre volumes d'air)
    t = time.perf_counter()
    env = front_env.union(rear_env)
    outside = box(-90, 90, -90, 90, Z_END - 10, Z_SEAT - 1.5).cut(env)
    # sortie exclue des deux cotes : la distance mesuree est alors la paroi autour d'elle
    outside = union_all([outside, ring(0.0, REBATE, -RING_H, 0.01),
                         ring(LED_CH[0], LED_CH[1], -LED_CH[2], 0.01), build_tunnel(), bay_cut().intersect(env)])
    cav_chk = cav.intersect(box(-90, 90, -90, 90, -80, Z_SEAT - 4.5))
    walls = {"cavity_to_outside": min_distance(cav_chk, outside), "duct_to_outside": min_distance(duct, outside),
             "duct_to_cavity": min_distance(duct, cav.cut(inlet)), "outlet_to_cavity": min_distance(outlet, cav.cut(inlet))}
    m["min_wall_mm"] = {k: round(v, 2) for k, v in walls.items()}
    if walls["cavity_to_outside"] < 3.0 - 0.05 or walls["duct_to_outside"] < 3.0 - 0.05:
        fail.append(f"paroi < 3 mm : {m['min_wall_mm']}")
    # paroi entre le micro et l'event : le son qui la traverse court-circuite le conduit
    if walls["duct_to_cavity"] < CAV_JOINT - DUCT[1] - 0.05 or walls["outlet_to_cavity"] < 3.0 - 0.05:
        fail.append(f"paroi micro / event trop fine : {m['min_wall_mm']}")
    log("parois", t)

    # --- micro
    t = time.perf_counter()
    mic, bonnet = refs["mic"], refs["bonnette"]
    clear = {"front": min_distance(mic, front), "insert": min_distance(mic, insert), "liner": min_distance(mic, refs["foam-liner"]),
             "rear_hors_plaque": min_distance(mic, rear.cut(grow(build_mic_mount(), 0.01))), "disque": min_distance(mic, refs["mic-disc"]),
             "bonnette_capot_et_col": min(min_distance(bonnet, front), min_distance(bonnet, insert)),
             "bonnette_plaque_et_disque": min(min_distance(bonnet, rear), min_distance(bonnet, refs["mic-disc"]))}
    # doigts : capot visse, le micro se prend par la bouche, par le haut de sa bonnette (micro abaisse le 23 nov. 2026).
    # De chaque cote de la bonnette, une bande de FINGER mm jusqu'a la crete du col, libre de toute piece rigide ; on
    # mesure de combien elle descend le long de la bonnette avant de toucher le rebord interieur du capot
    bbm = mic.val().BoundingBox()
    z_rim = PAD_BASE + COLLAR_HEIGHT  # crete du col au centre (plus haute sur les cotes)
    top_bonnet = bonnet.val().BoundingBox().zmax
    xb, hard = MIC_XC + BONNET[0] / 2, union_all([front, insert, rear, ring_])
    band = lambda z0: [box(-xb - FINGER, -xb - 0.01, bbm.ymin, bbm.ymax, z0, z_rim), box(xb + 0.01, xb + FINGER, bbm.ymin, bbm.ymax, z0, z_rim)]
    zf0 = bbm.zmax + 1.0
    while zf0 < top_bonnet and max(vol(b.intersect(hard)) for b in band(zf0)) > 0.01:
        zf0 += 0.5
    fingers = {"largeur_mm": FINGER, "prise_le_long_de_la_bonnette_mm": round(top_bonnet - zf0, 1),
               "haut_de_la_bonnette_sous_la_crete_mm": round(z_rim - top_bonnet, 1)}
    # doigts adultes simules (bonnet_pinch) : la pince sur la bonnette, puis la sortie du micro tenu par elle, ne doivent
    # toucher aucune piece rigide ; la fourrure et le manchon sont souples (recouvrement releve)
    rigid_f = {"capot": front, "coque": rear, "col": insert, "anneau": ring_, "micro": mic}
    pinch, pinch_m = bonnet_pinch(), {}
    for fn, f in pinch.items():
        pinch_m[fn] = {"rigide": {n: round(vol(f.intersect(q)), 1) for n, q in rigid_f.items() if vol(f.intersect(q)) > 0.05},
                       "souple": {n: round(vol(f.intersect(q)), 1) for n, q in {"bonnette": bonnet, "manchon": refs["foam-liner"]}.items()
                                  if vol(f.intersect(q)) > 0.05}}
    hand = union_all(list(pinch.values()))
    lift = {d: round(vol(hand.translate((0, 0, d)).intersect(union_all([front, rear, insert, ring_]))), 1) for d in (5.0, 15.0, 30.0, 60.0)}
    fingers["pince_de_la_bonnette"] = {"doigts": pinch_m, "sortie_mm3": lift, "a_mm_sous_le_haut_des_poils": 5.0, "fourrure_ecrasee_mm": 3.0}
    if any(v["rigide"] for v in pinch_m.values()) or max(lift.values()) > 0.05:
        fail.append(f"doigts simules contre une piece rigide : {fingers['pince_de_la_bonnette']}")
    m["mic"] = {"centre": [MIC_XC, round((bbm.ymin + bbm.ymax) / 2, 2), round(MIC_ZC, 2)],
                "clearance_mm": {k: round(v, 2) for k, v in clear.items()}, "stack_extra_mm": MIC_STACK_EXTRA,
                "acces_doigts_par_la_bouche": fingers, "haut_du_micro_au_dessus_du_joint_mm": round(bbm.zmax, 1),
                "sous_le_bord_du_col_mm": {"haut_du_micro": round(z_rim - bbm.zmax, 1),
                                           "haut_de_la_bonnette": round(z_rim - bonnet.val().BoundingBox().zmax, 1)},
                "sous_le_fond_du_coussin_au_centre_mm": {"haut_du_micro": round(PAD_BASE - bbm.zmax, 1),
                                                         "haut_de_la_bonnette": round(PAD_BASE - top_bonnet, 1), "regle_v2": AIR_GAP},
                "bonnette_mm": list(BONNET)}
    assert PAD_BASE - top_bonnet >= AIR_GAP - 0.01, f"bonnette a {PAD_BASE - top_bonnet:.1f} mm sous le fond du coussin, regle du v2 : {AIR_GAP}"
    # le temoin du capot d'essai reproduit cette marge, assise posee a plat ; le col du corps repose depuis le 26 nov. 2026 sur
    # ses diamants, SADDLE_GAP au-dessus de l'appui (0.02 avant) : 0.48 mm de plus, sans effet sur l'essai deja fait
    assert abs(PAD_BASE - top_bonnet - cp.GAUGE_GAP - (SADDLE_GAP - 0.02)) < 0.1, f"temoin de bonnette a {cp.GAUGE_GAP} mm, corps a {PAD_BASE - top_bonnet:.1f}"
    assert min(clear["front"], clear["insert"], clear["rear_hors_plaque"], clear["bonnette_capot_et_col"]) >= MIC_CLEARANCE - 0.01, clear
    assert clear["bonnette_plaque_et_disque"] >= 0.4, clear
    assert fingers["prise_le_long_de_la_bonnette_mm"] >= 8.0, fingers
    log("micro", t)

    # --- joint et vis
    t = time.perf_counter()
    # les percages ne doivent rien crever : ni l'exterieur, ni la rainure du joint, ni le conduit, ni la baie
    fs, rs, pil = front_screw_cut(), rear_screw_cut(), cover_nut_cut()
    gaps = {"capot_vers_exterieur": min_distance(fs, outside), "capot_vers_rainure": min_distance(fs, ring(GROOVE[0], GROOVE[1], -1, GROOVE_DEPTH)),
            "capot_col_vers_exterieur": min_distance(col_screw_cut_front(), outside),
            "coque_vers_exterieur": min_distance(rs, outside), "coque_vers_conduit": min_distance(rs, duct),
            "trappe_vers_exterieur": min_distance(pil, box(-90, 90, -90, 90, Z_END - 10, Z_SEAT - 1.5).cut(env)), "trappe_vers_chambre": min_distance(pil, cav)}
    m["screw_walls_mm"] = {k: round(v, 2) for k, v in gaps.items()}
    assert min(gaps["capot_vers_exterieur"], gaps["coque_vers_exterieur"], gaps["coque_vers_conduit"], gaps["trappe_vers_chambre"]) >= 1.5, m["screw_walls_mm"]
    assert gaps["capot_vers_rainure"] >= 0.9 and gaps["trappe_vers_exterieur"] >= 1.5, m["screw_walls_mm"]
    assert gaps["capot_col_vers_exterieur"] >= 1.0, m["screw_walls_mm"]
    # siege des vis de la trappe : 1 mm de matiere autour de la tete sur toute la hauteur sous le puits
    seat = union_all(cq.Workplane("XY", origin=(x, y, COVER_HEAD_Z)).circle(cp.HEAD_WELL_R + 1.0).extrude(Z_RF - COVER_HEAD_Z) for x, y in COVER_SCREW_XY)
    m["cover_seat_fill"] = round(vol(seat.intersect(build_cover(rear_env, holes=False))) / vol(seat), 4)
    assert m["cover_seat_fill"] > 0.999, "siege d'une vis de trappe au bord de la peau"
    # pose : un cylindre du diametre de la rondelle (+ 0.2), de chaque portee jusqu'au-dela du col, ne rencontre ni le
    # capot ni le manchon : vis et rondelle descendent jusqu'a leur portee, col retire
    z_s, z_top = cp.FRONT_SEAT_Z + 0.05, cp.FRONT_SEAT_Z + cp.WASHER[1] + cp.CAP_HEAD[1] + 0.05
    driver = union_all(cq.Workplane("XY", origin=(x, y, z_s)).circle(cp.WASHER_WELL_R - 0.1).extrude(z_rim + 5.0 - z_s)
                       for x, y in screw_xy())
    # cle six pans de 2.5 mm (2.9 sur angles, comptee a 3.2) : elle atteint chaque tete a travers le col en place,
    # pour rouvrir sans decoller le coussin ; les vis desserrees restent dans leurs puits
    key = union_all(cq.Workplane("XY", origin=(x, y, z_top)).circle(1.6).extrude(z_rim + 5.0 - z_top) for x, y in screw_xy())
    acc = {"capot": vol(driver.intersect(front)), "manchon": vol(driver.intersect(refs["foam-liner"])), "col_en_place_info": vol(driver.intersect(insert)),
           "cle_2_5mm_col_en_place": vol(key.intersect(union_all([front, insert, refs["foam-liner"]]))),
           "cle_2_5mm_jeu_au_col_mm": min_distance(key, insert)}
    m["gasket_compression_mm"] = round(comp, 2)
    # vis serrees : la pointe d'une M3 x 12 doit depasser l'ecrou d'un filet au moins, sans toucher le fond du percage
    nut_low = {"joint": -cp.NUT_SKIN - 2.4, "col": col_nut_z()[1] - cp.WASHER[1] - 2.4}
    tip = {"joint": cp.FRONT_SEAT_Z + cp.WASHER[1] - cp.SCREW_LEN,
           "col": col_screw_tip_z()}
    hole_low = {"joint": -(cp.SCREW_LEN - cp.BOSS_FRONT_H + 1.0), "col": col_screw_tip_z() - 0.8}
    m["screws"] = {"joint": len(screw_xy()), "trappe": len(COVER_SCREW_XY), "acces_tournevis_obstacle_mm3": {k: round(v, 2) for k, v in acc.items()},
                   "pointe_sous_l_ecrou_mm": {k: round(nut_low[k] - tip[k], 2) for k in tip},
                   "pointe_au_fond_du_percage_mm": {k: round(tip[k] - hole_low[k], 2) for k in tip}}
    assert acc["capot"] < 0.01 and acc["manchon"] < 0.01 and acc["cle_2_5mm_col_en_place"] < 0.01 and acc["cle_2_5mm_jeu_au_col_mm"] >= 1.0, acc
    assert all(1.0 <= nut_low[k] - tip[k] and tip[k] - hole_low[k] >= 0.3 for k in tip), m["screws"]
    # trappe, vis vers +z : pointe serree au-dessus de l'ecrou tire sur son plancher, et sous le plafond du logement
    c_tip = COVER_HEAD_Z + cp.SCREW_LEN
    m["screws"]["trappe_pointe_au_dessus_de_l_ecrou_mm"] = round(c_tip - (COVER_NUT_Z + 2.4), 2)
    m["screws"]["trappe_pointe_sous_le_plafond_mm"] = round(COVER_NUT_Z + COVER_NUT_H - c_tip, 2)
    assert c_tip - (COVER_NUT_Z + 2.4) >= 1.0 and COVER_NUT_Z + COVER_NUT_H - c_tip >= 0.3, m["screws"]
    # col : 1 mm de col plein autour du puits de chaque vis, du dos jusqu'au haut de la tete, et la tete sous l'assise
    body = cp.body_saddle()
    hh = COL_SEAT_Z + cp.WASHER[1] + cp.CAP_HEAD[1]
    shell_ = union_all(cq.Workplane("XY", origin=(x, y, 0)).circle(cp.WASHER_WELL_R + 1.0).circle(cp.WASHER_WELL_R).extrude(hh)
                       for x, y in col_screw_xy())
    m["col_screw_wall_fill"] = round(vol(shell_.intersect(body)) / vol(shell_), 4)
    assert m["col_screw_wall_fill"] > 0.999, "puits d'une vis du col au bord du col, ou tete au-dessus de l'assise"
    assert len(screw_xy()) == 4 and refs["joint-screws"].solids().size() == 4 and refs["joint-nuts"].solids().size() == 4
    assert refs["cover-screws"].solids().size() == 2 and refs["cover-nuts"].solids().size() == 2
    log("vis", t)

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
            if v > 0.005:  # mm3 : a 0.1, un vrai contact pied du micro / capot avant (0.03 mm3) passait
                hits.append((a, b, round(v, 3)))
    m["interferences"] = hits
    assert not hits, hits
    # demontage : chaque piece retiree au quotidien doit sortir en translation droite. Le 21 nov. 2026, sans
    # aucune interference au repos, la tete du pied et le micro debordaient de 5.5 mm au-dessus du corbeau
    # du capot avant : capot ni posable ni retirable (trouve par une relecture independante des STL).
    steps = (1.0, 2.0, 4.0, 8.0, 14.0, 22.0, 32.0, 45.0, 60.0)
    stays = union_all([rear, refs["mic"], refs["mic-disc"], refs["bonnette"]])
    mic_on = refs["mic"].union(refs["bonnette"])
    held = union_all([rear, refs["mic-disc"], front, insert])
    # capot visse : le micro, bonnette en place, sort droit par la bouche, ou se decolle d'abord du disque
    # vers l'avant (+y), ou 4 mm suffisent a liberer l'aimant
    pulls = {"capot_avant_et_col_micro_en_place": (front.union(insert), stays, (0, 0, 1)),
             "micro_et_bonnette_par_la_bouche": (mic_on, held, (0, 0, 1)), "micro_et_bonnette_decolles": (mic_on, held, (0, 1, 0)),
             "trappe": (cover, rear, (0, 0, -1))}
    m["demontage_volume_commun_mm3"] = {k: {d: round(vol(p.translate(tuple(c * d for c in u)).intersect(q)), 2)
                                            for d in steps if u[1] == 0 or d <= 4.0} for k, (p, q, u) in pulls.items()}
    for k, v in m["demontage_volume_commun_mm3"].items():
        if max(v.values()) > 0.05:
            fail.append(f"demontage bloque ({k}) : {max(v.values())} mm3 communs pendant le retrait")
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
    written = {}
    for n, p in parts.items():
        written[n] = cp.export_step(p, out / f"{stem}-{n}.step")
    membranes = print_membranes()  # premiere couche pleine des plafonds de rondelle d'ecrou, percee au montage
    # STL en orientation d'impression : capot appui en bas, coque face arriere en bas,
    # couvercle face plane en bas, anneau et collier a plat.
    printed = {
        # retourne depuis le 26 nov. 2026 : joint sur le plateau, appui et diamants en haut. Une copie : mailler le capot
        # lui-meme pour le STL accrochait le maillage a ses faces, que partage le volume d'air, dont le STEP ne se relisait plus
        "front": wp(front.union(membranes["front"]).val().copy()),
        "rear": rear.union(membranes["rear"]).translate((0, 0, -Z_RF)),
        "cover": cover.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, Z_RF)),
        # retourne : face haute (contre le capot) sur le plateau, plots imprimes en dernier
        "ring": build_ring(printed=True).rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, -0.02)),
        "assise-col": col_piece(),
    }
    for n, p in printed.items():
        pb = p.val().BoundingBox()
        assert abs(pb.zmin) < 0.05 and pb.xlen <= 180 and pb.ylen <= 180 and pb.zlen <= 180, (n, pb.zmin)
        cq.exporters.export(p, str(out / f"{stem}-{n}.stl"), tolerance=LIN_TOL, angularTolerance=ANG_TOL)
        cp.clean_stl(out / f"{stem}-{n}.stl")
    air = cav.union(duct).union(build_inlet()).union(build_outlet())
    air_written = cp.export_step(air, out / f"{stem}-air-volume.step")
    temoin = temoin_pieces(front)
    cdir = out / "coupons"
    for n, p in temoin.items():
        assert p.val().isValid() and p.solids().size() == 1, f"temoin {n}"
        lay = p.translate((0, 0, -p.val().BoundingBox().zmin))
        cq.exporters.export(lay, str(cdir / f"temoin-diamant-{n}.stl"), tolerance=LIN_TOL, angularTolerance=ANG_TOL)
        cp.clean_stl(cdir / f"temoin-diamant-{n}.stl")
    m["temoin_diamant_cm3"] = {n: round(vol(p) / 1000, 2) for n, p in temoin.items()}
    # corps de reference : meme controle de relecture (joint, filament LED et fond de mousse passent en NURBS)
    with tempfile.TemporaryDirectory() as tmp:
        ref_written = {n: cp.export_step(p, Path(tmp) / f"{n}.step") for n, p in refs.items()}
    assembly = cq.Assembly(name=f"{stem}-technical")
    # pieces imprimees opaques et de couleurs distinctes : en revue (Onshape), des coques transparentes
    # donnent l'impression de voir a travers la paroi
    colors = {"front": (0.35, 0.50, 0.65, 1.0), "rear": (0.80, 0.55, 0.10, 1.0), "cover": (0.30, 0.30, 0.32, 1.0),
              "ring": (0.92, 0.92, 1.0, 0.6), "assise-col": (0.20, 0.20, 0.22, 1.0)}
    for n, p in parts.items():
        assembly.add(written[n], name=n, color=cq.Color(*colors[n]))
    for n, p in refs.items():
        assembly.add(ref_written[n], name=f"ref-{n}", color=cq.Color(0.6, 0.6, 0.65, 0.6))
    assembly.add(air_written, name="air-cavity-and-duct", color=cq.Color(0.1, 0.7, 0.95, 0.25))
    assembly.export(str(out / f"{stem}-technical.step"))
    n_step = cp.step_solids(out / f"{stem}-technical.step").solids().size()
    n_expected = sum(b.solids().size() for b in list(parts.values()) + list(refs.values()) + [air])
    assert n_step == n_expected, f"assemblage STEP relu en {n_step} solides au lieu de {n_expected}"
    log("exports STEP/STL", t)

    # --- web : STL grossiers et manifeste
    t = time.perf_counter()
    # eclate = ordre de montage : baie par l'arriere, le reste par le plan de joint, le micro en dernier par la bouche
    roles = {"front": ("Capot avant", "black", (0, 0, 135)), "rear": ("Coque arriere", "black", (0, 0, 0)),
             "cover": ("Couvercle de la baie", "black", (0, 0, -62)), "ring": ("Anneau lumineux", "translucent", (0, 0, 10)),
             "assise-col": (f"Assise courbe et col {COLLAR_HEIGHT:g} mm", "black", (0, 0, 150)),
             "mic": ("DJI Mic Mini 2", "electronics", (0, 0, 250)), "mic-disc": ("Disque acier 30 mm, recoupe en bas", "metal", (0, 0, 62)),
             "earpad": ("Coussin Brainwavz", "soft", (0, 0, 175)), "gasket": ("Joint mousse 3 x 2", "soft", (0, 0, 128)),
             "led-filament": ("Filament LED", "electronics", (0, 0, 5)), "foam-disc": ("Fond de mousse, 2 couches de 10 mm entaillees", "foam", (0, 0, 45)),
             "foam-liner": ("Manchon de mousse 10 mm", "foam", (0, 0, 100)), "foam-liner-rear": ("Mousse des flancs arriere 8 mm", "foam", (0, 0, 58)),
             "bonnette": ("Bonnette DJI (encombrement estime)", "soft", (0, 0, 250)),
             "battery": ("LiPo 30 x 20 x 5", "electronics", (0, 0, -26)), "charger": ("Chargeur USB-C TP4056", "electronics", (0, 0, -44)),
             "switch": ("Interrupteur", "electronics", (0, 0, -44)), "joint-screws": ("Vis M3 x 12 a tete cylindrique du joint, sur rondelle", "metal", (0, 0, 160)),
             "joint-nuts": ("Ecrous M3 du joint", "metal", (0, 0, 0)), "cover-screws": ("Vis M3 x 12 a tete cylindrique de la trappe", "metal", (0, 0, -80)),
             "cover-nuts": ("Ecrous M3 de la trappe", "metal", (0, 0, 0))}
    manifest = []
    shown = dict(parts) | refs | {"earpad": web_earpad()}
    for n, p in shown.items():
        f = web / f"{n}.stl"
        tol = WEB_TOL_FINE if n in ("front", "rear", "cover") else WEB_TOL
        if n == "assise-col":  # bord arrondi de l'assise : en maillage fin, 2.4 Mo
            tol = (0.15, 0.3)
        cq.exporters.export(p, str(f), tolerance=tol[0], angularTolerance=tol[1])
        if n == "earpad":  # coussin arrondi a plat sur son fond ; la page le pose sur l'assise courbe (padZ de galet-cao.html)
            bend_stl(f, lambda x: PAD_BASE - Z_SEAT + 0 * x)
        assert f.stat().st_size < 1.5e6, (n, f.stat().st_size)
        label, role, ex = roles[n]
        manifest.append({"file": f.name, "label": label, "role": role, "explode": list(ex)})
    for n, p in temoin.items():  # en position de montage ; la page les montre seuls, bouton Fixation du col
        f = web / f"temoin-diamant-{n}.stl"
        cq.exporters.export(p.translate((0, 0, Z_SEAT + SADDLE_GAP) if n == "col" else (0, 0, 0)), str(f), tolerance=0.1, angularTolerance=0.3)
        manifest.append({"file": f.name, "label": f"Temoin du col : {n}", "role": "coupon", "explode": [0, 0, 0]})
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
