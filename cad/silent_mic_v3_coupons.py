# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright 2026 Clement Barberousse
"""Silent Mic v3 galet : eprouvettes a imprimer avant le corps.

- un capot d'essai du coussin d'oreillette et des assises courbes a col (SADDLE_COLLARS) ;
- eprouvette de joint (deux moities, deux vis M3 a ecrou prisonnier, rainure de mousse) ;
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
import whisper_mask_v2_screwed as v2


# ---------- coussin d'oreillette ----------
# Montage v0/v2 eprouve : l'ouverture du coussin s'enfile sur un collier rigide.
PADS = {
    # mesure par Clement sur son coussin le 23 nov. 2026 (fiche : 110 x 90, ouverture 70 x 50, 30 mm)
    "brainwavz": {"outer": (108.0, 81.0), "opening": (72.6, 48.5), "thickness": 28.0},
    # Type Sony MDR-7506, cotes de fiches vendeur, non verifiees sur piece.
    "small-oval": {"outer": (100.0, 81.0), "opening": (60.0, 40.0), "thickness": 20.0},
}
PAD = PADS["brainwavz"]
PAD_CLEARANCE = 1.0  # jeu par cote entre col et ouverture du coussin : col interieur 66.6 x 42.5
COLLAR_WALL = 2.0
COLLAR_ROUND = 0.95  # arrondi du sommet, quasi demi-rond sur 2 mm
SEAT = (104.0, 77.0)  # appui du coussin : 2 mm sous le coussin de chaque cote (demande de Clement, le plus compact)
MIN_COLLAR_INNER = (62.0, 42.0)


def collar_outer(pad=PAD):
    return tuple(s - 2 * PAD_CLEARANCE for s in pad["opening"])


def collar_inner(pad=PAD):
    return tuple(s - 2 * COLLAR_WALL for s in collar_outer(pad))


# ---------- joint ----------
RING_DEPTH, RING_H = 2.5, 2.8  # anneau translucide visible
REBATE = 2.6
LED_CH = (2.6, 5.0, 2.2)  # offsets et profondeur de la rainure du filament LED
# languette (coque arriere) : offsets et hauteur. v10 : 2.4 de large au lieu de 2.8 et recentree vers l'interieur, pour
# 0.35 mm de jeu par cote (0.1 puis 0.2 coincaient) sans manger l'appui exterieur entre la rainure LED et la rainure
TONGUE = (6.55, 8.95, 2.0)
# rainure du capot avant. Essai du 27 nov. 2026 (Clement) : a 0.2 mm de jeu, la languette butait a l'entree (premiere
# couche ecrasee du capot, imprime joint au plateau) et le capot basculait vers les vis autour de l'appui exterieur,
# trop etroit (0.9 mm). Depuis la v10 : 0.35 mm de jeu, appui de 1.2 mm (controle dans check()). Pas de marche ni de
# chanfrein a l'entree (GROOVE_CHAMFER vide) : en v10-v12, une marche de 0.2 mm y faisait poser par Bambu Studio des
# supports sur tout le tour de la rainure du capot, impossibles a retirer (G-code de la plaque 2)
GROOVE = (6.2, 9.3)
GROOVE_CHAMFER = ()
GASKET = (3.0, 2.0)  # bande de mousse a cellules fermees
GASKET_COMPRESSION = 0.55
GROOVE_DEPTH = TONGUE[2] + GASKET[1] - GASKET_COMPRESSION

# ---------- vis ----------
# Le capot avant et la trappe se vissent (decision de Clement du 23 nov. 2026 : seul le micro, retire tous
# les jours, tient par aimant). Vis M3 fraisees et ecrous prisonniers aux cotes du v2, deja imprime et monte.
# passage, tete, hauteur de fraisure. Fraisure a 90 deg, comme la tete d'une vis ISO 10642 : a 72 deg (cotes du
# v2), la tete ne portait que sur l'arete du haut (relecture independante du 23 nov. 2026)
SCREW = (v2.M3_CLEARANCE_DIAMETER, v2.M3_HEAD_DIAMETER, (v2.M3_HEAD_DIAMETER - v2.M3_CLEARANCE_DIAMETER) / 2)
# logement d'ecrou : sur angles, hauteur du niveau de l'ecrou (2.4 + 0.1 de jeu). Au-dessus, le niveau de la rondelle
# (WASHER_LEVEL), sous un plafond imprime en pont : c'est lui qui flechit, d'ou ses 0.3 mm de jeu
NUT = (v2.M3_NUT_POCKET_DIAMETER, 2.5)
SCREW_LEN = 12.0  # M3 x 12 sous la tete (ISO 4762) : la boite de Clement n'a que des 6 et des 12, pas de 10 (27 nov. 2026)
# axe des vis depuis la peau : a l'interieur de la rainure, rien ne traverse la paroi. A 13.9, une cle six pans
# de 2 mm atteint chaque tete a travers le col en place (controle dans le corps) : on rouvre sans decoller le coussin
SCREW_OFFSET = 13.9
BOSS_R = 5.0  # bossage rond de la coque arriere et des ecrous du col (6 : le micro, decolle de son aimant, l'accrochait)
BOSS_HALF, BOSS_FAR = 4.6, 4.3  # bossage du capot : demi-largeur, et avancee vers la chambre depuis l'axe
# et celui de la rondelle jusque-la : au-dela, ses parois tombent sous 0.5 mm ; la rondelle y perd 3 mm2 d'appui sur 28
# bossage du capot : 3.7 mm de matiere sous la fraisure. A 4.5, presque au niveau du dessus de la bride du
# capot (4.45), OCCT rendait un capot invalide
BOSS_FRONT_H = 5.0
NUT_SKIN = 1.2  # entre la rondelle et le plan de joint : pont de 7.6 mm, 6 couches
HEAD_WELL_R = SCREW[1] / 2 + 0.2  # puits de la tete et du tournevis (trappe)
# Joint et col (Clement, 26 nov. 2026) : vis a tete cylindrique ISO 4762 M3 x 12 de sa boite, une rondelle plate
# ISO 7089 M3 sous la tete et une sur l'ecrou du col. Sous la tete, la rondelle porte a plat sur 28 mm2 au lieu des 13 mm2
# projetes d'une fraisure, sans l'effet de coin d'un cone qui ouvre le bossage. Cote ecrou du col (peau en poinconnement),
# elle porte sur 28 mm2 au lieu de 16 sous l'ecrou seul. Plus de rondelle sur l'ecrou du joint depuis la v09 (essai du
# 27 nov. 2026 : elle n'entrait qu'en forcant et soulevait la languette de 0.7 mm entre le trou de vis et sa fente) : la
# peau y est ecrasee contre le bossage du capot, en compression, l'ecrou seul suffit. Le logement six pans empeche l'ecrou
# de tourner, sans pince (essai du 27 nov. 2026 : il entre et ne tourne pas).
WASHER = (7.0, 0.5)  # diametre exterieur, epaisseur
CAP_HEAD = (5.5, 3.0)  # tete cylindrique : diametre, hauteur ; cle six pans de 2.5
WASHER_WELL_R = WASHER[0] / 2 + 0.3  # logements de rondelle : les trous sortent 0.3 a 0.4 mm plus petits (temoins du 26 nov.)
WASHER_LEVEL = WASHER[1] + 0.6  # niveau de la rondelle d'ecrou du col, sous la peau : 0.8 coinçait la rondelle a l'essai du 27 nov.
FRONT_SEAT_Z = BOSS_FRONT_H - 1.0  # portee plate de la rondelle dans le bossage du capot, 4 mm au-dessus du joint
# nervures du bossage du capot : 0.8 mm (1.3 avec le puits de 6.6 de la fraisure). Les elargir faisait toucher le pouce
# qui sort le micro (controle du corps) ; elles ne portent pas le serrage, qui passe du bossage au plan de joint
BOSS_REAR_H = NUT_SKIN + NUT[1] + 2.0
MEMBRANE = 0.2  # une couche pleine sur le plafond des logements de rondelle d'ecrou, percee au montage
PILOT_D = 2.7  # avant-trou d'une M3 qui taille son filet dans le PLA (trappe, hors volume acoustique)

# ---------- assise courbe et col (23 nov. 2026) ----------
# Clement : sur le v2 imprime, ses levres descendent un peu sous le fond du coussin, et l'assise du v2, creusee
# en cylindre de 105 mm (axe vertical), fait epouser les joues au coussin. L'assise se rapporte sur l'appui plat
# du capot (ruban double face, comme le coussin) : le capot garde son impression appui au plateau, sans support.
FACE_RADIUS = v0.FACE_RADIUS
SADDLE_T0 = 4.0  # epaisseur au centre, sous la bouche : le fond du coussin monte d'autant
# hauteur du col au-dessus du fond du coussin, au centre. La crete suit la courbe : plus haute sur les cotes,
# ou le coussin plie moins (idee de Clement). Coussin de 30 mm, environ 15 une fois comprime (Clement).
# (hauteur du col, rayon de l'assise). Essai du 24 nov. 2026 sur l'assise de 10 mm / 105 : taille juste, mais
# pas assez courbee, et col a monter a 20 mm au moins (Clement). 85 : un peu plus courbe, 70 : nettement plus.
SADDLE_COLLARS = ((10.0, FACE_RADIUS), (20.0, 85.0), (20.0, 70.0))
# Essai du 24 nov. 2026 sur l'assise de 20 mm / 85 : bords encore a relever d'environ 12 mm (Clement). Plutot que
# reimprimer l'assise, deux cales posees dessus, une de chaque cote, sous le coussin : dessous au rayon de l'assise
# imprimee, dessus au rayon qui releve son bord de SHIM_RISE (60 mm environ), celui de l'assise suivante si ca plait.
# Puis encore 12 mm (Clement, meme jour) : une seconde paire se pose sur la premiere (dessus au rayon 53). SHIM_LAYERS
# paires empilees, chacune dessous au rayon du dessus de la precedente.
SHIM_ON, SHIM_RISE, SHIM_MIN, SHIM_CLEAR, SHIM_LAYERS = 85.0, 12.0, 1.0, 0.5, 2

# temoin de bonnette (idee de Clement, 23 nov. 2026) : pose au fond du capot d'essai, sous l'assise, son dessus est a
# la hauteur du haut de la bonnette dans le corps, GAUGE_GAP sous le fond du coussin. On appuie le visage comme pour
# parler : si les levres le touchent, la bonnette les toucherait. Des cales dessous (pieces, rondelles) mesurent la
# marge reelle. GAUGE_GAP doit egaler la marge du corps (controle dans silent_mic_v3_galet.py)
GAUGE_GAP = 13.0
GAUGE_SIZE = (36.0, 26.0)  # encombrement estime de la bonnette DJI, comme BONNET dans le corps

# ---------- capots d'essai ----------
CAP_DEPTH = 28.0  # interieur derriere l'appui : DJI 28.6 x 28 x 13.5 a plat + ecouteur
CAP_WALL = 3.0
CABLE_PORT = 5.5
FLANGE_T, FLANGE_W, FLANGE_GAP = 1.2, 9.0, 0.2  # bride du collier amovible

LIGHT_STEPS = (0.8, 1.2, 1.6, 2.0, 2.4)
LIN_TOL, ANG_TOL = 0.02, 0.1  # a 0.1 / 0.3, le maillage de l'assise courbe gravee restait ouvert (58 aretes)


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


def _lbox(x0, x1, half_y, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, 2 * half_y, z1 - z0, centered=(False, True, False)).translate((x0, 0, z0))


def screw_hole_front(x, y, top, angle):
    """Cote tete (capot avant, tete vers +z) : passage, portee plate de la rondelle a FRONT_SEAT_Z, puis puits de
    la rondelle, de la tete et de la cle jusqu'a top, ouvert vers la chambre (direction angle, en degres).
    Capot et eprouvette s'impriment joint au plateau : la portee est un fond plat, sans pont. Jusqu'au 27 nov. 2026,
    l'ancienne astuce de pont (fente et carre de 0.2 mm sous la portee, pour une impression joint en haut) y
    laissait une rainure de 3.6 mm sous la rondelle : 14.4 mm2 d'appui au lieu de 28.3."""
    r, rw, s = SCREW[0] / 2, WASHER_WELL_R, FRONT_SEAT_Z
    local = (cq.Workplane("XY", origin=(0, 0, -0.5)).circle(r).extrude(s + 0.5)
             .union(cq.Workplane("XY", origin=(0, 0, s)).circle(rw).extrude(top - s))
             .union(_lbox(0, BOSS_FAR + 1.0, rw, s, top)))  # puits ouvert vers la chambre, entre les nervures
    return local.rotate((0, 0, 0), (0, 0, 1), angle).translate((x, y, 0))


