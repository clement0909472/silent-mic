# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright 2026 Clement Barberousse
"""Silent Mic v3 galet : eprouvettes a imprimer avant le corps.

- un capot d'essai du coussin d'oreillette et trois colliers amovibles (3, 10 et 16 mm) ;
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
TONGUE = (6.1, 8.9, 2.0)  # offsets et hauteur de la languette (coque arriere) ; 0.2 mm de jeu par cote (0.1 coincait en FDM)
GROOVE = (5.9, 9.1)  # rainure du capot avant
GASKET = (3.0, 2.0)  # bande de mousse a cellules fermees
GASKET_COMPRESSION = 0.55
GROOVE_DEPTH = TONGUE[2] + GASKET[1] - GASKET_COMPRESSION

# ---------- vis ----------
# Le capot avant et la trappe se vissent (decision de Clement du 23 nov. 2026 : seul le micro, retire tous
# les jours, tient par aimant). Vis M3 fraisees et ecrous prisonniers aux cotes du v2, deja imprime et monte.
# passage, tete, hauteur de fraisure. Fraisure a 90 deg, comme la tete d'une vis ISO 10642 : a 72 deg (cotes du
# v2), la tete ne portait que sur l'arete du haut (relecture independante du 23 nov. 2026)
SCREW = (v2.M3_CLEARANCE_DIAMETER, v2.M3_HEAD_DIAMETER, (v2.M3_HEAD_DIAMETER - v2.M3_CLEARANCE_DIAMETER) / 2)
# logement d'ecrou : sur angles, hauteur. 2.8 pour un ecrou de 2.4 : le plafond, imprime en pont, flechit un peu
NUT = (v2.M3_NUT_POCKET_DIAMETER, 2.8)
SCREW_LEN = 10.0  # M3 x 10, tete comprise
# axe des vis depuis la peau : a l'interieur de la rainure, rien ne traverse la paroi. A 13.9, une cle six pans
# de 2 mm atteint chaque tete a travers le col en place (controle dans le corps) : on rouvre sans decoller le coussin
SCREW_OFFSET = 13.9
BOSS_R = 5.0  # bossage rond de la coque arriere (ecrou)
BOSS_HALF, BOSS_FAR = 4.6, 4.3  # bossage du capot : demi-largeur, et avancee vers la chambre depuis l'axe
NUT_MOUTH = 3.3  # le logement d'ecrou est ferme par la peau jusque-la
# bossage du capot : 3.7 mm de matiere sous la fraisure. A 4.5, presque au niveau du dessus de la bride du
# capot (4.45), OCCT rendait un capot invalide
BOSS_FRONT_H = 5.0
NUT_SKIN = 1.2  # entre l'ecrou et le plan de joint : pont de 5.8 mm, 6 couches
BOSS_REAR_H = NUT_SKIN + NUT[1] + 1.2
HEAD_WELL_R = SCREW[1] / 2 + 0.2  # puits de la tete et du tournevis
PILOT_D = 2.7  # avant-trou d'une M3 qui taille son filet dans le PLA (trappe, hors volume acoustique)

# ---------- assise courbe et col (23 nov. 2026) ----------
# Clement : sur le v2 imprime, ses levres descendent un peu sous le fond du coussin, et l'assise du v2, creusee
# en cylindre de 105 mm (axe vertical), fait epouser les joues au coussin. L'assise se rapporte sur l'appui plat
# du capot (ruban double face, comme le coussin) : le capot garde son impression appui au plateau, sans support.
FACE_RADIUS = v0.FACE_RADIUS
SADDLE_T0 = 4.0  # epaisseur au centre, sous la bouche : le fond du coussin monte d'autant
# hauteur du col au-dessus du fond du coussin, au centre. La crete suit la courbe : plus haute sur les cotes,
# ou le coussin plie moins (idee de Clement). Coussin de 30 mm, environ 15 une fois comprime (Clement).
SADDLE_COLLARS = (8.0, 10.0, 14.0)

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
    """Cote tete (capot avant, tete vers +z) : passage, fraisure au sommet du bossage, puis puits de la tete et
    du tournevis jusqu'a top, ouvert vers la chambre (direction angle, en degres).
    Le capot s'imprime joint en haut : le puits est sous le bossage. Ouvert vers la chambre, rien ne s'y ferme
    dans le vide ; la face du bossage se ferme en trois couches de 0.2 : un pont droit entre les deux nervures
    (fente restante), puis un carre, puis le rond de la fraisure. Un puits rond dans un contrefort plein donnait
    un contour pose dans le vide, que le trancheur soutenait par une colonne de 24 mm dans chaque puits."""
    r, rh, dh, rw, h = SCREW[0] / 2, SCREW[1] / 2, SCREW[2], HEAD_WELL_R, BOSS_FRONT_H
    disc = lambda z0, z1: cq.Workplane("XY", origin=(0, 0, z0)).circle(rw).extrude(z1 - z0)
    local = (cq.Workplane("XY", origin=(0, 0, -0.5)).circle(r).extrude(h + 0.5)
             .union(cq.Workplane("XY").newObject([cq.Solid.makeCone(rh, r, dh, cq.Vector(0, 0, h), cq.Vector(0, 0, -1))]))
             .union(_lbox(-rh, rh, rh, h - 0.4, h - 0.2))  # 2e couche : carre
             .union(disc(h - 0.2, top)).union(_lbox(0, rh, rw, h - 0.2, h))  # 1re couche : pont au-dela de rh
             .union(_lbox(0, BOSS_FAR + 1.0, rw, h, top)))  # puits ouvert vers la chambre, entre les nervures
    return local.rotate((0, 0, 0), (0, 0, 1), angle).translate((x, y, 0))


def screw_hole_rear(x, y, angle):
    """Cote ecrou (coque arriere) : passage de la vis sous le plan de joint et logement d'ecrou M3 ouvert de
    cote (direction angle, en degres) pour y glisser l'ecrou. Le serrage ecrase la peau de NUT_SKIN entre
    l'ecrou et le bossage d'en face : rien ne travaille en traction a travers les couches.
    La peau s'imprime en pont au-dessus du logement : le trou de la vis s'y ferme en trois couches de 0.2
    (fente de toute la portee, carre, rond). Au-dela de NUT_MOUTH les parois du bossage rond sont trop minces
    pour porter un pont : le logement y est ouvert jusqu'en haut."""
    r = SCREW[0] / 2
    depth = SCREW_LEN - BOSS_FRONT_H + 1.0
    z0, z1 = -NUT_SKIN - NUT[1], -NUT_SKIN
    half = NUT[0] * math.cos(math.radians(30)) / 2
    local = (cq.Workplane("XY", origin=(0, 0, -depth)).circle(r).extrude(depth + z1)
             .union(cq.Workplane("XY", origin=(0, 0, z1 + 0.4)).circle(r).extrude(-z1 - 0.4 + 0.5))
             .union(cq.Workplane("XY", origin=(0, 0, z0)).polygon(6, NUT[0]).extrude(NUT[1]))  # un angle vers la fente
             .union(_lbox(0, BOSS_R + 0.5, half, z0, z1)).union(_lbox(NUT_MOUTH, BOSS_R + 0.5, half, z0, 0.5))
             .union(_lbox(-r, r, half, z1, z1 + 0.2)).union(_lbox(-r, r, r, z1 + 0.2, z1 + 0.4)))
    return local.rotate((0, 0, 0), (0, 0, 1), angle).translate((x, y, 0))


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
    1 %, d'ou la tolerance. Renvoie la forme reellement ecrite, a reutiliser dans l'assemblage."""
    n0, v0 = shape.solids().size(), vol(shape)
    for ready, tol in ((shape, 1e-4), (step_ready(shape), 1e-2)):
        cq.exporters.export(ready, str(path))
        back = step_solids(path)
        if back.solids().size() == n0 >= 1 and abs(vol(back) - v0) <= tol * v0:
            return ready
    raise AssertionError(f"{Path(path).name} : STEP relu en {back.solids().size()} solide(s) au lieu de {n0}, volume {vol(back):.0f} au lieu de {v0:.0f}")


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


def face_sag(x):
    """Avancee de l'assise vers le visage a l'abscisse x, par rapport au centre."""
    return FACE_RADIUS - math.sqrt(FACE_RADIUS ** 2 - x * x)


def below_face(depth):
    """Tout ce qui est sous la surface cylindrique de rayon FACE_RADIUS (axe vertical y) dont le creux est a z = depth."""
    zc = depth + FACE_RADIUS
    cyl = cq.Solid.makeCylinder(FACE_RADIUS, 300, cq.Vector(0, -150, zc), cq.Vector(0, 1, 0))
    return cq.Workplane("XY").box(300, 300, zc + 100, centered=(True, True, False)).translate((0, 0, -100)).cut(cq.Workplane("XY").newObject([cyl]))


def saddle_collar(height, seat=SEAT):
    """Assise du coussin et col d'une piece, dos plat (z = 0) pose sur l'appui plat du capot, imprime dos au plateau
    sans support. Dessus creuse en cylindre de 105 mm comme le v2 ; crete du col a `height` au-dessus de l'assise,
    partout. Le passage interieur garde l'ouverture du col (62 x 42) : la cle de 2 mm atteint toujours les vis."""
    ci, co = collar_inner(), collar_outer()
    base = ell_prism(*seat, 0, 60).intersect(below_face(SADDLE_T0))
    rim = ell_prism(*co, 0, 60).intersect(below_face(SADDLE_T0 + height))
    piece = base.union(rim).cut(ell_prism(*ci, -1, 61))
    top = SADDLE_T0 + height - 0.01
    try:  # crete arrondie, comme l'ancien col
        piece = piece.edges(cq.selectors.BoxSelector((-80, -80, top), (80, 80, 100))).fillet(COLLAR_ROUND)
    except Exception as exc:  # shortcut: crete vive si OCCT refuse le conge ; a reprendre a la main
        print(f"conge de la crete refuse : {exc}")
    # hauteur gravee sous l'assise, cote +x, dans le porte-a-faux au-dessus de l'ouverture du capot, hors de la bande
    # du ruban adhesif : lisible piece retournee
    x = (ci[0] / 2 + flange_outer()[0] / 2 - 1.5) / 2
    label = (cq.Workplane(cq.Plane(origin=(x, 0, 0), xDir=(0, -1, 0), normal=(0, 0, -1)))
             .text(f"{height:g}", 5, -0.4, combine=False, halign="center", valign="center"))
    return piece.cut(label)


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
    """Troncon droit du joint : y = offset depuis la peau, z = 0 plan de joint. Deux vis M3 fraisees et leurs
    ecrous prisonniers, comme au corps, et un avant-trou d'essai (vis de la trappe) sous la moitie arriere."""
    def strip(y0, y1, z0, z1):
        return cq.Workplane("XY").box(length + 2, y1 - y0, z1 - z0).translate((0, (y0 + y1) / 2, (z0 + z1) / 2))

    front = cq.Workplane("XY").box(length, width, thick).translate((0, width / 2, thick / 2))
    front = front.cut(strip(GROOVE[0], GROOVE[1], -1, GROOVE_DEPTH))
    rear = cq.Workplane("XY").box(length, width, thick).translate((0, width / 2, -thick / 2))
    rear = rear.union(cq.Workplane("XY").box(length, TONGUE[1] - TONGUE[0], TONGUE[2] + 0.5)
                      .translate((0, (TONGUE[0] + TONGUE[1]) / 2, (TONGUE[2] - 0.5) / 2)))
    rear = rear.cut(strip(-1, REBATE, -RING_H, 1)).cut(strip(LED_CH[0], LED_CH[1], -LED_CH[2], 1))
    for x in (-10, 10):
        front = front.cut(screw_hole_front(x, SCREW_OFFSET, thick + 1, 90))
        rear = rear.cut(screw_hole_rear(x, SCREW_OFFSET, 90))  # fentes ouvertes sur le chant, cote chambre
    rear = rear.cut(pilot_hole(0, SCREW_OFFSET, -thick, 5.0))
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
    assert 0.15 <= TONGUE[0] - GROOVE[0] <= 0.25 and 0.15 <= GROOVE[1] - TONGUE[1] <= 0.25, "jeu languette/rainure"
    assert LED_CH[0] >= REBATE and TONGUE[0] - LED_CH[1] >= 0.9
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
    for h in SADDLE_COLLARS:
        ins = saddle_collar(h)
        z_seat = CAP_WALL + CAP_DEPTH
        placed = ins.translate((0, 0, z_seat + 0.02))
        assert vol(placed.intersect(cap)) < 1e-6, "assise / capot"
        save(f"assise-col-{h:g}mm", ins)
    gauge = bonnet_gauge()
    assert vol(gauge.translate((0, 0, CAP_WALL + 0.02)).intersect(cap)) < 1e-6, "temoin / capot"
    assert max(GAUGE_SIZE[0] / collar_inner()[0], GAUGE_SIZE[1] / collar_inner()[1]) < 0.95, "temoin trop large pour le col"
    save("temoin-bonnette", gauge)
    front, rear = joint_coupon_halves()
    assert vol(front.intersect(rear)) < 1e-6
    # imprimee comme le capot du corps : plan de joint en haut, fraisures vers le plateau
    save("joint-coupon-front", front, front.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, front.val().BoundingBox().zmax)))
    # impression languette en haut : on garde l'orientation du corps (z vers le haut), posee a z = 0
    save("joint-coupon-rear", rear, rear.translate((0, 0, -rear.val().BoundingBox().zmin)))
    save("light-coupon-petg", light_coupon())
    (out / "coupons.json").write_text(json.dumps({"gasket_compression_mm": comp, "parts": report}, indent=2))
    print(f"OK compression joint {comp:.2f} mm, sorties {out}")


import json  # noqa: E402

if __name__ == "__main__":
    export()