def screw_hole_rear(x, y, angle):
    """Cote ecrou (coque arriere) : passage de la vis sous le plan de joint et logement d'ecrou M3, ouvert de cote
    (direction angle, en degres) : on y glisse l'ecrou, sans rondelle depuis la v09. Le serrage ecrase la peau de
    NUT_SKIN entre l'ecrou et le bossage d'en face : rien ne travaille en traction a travers les couches.
    La peau s'imprime en pont au-dessus de l'ecrou. Sa premiere couche (MEMBRANE) est pleine (nut_membrane, seulement
    dans le STL d'impression), on la perce au montage, avant les ecrous. Depuis la v11, cette peau couvre toute la
    fente jusqu'au bord du bossage (Clement, 27 nov. 2026) : jusqu'a la v10, elle s'arretait a 3.3 mm de l'axe, de peur
    que le pont de 5.8 mm ne tienne pas sur les parois amincies du bossage rond ; un pont de 5.8 mm s'imprime sans
    peine, et le dessus du bossage est maintenant un disque plein face au capot."""
    r, R = SCREW[0] / 2, BOSS_R
    depth = SCREW_LEN - BOSS_FRONT_H + 1.0
    z1 = -NUT_SKIN
    z0 = z1 - NUT[1]
    half = NUT[0] * math.cos(math.radians(30)) / 2
    local = (cq.Workplane("XY", origin=(0, 0, -depth)).circle(r).extrude(depth + 0.5)
             .union(cq.Workplane("XY", origin=(0, 0, z0)).polygon(6, NUT[0]).extrude(NUT[1]))  # un angle vers la fente
             .union(_lbox(0, R + 0.5, half, z0, z1)))
    return local.rotate((0, 0, 0), (0, 0, 1), angle).translate((x, y, 0))


def nut_membrane(x, y, z_ceiling):
    """Premiere couche pleine du plafond d'un logement de rondelle d'ecrou, a remettre dans le STL d'impression ; les
    pieces et l'assemblage restent perces (etat monte)."""
    return cq.Workplane("XY", origin=(x, y, z_ceiling)).circle(SCREW[0] / 2 + 0.05).extrude(MEMBRANE)


def pilot_hole(x, y, z0, depth):
    """Avant-trou borgne ouvert vers -z (face posee sur le plateau), fond en pointe a 45 deg : a fond plat, le
    trancheur y pose un support impossible a retirer."""
    r = PILOT_D / 2
    tip = cq.Workplane("XY").newObject([cq.Solid.makeCone(r, 0.0, r, cq.Vector(x, y, z0 + depth), cq.Vector(0, 0, 1))])
    return cq.Workplane("XY", origin=(x, y, z0 - 0.5)).circle(r).extrude(depth + 0.5).union(tip)


def step_ready(shape):
    """Toutes les surfaces en NURBS, pour un STEP que les autres logiciels savent relire."""
    from OCP.BRepBuilderAPI import BRepBuilderAPI_NurbsConvert
    return cq.Workplane("XY").newObject([cq.Shape.cast(BRepBuilderAPI_NurbsConvert(shape.val().wrapped, True).Shape())])


def step_solids(path):
    """Relit un STEP."""
    return cq.importers.importStep(str(path))


def export_step(shape, path):
    """Ecrit le STEP et le relit : il doit redonner les memes solides fermes.
    Ecrit tel quel, le STEP de la coque arriere et du capot avant perdait les faces reglees sur des
    courbes decalees (gorge, fentes, entree du conduit, rainures) : relu, ce n'etait plus un solide,
    et Onshape l'importait en surfaces ouvertes (constate le 20 nov. 2026). Dans ce cas on reecrit en
    NURBS : memes surfaces (ecart mesure nul), mais le volume qu'OCCT recalcule dessus varie jusqu'a
    1 %, d'ou la tolerance. Renvoie la forme reellement ecrite, a reutiliser dans l'assemblage.
    Volumes en integration precise : sur l'assise arrondie de 2 mm, l'integration par defaut donnait 2,4 %
    d'ecart au STEP en NURBS, et 1,6e-4 au STEP brut, pour des maillages identiques a 0,3 % pres (24 nov. 2026)."""
    n0, v0 = shape.solids().size(), vol_precise(shape)
    for ready, tol in ((shape, 1e-4), (step_ready(shape), 1e-2)):
        cq.exporters.export(ready, str(path))
        back = step_solids(path)
        if back.solids().size() == n0 >= 1 and abs(vol_precise(back) - v0) <= tol * v0:
            return ready
    raise AssertionError(f"{Path(path).name} : STEP relu en {back.solids().size()} solide(s) au lieu de {n0}, volume {vol_precise(back):.0f} au lieu de {v0:.0f}")


def vol_precise(w, eps=1e-7):
    from OCP.GProp import GProp_GProps
    from OCP.BRepGProp import BRepGProp
    total = 0.0
    for s in w.solids().vals():
        p = GProp_GProps()
        BRepGProp.VolumeProperties_s(s.wrapped, p, eps)
        total += p.Mass()
    return total


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


def face_sag(x, radius=FACE_RADIUS):
    """Avancee de l'assise vers le visage a l'abscisse x, par rapport au centre."""
    return radius - math.sqrt(radius ** 2 - x * x)


def below_face(depth, radius=FACE_RADIUS):
    """Tout ce qui est sous la surface cylindrique de rayon `radius` (axe vertical y) dont le creux est a z = depth."""
    zc = depth + radius
    cyl = cq.Solid.makeCylinder(radius, 300, cq.Vector(0, -150, zc), cq.Vector(0, 1, 0))
    return cq.Workplane("XY").box(300, 300, zc + 100, centered=(True, True, False)).translate((0, 0, -100)).cut(cq.Workplane("XY").newObject([cyl]))


# deg : au-dela, le dessus de l'assise continue en droite. 60 deg : courbe R53 intacte jusqu'a x = 46, sous toute la
# ligne d'appui du coussin (x = 45), et pointe assez ouverte (30 deg) pour un arrondi de 2 mm (Clement, 24 nov. 2026 :
# bords bien arrondis dans l'epaisseur). A 70 deg et 1 mm, la pointe n'etait qu'une levre de 2 mm, a 39,7 mm.
SEAT_MAX_SLOPE = 60.0


def below_face_capped(depth, radius, slope_deg=SEAT_MAX_SLOPE):
    """Comme below_face, mais l'arc s'arrete a la pente `slope_deg` et se prolonge par sa tangente."""
    s = math.radians(slope_deg)
    xk, zk, X = radius * math.sin(s), depth + radius * (1 - math.cos(s)), 80.0
    zx = zk + (X - xk) * math.tan(s)
    return (cq.Workplane("XZ").moveTo(-X, -10).lineTo(X, -10).lineTo(X, zx).lineTo(xk, zk)
            .threePointArc((0, depth), (-xk, zk)).lineTo(-X, zx).close().extrude(150, both=True))


def rounded_seat(seat, radius, r):
    """Assise aux aretes du haut du contour arrondies de r. Aux pointes de l'assise R53, le dessus presque vertical
    faisait avec le flanc une lame de 12 deg, coupante a l'essai (Clement, 24 nov. 2026), et le conge d'OCCT y
    echoue. Plafonner la pente a SEAT_MAX_SLOPE ouvre l'angle (30 deg a 60), et le conge passe. (Un decale de toute
    l'assise arrondissait aussi, mais ses surfaces faussaient les booleens d'OCCT.)"""
    sharp = ell_prism(*seat, 0, 80).intersect(below_face_capped(SADDLE_T0, radius))
    top = [e for e in sharp.edges().vals() if e.geomType() != "LINE" and e.BoundingBox().zmin > 1.0]
    out = sharp.newObject(top).fillet(r)
    vif = ell_prism(*seat, 0, 80).intersect(below_face(SADDLE_T0, radius))
    assert out.val().isValid() and out.solids().size() == 1, "arrondi de l'assise"
    # un conge rate d'OCCT retire des volumes absurdes ; un arrondi de 2 mm sur le tour en retire environ 1,5 %
    assert vol(out.cut(vif)) < 0.01 and 0 < vol(sharp.cut(out)) < 0.03 * vol(sharp), "arrondi de l'assise : aretes seules"
    return out


def saddle_collar(height, seat=SEAT, radius=FACE_RADIUS, rim_radius=None, edge_round=0.0):
    """Assise du coussin et col d'une piece, dos plat (z = 0) pose sur l'appui plat du capot, imprime dos au plateau
    sans support. Dessus creuse en cylindre (105 mm comme le v2 par defaut) ; crete du col a `height` au-dessus du
    fond de l'assise, courbee au rayon `rim_radius` (celui de l'assise par defaut : meme hauteur partout). Le passage
    interieur garde l'ouverture du col (62 x 42) : la cle de 2 mm atteint toujours les vis."""
    ci, co = collar_inner(), collar_outer()
    rim_radius = rim_radius or radius
    assert max(face_sag(seat[0] / 2, radius), face_sag(co[0] / 2, rim_radius) + height) + SADDLE_T0 < 60, "assise plus haute que le prisme qui la decoupe"
    base = ell_prism(*seat, 0, 60).intersect(below_face(SADDLE_T0, radius))
    if edge_round:  # aretes du contour arrondies : 12 deg aux pointes de l'assise R53, coupante a l'essai (Clement, 24 nov. 2026)
        base = rounded_seat(seat, radius, edge_round)
    rim = ell_prism(*co, 0, 60).intersect(below_face(SADDLE_T0 + height, rim_radius))
    piece = base.union(rim).cut(ell_prism(*ci, -1, 61))
    top = SADDLE_T0 + height - 0.01
    try:  # crete arrondie, comme l'ancien col
        piece = piece.edges(cq.selectors.BoxSelector((-80, -80, top), (80, 80, 100))).fillet(COLLAR_ROUND)
    except Exception as exc:  # shortcut: crete vive si OCCT refuse le conge ; a reprendre a la main
        print(f"conge de la crete refuse : {exc}")
    # hauteur gravee sous l'assise, cote +x, dans le porte-a-faux au-dessus de l'ouverture du capot, hors de la bande
    # du ruban adhesif : lisible piece retournee
    x = (ci[0] / 2 + flange_outer()[0] / 2 - 1.5) / 2
    mark = f"{height:g}" if radius == FACE_RADIUS else f"{height:g} R{radius:.0f}"
    label = (cq.Workplane(cq.Plane(origin=(x, 0, 0), xDir=(0, -1, 0), normal=(0, 0, -1)))
             .text(mark, 5, -0.4, combine=False, halign="center", valign="center"))
    return piece.cut(label)


def radius_for_sag(x, sag):
    """Rayon dont l'avancee vaut `sag` a l'abscisse x (inverse de face_sag)."""
    return (x * x + sag * sag) / (2 * sag)


def saddle_shim(on=SHIM_ON, rise=SHIM_RISE, seat=SEAT):
    """Cale du cote +x, en place sur une surface de rayon `on` (repere de saddle_collar), le rayon de son dessus et son
    abscisse de debut, la ou elle atteint SHIM_MIN. La cale du cote -x est la meme tournee d'un demi-tour."""
    half = seat[0] / 2
    r = radius_for_sag(half, face_sag(half, on) + rise)
    lo, hi = 0.0, half
    for _ in range(50):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if face_sag(mid, r) - face_sag(mid, on) < SHIM_MIN else (lo, mid)
    co = collar_outer()
    side = cq.Workplane("XY").box(half, 200, 200, centered=(False, True, True)).translate((hi, 0, 0))
    shim = (ell_prism(*seat, 0, 60).intersect(below_face(SADDLE_T0, r)).cut(below_face(SADDLE_T0, on))
            .cut(ell_prism(co[0] + 2 * SHIM_CLEAR, co[1] + 2 * SHIM_CLEAR, -1, 61)).intersect(side))
    return shim, r, hi


# Assise du corps, retenue par Clement le 24 nov. 2026 apres l'essai des deux paires de cales sur la R85 : « niveau
# courbure, c'est vraiment ce qu'on veut ». D'une piece, dessus au rayon des cales du haut ; col a 20 mm au-dessus
# de l'assise partout, qui remonte avec elle sur les cotes (demande de Clement) ; arete exterieure du haut arrondie,
# la pointe des cales empilees etant presque coupante. (hauteur du col, rayon de l'assise, rayon de la crete)
BODY_SEAT_RADIUS = SHIM_ON
for _ in range(SHIM_LAYERS):
    BODY_SEAT_RADIUS = radius_for_sag(SEAT[0] / 2, face_sag(SEAT[0] / 2, BODY_SEAT_RADIUS) + SHIM_RISE)
BODY_SEAT = (20.0, BODY_SEAT_RADIUS, None)
SEAT_EDGE_ROUND = 2.0  # pointe : levre de 3,5 mm a 1 mm sous son sommet (2,1 a 1 mm d'arrondi)


def body_saddle():
    return saddle_collar(BODY_SEAT[0], radius=BODY_SEAT[1], rim_radius=BODY_SEAT[2], edge_round=SEAT_EDGE_ROUND)


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


def bonnet_gauge():
    """Temoin pose a plat au fond du capot d'essai (z = CAP_WALL) ; dessus a GAUGE_GAP sous le fond du coussin."""
    top = CAP_WALL + CAP_DEPTH + 0.02 + SADDLE_T0 - GAUGE_GAP  # appui du capot, jeu de l'assise, assise au centre
    h = top - CAP_WALL
    w = ell_prism(*GAUGE_SIZE, 0, h).faces(">Z").edges().fillet(1.0)
    label = cq.Workplane("XY", origin=(0, 0, h)).text(f"{GAUGE_GAP:g}", 8, -0.6, combine=False, halign="center", valign="center")
    return w.cut(label)


def joint_coupon_halves(length=40.0, width=19.0, thick=8.0):
    """Troncon droit du joint : y = offset depuis la peau, z = 0 plan de joint. Deux vis M3 a tete cylindrique sur
    rondelle et leurs ecrous prisonniers, comme au corps, et un avant-trou d'essai (vis de la trappe) sous la moitie arriere."""
    def strip(y0, y1, z0, z1):
        return cq.Workplane("XY").box(length + 2, y1 - y0, z1 - z0).translate((0, (y0 + y1) / 2, (z0 + z1) / 2))

    front = cq.Workplane("XY").box(length, width, thick).translate((0, width / 2, thick / 2))
    front = front.cut(strip(GROOVE[0], GROOVE[1], -1, GROOVE_DEPTH))
    for w, z in GROOVE_CHAMFER:
        front = front.cut(strip(GROOVE[0] - w, GROOVE[1] + w, -1, z))
    rt = max(thick, SCREW_LEN - BOSS_FRONT_H + 3.0)  # 2 mm de fond sous le percage de la vis
    rear = cq.Workplane("XY").box(length, width, rt).translate((0, width / 2, -rt / 2))
    rear = rear.union(cq.Workplane("XY").box(length, TONGUE[1] - TONGUE[0], TONGUE[2] + 0.5)
                      .translate((0, (TONGUE[0] + TONGUE[1]) / 2, (TONGUE[2] - 0.5) / 2)))
    rear = rear.cut(strip(-1, REBATE, -RING_H, 1)).cut(strip(LED_CH[0], LED_CH[1], -LED_CH[2], 1))
    for x in (-10, 10):
        front = front.cut(screw_hole_front(x, SCREW_OFFSET, thick + 1, 90))
        rear = rear.cut(screw_hole_rear(x, SCREW_OFFSET, 90)).union(nut_membrane(x, SCREW_OFFSET, -NUT_SKIN))  # fentes ouvertes sur le chant, cote chambre
    rear = rear.cut(pilot_hole(0, SCREW_OFFSET, -rt, 5.0))
    return front, rear


def light_coupon(width=12.0, step=10.0):
    out = None
    for i, t in enumerate(LIGHT_STEPS):
        b = cq.Workplane("XY").box(step + 0.01, width, t, centered=(False, True, False)).translate((i * step, 0, 0))
        out = b if out is None else out.union(b)
    return out


def light_walls(width=10.0, gap=4.0, base=0.6):
    """Parois debout de LIGHT_STEPS mm d'epaisseur : la lumiere y traverse des perimetres cote a cote, comme dans
    l'anneau, et non des couches empilees comme dans la bande a plat. Dos alignes sur y = 0, ou se pose la lumiere ;
    plus fine = plus basse (10 mm, puis 1 mm de plus par marche), pour les reconnaitre sans marquage."""
    out = cq.Workplane("XY").box(len(LIGHT_STEPS) * (width + gap) - gap, max(LIGHT_STEPS) + 4.0, base, centered=False).translate((0, -2.0, 0))
    for i, t in enumerate(LIGHT_STEPS):
        out = out.union(cq.Workplane("XY").box(width, t, 10.0 + i, centered=False).translate((i * (width + gap), 0, base)))
    return out


def check():
    ci = collar_inner()
    assert ci[0] >= MIN_COLLAR_INNER[0] - 1e-9 and ci[1] >= MIN_COLLAR_INNER[1] - 1e-9, ci
    comp = TONGUE[2] + GASKET[1] - GROOVE_DEPTH
    assert 0.5 <= comp <= 0.6, comp
    assert GROOVE[1] - GROOVE[0] >= GASKET[0] and TONGUE[1] - TONGUE[0] <= GROOVE[1] - GROOVE[0]
    assert 0.3 <= TONGUE[0] - GROOVE[0] <= 0.4 and 0.3 <= GROOVE[1] - TONGUE[1] <= 0.4, "jeu languette/rainure (0.35 par cote depuis la v10)"
    assert LED_CH[0] >= REBATE and TONGUE[0] - LED_CH[1] >= 0.9
    assert GROOVE[0] - max((w for w, _ in GROOVE_CHAMFER), default=0.0) - LED_CH[1] >= 0.95, "appui exterieur du joint trop etroit"
    return comp


def export(out=HERE / "out" / "v3-galet" / "coupons"):
    out.mkdir(parents=True, exist_ok=True)
    comp = check()
    report = {}

    def save(name, shape, printed=None):
        t = time.perf_counter()
        assert shape.val().isValid() and shape.solids().size() == 1, name
        export_step(shape, out / f"{name}.step")
        cq.exporters.export(printed or shape, str(out / f"{name}.stl"), tolerance=LIN_TOL, angularTolerance=ANG_TOL)
        clean_stl(out / f"{name}.stl")
        bb = shape.val().BoundingBox()
        report[name] = {"volume_cm3": round(vol(shape) / 1000, 2), "size_mm": [round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1)]}
        print(f"{name}: {report[name]}  ({time.perf_counter() - t:.1f} s)", flush=True)

    t = time.perf_counter()
    cap = pad_test_cap()
    print(f"construit capot en {time.perf_counter() - t:.1f} s", flush=True)
    assert CAP_DEPTH >= v0.MIC_SIZE[2] + 8.0, "place pour DJI a plat + ecouteur"
    save("pad-test-cap", cap)
    for h, r in SADDLE_COLLARS:
        ins = saddle_collar(h, radius=r)
        z_seat = CAP_WALL + CAP_DEPTH
        placed = ins.translate((0, 0, z_seat + 0.02))
        assert vol(placed.intersect(cap)) < 1e-6, "assise / capot"
        save(f"assise-col-{h:g}mm" + ("" if r == FACE_RADIUS else f"-r{r:g}"), ins)
    on, prev_x0, half, wall = SHIM_ON, 0.0, SEAT[0] / 2, collar_outer()[0] / 2 + SHIM_CLEAR
    for i in range(SHIM_LAYERS):
        shim, r, x0 = saddle_shim(on)
        bb = shim.val().BoundingBox()
        assert abs(bb.zmax - SADDLE_T0 - face_sag(half, r)) < 0.1 and abs(bb.xmax - half) < 0.1 and abs(bb.xmin - x0) < 0.1, bb
        assert abs(face_sag(half, r) - face_sag(half, SHIM_ON) - (i + 1) * SHIM_RISE) < 1e-9
        assert x0 >= prev_x0, "cale sans appui sur la precedente"
        print(f"cale {i + 1} : sur le rayon {on:.1f}, dessus au rayon {r:.1f}, de x = {x0:.1f} a {half:g} ; contre le col, "
              f"{face_sag(wall, r) - face_sag(wall, on):.1f} mm, col de 20 mm depassant de {20 - face_sag(wall, r) + face_sag(wall, SHIM_ON):.1f}", flush=True)
        # imprimee dessous au plateau : on tourne autour de l'axe de son appui pour mettre le milieu de l'arc d'appui en bas
        tilt = math.degrees((math.asin(x0 / on) + math.asin(half / on)) / 2)
        lying = shim.rotate((0, 0, SADDLE_T0 + on), (0, 1, SADDLE_T0 + on), tilt)
        save(f"cale-assise-r{on:.0f}-12mm", shim, lying.translate((0, 0, -lying.val().BoundingBox().zmin)))
        on, prev_x0 = r, x0
    assert abs(on - BODY_SEAT_RADIUS) < 1e-9
    body = body_saddle()
    assert vol(body.translate((0, 0, CAP_WALL + CAP_DEPTH + 0.02)).intersect(cap)) < 1e-6, "assise du corps / capot"
    save(f"assise-col-{BODY_SEAT[0]:g}mm-r{BODY_SEAT[1]:.0f}", body)
    gauge = bonnet_gauge()
    assert vol(gauge.translate((0, 0, CAP_WALL + 0.02)).intersect(cap)) < 1e-6, "temoin / capot"
    assert max(GAUGE_SIZE[0] / collar_inner()[0], GAUGE_SIZE[1] / collar_inner()[1]) < 0.95, "temoin trop large pour le col"
    save("temoin-bonnette", gauge)
    front, rear = joint_coupon_halves()
    assert vol(front.intersect(rear)) < 1e-6
    # imprimee comme le capot du corps depuis la v06 : plan de joint au plateau, portee de la rondelle en fond plat
    save("joint-coupon-front", front, front)
    # impression languette en haut : on garde l'orientation du corps (z vers le haut), posee a z = 0
    save("joint-coupon-rear", rear, rear.translate((0, 0, -rear.val().BoundingBox().zmin)))
    save("light-coupon-petg", light_coupon())
    save("light-walls", light_walls())
    (out / "coupons.json").write_text(json.dumps({"gasket_compression_mm": comp, "parts": report}, indent=2))
    print(f"OK compression joint {comp:.2f} mm, sorties {out}")


import json  # noqa: E402

if __name__ == "__main__":
    export()
