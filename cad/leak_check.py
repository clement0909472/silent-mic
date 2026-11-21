# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright 2026 Clement Barberousse
"""Controle d'etancheite du galet v3 sur les fichiers a imprimer, sans CadQuery.

Les STL d'impression sont remis en position de montage et decoupes en voxels de 0.25 mm.
On "inonde" ensuite l'air de la chambre : il doit rejoindre l'exterieur, et seulement par l'entree
du conduit, un tour complet, puis les 4 fentes. Pour les passages, un voxel compte comme plein des
qu'un de ses 8 sous-voxels l'est : une peau de plastique de 0.13 mm en travers d'une fente est vue
(le 20 nov. 2026, fentes et entree etaient fermees par 0.2 a 0.9 mm de plastique, sans alerte).

    cad/guarded.sh -m 4 -t 900 .venv/bin/python cad/leak_check.py [--figure docs/img/v3-etancheite.png]

Le meme decoupage sert au controle acoustique : un ecoulement potentiel chambre -> exterieur est resolu
dans l'air des pieces imprimees. Sa conductivite K (mm) donne la masse acoustique de l'event, rho / K, le
parametre qui fixe l'attenuation. Elle est comparee a celle que suppose acoustics/params.json : le modele
1D ne lit pas la CAO, et le 20 nov. 2026 il annoncait 21 dB(A) pour un event dessine ferme.

Hypotheses, non prouvees ici : le joint mousse ferme le plan de joint, le coussin colle ferme
l'appui et le visage ferme le col. Le controle porte sur les parois imprimees.
"""

import argparse
import json
from pathlib import Path

import numpy as np
from scipy import ndimage

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "v3-galet"
P = 0.25
Z_SEAT, Z_RF, RING_H = 31.0, -47.0, 2.6
LO = np.array([-58.03, -48.03, -58.03])  # decale : aucun plan de coupe ne tombe sur un sommet
NX, NY, NZ = 464, 384, 432
XC, YC, ZC = (LO[i] + (np.arange(n) + 0.5) * P for i, n in enumerate((NX, NY, NZ)))
XX, YY = np.meshgrid(XC, YC)
FRONT, REAR, COVER, RING, COLLAR, GASKET, MOUTH, SLOTS, INLET, TOP = range(1, 11)
STL = np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])


def load(path):
    raw = Path(path).read_bytes()
    n = int.from_bytes(raw[80:84], "little")
    assert len(raw) == 84 + 50 * n, f"{path} : STL binaire attendu"
    return np.frombuffer(raw, STL, n, 84)["v"].astype(float)


def flip(tri, z0):
    """Demi-tour autour de x puis remontee : inverse de l'orientation d'impression."""
    return tri * np.array([1.0, -1.0, -1.0]) + np.array([0.0, 0.0, z0])


def parts():
    stem = OUT / "silent-mic-v3-galet"
    collar = load(f"{stem}-collar-insert-14mm.stl")
    collar[:, :, 2] += load(OUT / "web" / "collar-insert-14mm.stl")[:, :, 2].min() - collar[:, :, 2].min()
    return {FRONT: flip(load(f"{stem}-front.stl"), Z_SEAT), REAR: load(f"{stem}-rear.stl") + np.array([0, 0, Z_RF]),
            COVER: flip(load(f"{stem}-cover.stl"), Z_RF), RING: load(f"{stem}-ring.stl") - np.array([0, 0, RING_H]),
            COLLAR: collar, GASKET: load(OUT / "web" / "gasket.stl")}


def layer_segments(tri, c):
    """Segments de l'intersection des triangles avec le plan z = c."""
    up = tri[:, :, 2] > c
    hit = up.any(1) & ~up.all(1)
    t, up = tri[hit], up[hit]
    pts, ok = [], []
    for i, j in ((0, 1), (1, 2), (2, 0)):
        a, b = t[:, i], t[:, j]
        dz = b[:, 2] - a[:, 2]
        w = (c - a[:, 2]) / np.where(dz == 0, 1.0, dz)
        pts.append(a[:, :2] + w[:, None] * (b[:, :2] - a[:, :2]))
        ok.append(up[:, i] != up[:, j])
    pts, ok = np.stack(pts, 1), np.stack(ok, 1)
    order = np.argsort(~ok, axis=1, kind="stable")[:, :2]
    return np.take_along_axis(pts, order[:, :, None], 1)


def raster(seg, fine=1):
    """Remplissage pair-impair, grille fine fois plus serree : True quand le centre du pixel est dans la matiere."""
    p, nx, ny = P / fine, NX * fine, NY * fine
    xa, ya, xb, yb = seg[:, 0, 0], seg[:, 0, 1], seg[:, 1, 0], seg[:, 1, 1]
    r0 = np.clip(np.ceil((np.minimum(ya, yb) - LO[1]) / p - 0.5), 0, ny).astype(int)
    r1 = np.clip(np.ceil((np.maximum(ya, yb) - LO[1]) / p - 0.5), 0, ny).astype(int)
    cnt = r1 - r0
    idx = np.repeat(np.arange(len(seg)), cnt)
    rows = r0[idx] + np.arange(len(idx)) - np.repeat(np.cumsum(cnt) - cnt, cnt)
    yc = LO[1] + (rows + 0.5) * p
    x = xa[idx] + (yc - ya[idx]) / (yb[idx] - ya[idx]) * (xb[idx] - xa[idx])
    cols = np.clip(np.ceil((x - LO[0]) / p - 0.5), 0, nx).astype(int)
    d = np.bincount(rows * (nx + 1) + cols, minlength=ny * (nx + 1)).reshape(ny, nx + 1)
    return (np.cumsum(d[:, :nx], axis=1) & 1).astype(bool)


def voxelize():
    mat = np.zeros((NZ, NY, NX), np.uint8)
    thick = np.zeros((NZ, NY, NX), bool)  # matiere au plus large, pour les passages
    axes = {}  # demi-axes de la peau, lus sur la coque arriere (cote y > 0, sans gorge)
    spans = {pid: (tri, tri[:, :, 2].min(), tri[:, :, 2].max()) for pid, tri in parts().items()}
    for k, c in enumerate(ZC):
        for pid, (tri, z0, z1) in spans.items():
            if not z0 < c < z1:
                continue
            m = raster(layer_segments(tri, c))
            if pid == REAR and m[YC >= 0].any():
                ys, xs = np.nonzero(m[YC >= 0])
                axes[k] = (np.abs(XC[xs]).max() + P / 2, YC[YC >= 0][ys].max() + P / 2)
            mat[k][m & (mat[k] == 0)] = pid
            for dz in (-P / 4, P / 4):
                thick[k] |= raster(layer_segments(tri, c + dz), 2).reshape(NY, 2, NX, 2).any((1, 3))
    return mat, thick, axes


def band(axes, k, d0, d1):
    """Bande entre deux decalages de la peau (ellipses reduites, erreur < 0.1 mm ici)."""
    a, b = axes[k]
    inside = lambda d: (XX / (a - d)) ** 2 + (YY / (b - d)) ** 2 <= 1.0
    return inside(d0) & ~inside(d1)


def add_plugs(mat, axes):
    iy0, ix0 = np.abs(YC).argmin(), np.abs(XC).argmin()
    for k, c in enumerate(ZC):
        air = mat[k] == 0
        if c > Z_SEAT + 13.0:  # le visage
            mat[k][air] = MOUTH
        elif c > Z_SEAT:  # le coussin colle : tout sauf l'alesage du col
            lab, _ = ndimage.label(air)
            assert lab[iy0, ix0] > 0, c
            mat[k][air & (lab != lab[iy0, ix0])] = MOUTH
        if -9.4 < c < -3.2:  # gorge d'ombre et debouche des fentes
            mat[k][air & band(axes, k, -1.2, 2.3) & (YY < 0.6)] = SLOTS
        if -18.5 < c < -7.5:  # entree du conduit, dans la cloison conduit / chambre
            mat[k][air & band(axes, k, 9.35, 10.45) & (YY < 0) & (XX > 2) & (XX < 18)] = INLET
        if -19.0 < c < -4.4:  # bouchon d'essai dans le conduit, a midi
            mat[k][air & band(axes, k, 3.9, 9.8) & (YY > 0) & (np.abs(XX) < 1.5)] = TOP


def flood(mat, thick, closed):
    lut = np.zeros(16, bool)
    lut[[0] + [i for i in (MOUTH, SLOTS, INLET, TOP) if i not in closed]] = True
    return ndimage.label(lut[mat] & ~thick)[0]


def vent_conductivity(mat, lab, chamber, duct, outside, reach=8.0):
    """Conductivite de Rayleigh K (mm) du trajet chambre -> exterieur, par ecoulement potentiel dans l'air
    echantillonne au centre des voxels. Potentiel 1 dans la chambre et 0 dehors, au-dela de reach (mm) de
    l'entree et des fentes ; parois impermeables. Un conduit droit de section S et de longueur L donne S / L."""
    from scipy.sparse import coo_matrix, diags
    from scipy.sparse.linalg import cg

    k0, k1 = np.searchsorted(ZC, -19.0 - reach), np.searchsorted(ZC, -3.0 + reach)
    m, l = mat[k0:k1], lab[k0:k1]
    air = (m == 0) | (m >= SLOTS)
    near = lambda pid: ndimage.distance_transform_edt(m != pid) * P <= reach
    core = ndimage.binary_dilation((l == lab[duct]) | (m >= SLOTS), iterations=2)  # avec la lisiere que flood() ecarte
    near_in, near_out = near(INLET), near(SLOTS)
    one = air & (l == lab[chamber]) & ~near_in
    zero = air & (l == lab[outside]) & ~near_out
    free = air & ~one & ~zero & (core | near_in | near_out)
    n = int(free.sum())
    idx = np.full(m.shape, -1, np.int32)
    idx[free] = np.arange(n)
    diag, rhs, rows, cols, to_zero = np.zeros(n), np.zeros(n), [], [], []
    for ax in range(3):
        a = tuple(slice(None, -1) if i == ax else slice(None) for i in range(3))
        b = tuple(slice(1, None) if i == ax else slice(None) for i in range(3))
        both = free[a] & free[b]
        i, j = idx[a][both], idx[b][both]
        rows += [i, j]
        cols += [j, i]
        np.add.at(diag, np.concatenate([i, j]), 1.0)
        for u, v in ((a, b), (b, a)):
            w1, w0 = idx[u][free[u] & one[v]], idx[u][free[u] & zero[v]]
            np.add.at(diag, np.concatenate([w1, w0]), 1.0)
            np.add.at(rhs, w1, 1.0)
            to_zero.append(w0)
    rows, cols = np.concatenate(rows), np.concatenate(cols)
    a_mat = diags(diag + 1e-9) - coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n)).tocsr()
    phi, info = cg(a_mat, rhs, rtol=1e-9, maxiter=40000, M=diags(1.0 / (diag + 1e-9)))
    assert info == 0, f"gradient conjugue non converge ({info})"
    q_in = P * float(rhs.sum() - (rhs * phi).sum())
    q_out = P * float(phi[np.concatenate(to_zero)].sum())
    assert abs(q_in - q_out) <= 0.005 * q_in, (q_in, q_out)
    return q_in, n


def model_conductivity():
    """La meme grandeur, telle que le modele 1D la suppose (acoustics/params.json, design v3-galet)."""
    design = next(d for d in json.loads((HERE.parent / "acoustics" / "params.json").read_text())["designs"] if d["name"] == "v3-galet")
    inv = 0.0
    for e in design["vent"]["elements"]:
        if e["type"] == "duct":
            s = e["width"] * e["height"] * e.get("count", 1)
            inv += (e["length"] + e.get("end_correction", 0.85) * np.sqrt(s / np.pi)) / s
    s = design["vent"]["outlet_area_mm2"]
    return 1.0 / (inv + 0.61 * np.sqrt(s / np.pi) / s), design["cavity"]["volume_cm3"]


def at(x, y, z):
    return np.abs(ZC - z).argmin(), np.abs(YC - y).argmin(), np.abs(XC - x).argmin()


def run():
    mat, thick, axes = voxelize()
    add_plugs(mat, axes)
    chamber, outside = at(0, 10, 0), (0, 0, 0)
    assert mat[chamber] == 0 and mat[outside] == 0 and not thick[chamber] and not thick[outside]
    res = {"pas_mm": P}
    linked = lambda lab: bool(lab[chamber] == lab[outside])

    res["tel_que_dessine_la_chambre_rejoint_l_exterieur"] = linked(flood(mat, thick, {MOUTH}))
    res["fentes_bouchees_chambre_etanche"] = not linked(flood(mat, thick, {MOUTH, SLOTS}))
    # sans epaissir la matiere : un jeu de montage de plus de 0.25 mm entre deux pieces serait un chemin
    res["conduit_bouche_parois_non_epaissies_chambre_etanche"] = not linked(flood(mat, np.zeros_like(thick), {MOUTH, TOP}))
    res["entree_bouchee_chambre_etanche"] = not linked(flood(mat, thick, {MOUTH, INLET}))
    res["conduit_bouche_a_midi_chambre_etanche"] = not linked(flood(mat, thick, {MOUTH, TOP}))

    # temoin : un trou de 1 mm2 perce dans la paroi de 3 mm, fentes bouchees, doit etre detecte
    k = at(0, 0, -31.0)[0]
    hole = np.zeros_like(thick)
    for kk in range(k - 2, k + 2):
        hole[kk] = band(axes, kk, -0.6, 5.0) & (YY > 0) & (np.abs(XX) < 0.5)
    res["temoin_trou_1mm2_detecte"] = linked(flood(np.where(hole & (mat == REAR), 0, mat).astype(np.uint8), thick & ~hole, {MOUTH, SLOTS}))
    del hole

    lab = flood(mat, thick, {MOUTH, SLOTS, INLET})
    duct = at(0, axes[at(0, 0, -11.3)[0]][1] - 6.85, -11.3)
    assert mat[duct] == TOP
    vol = lambda p: float((lab == lab[p]).sum() * P ** 3 / 1000)
    res["volume_chambre_cm3"] = round(vol(chamber), 1)
    res["volume_conduit_cm3"] = round(vol(duct), 2)

    # sections, sur la matiere echantillonnee au centre des voxels (non epaissie)
    air0 = (mat == 0) | (mat >= SLOTS)
    stations = [round(1.8 + 0.3 * i, 1) for i in range(8)]  # dans la paroi entre gorge (1.5) et conduit (4.6)
    slot = {d: 0.0 for d in stations}
    win = np.zeros_like(air0)
    inl = np.zeros_like(air0)
    sec = np.zeros_like(air0)
    cols = np.abs(XC) < 0.5
    for k, c in enumerate(ZC):
        if -16.0 < c < -5.0:
            side = air0[k] & (YY < 0.6) & (XX < -4)  # hors tunnel des fils
            for d in stations:
                slot[d] += float((side & band(axes, k, d, d + 0.3)).sum()) * P ** 3 / 0.3
            win[k] = side & band(axes, k, 2.4, 3.6)
        if -18.5 < c < -7.5:
            inl[k] = air0[k] & band(axes, k, 9.4, 10.4) & (YY < 0) & (XX > 0) & (XX < 20)
        if -19.0 < c < -4.4:
            sec[k] = air0[k] & band(axes, k, 3.9, 9.8) & (YY > 0) & cols
    res["fentes_nombre"] = int(ndimage.label(win, structure=np.ones((3, 3, 3)))[1])
    res["fentes_section_dans_la_paroi_mm2"] = {str(d): round(v, 1) for d, v in slot.items()}
    res["fentes_section_min_mm2"] = round(min(slot.values()), 1)
    res["entree_surface_mm2"] = round(float(inl.sum() * P ** 3 / 1.0), 1)
    res["conduit_section_mm2"] = round(float(sec.sum() * P ** 3 / (cols.sum() * P)), 1)

    k3d, n = vent_conductivity(mat, lab, chamber, duct, outside)
    k1d, v1d = model_conductivity()
    helmholtz = lambda k, v: round(float(343.2 / (2 * np.pi) * np.sqrt(k * 1e-3 / (v * 1e-6))), 1)
    res["event_conductivite_mm"] = {"pieces_imprimees": round(k3d, 4), "modele_1d": round(float(k1d), 4),
                                    "rapport": round(float(k3d / k1d), 3), "inconnues": n}
    res["volume_chambre_modele_1d_cm3"] = v1d  # air + mousse dans la CAO ; les voxels comptent aussi le volume du micro
    res["event_longueur_equivalente_mm_pour_48_mm2"] = round(res["conduit_section_mm2"] / k3d, 1)
    res["resonance_helmholtz_hz"] = {"pieces_imprimees": helmholtz(k3d, res["volume_chambre_cm3"]), "modele_1d": helmholtz(k1d, v1d)}
    return res, mat, lab, axes


def figure(path, mat, lab, axes, res):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap

    chamber, duct = lab[at(0, 10, 0)], lab[at(0, axes[at(0, 0, -11.3)[0]][1] - 6.85, -11.3)]
    outside = lab[0, 0, 0]
    # 0 exterieur, 1 plastique, 2 anneau, 3 joint, 4 chambre, 5 conduit, 6 coussin et visage, 7 poche fermee
    colors = ["#ffffff", "#2d2d2d", "#7db8ff", "#d94a4a", "#cfe6fb", "#ff9a3c", "#e9dcc6", "#bdbdbd"]

    def cat(m, l):
        c = np.full(m.shape, 7, np.uint8)
        c[np.isin(m, (FRONT, REAR, COVER, COLLAR))] = 1
        c[m == RING], c[m == GASKET], c[m == MOUTH] = 2, 3, 6
        air = (m == 0) | (m >= SLOTS)
        c[air & (l == outside)] = 0
        c[m == SLOTS] = 0
        c[air & (l == chamber)] = 4
        c[(air & (l == duct)) | (m == INLET) | (m == TOP)] = 5
        return c

    fig, ax = plt.subplots(1, 3, figsize=(19, 7.2), dpi=130)
    cmap = ListedColormap(colors)
    ext_zy = (ZC[0], ZC[-1], YC[0], YC[-1])
    note = dict(fontsize=9.5, color="#111111", arrowprops=dict(arrowstyle="-", color="#111111", lw=0.9),
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#888888", lw=0.6))

    def side(a, x, title):
        i = np.abs(XC - x).argmin()
        a.imshow(cat(mat[:, :, i], lab[:, :, i]).T, origin="lower", extent=ext_zy, cmap=cmap, vmin=0, vmax=7, interpolation="nearest")
        a.set_title(title, fontsize=11)
        a.set_xlim(-58, 50)
        a.set_ylim(-48, 48)
        a.set_xlabel("arrière  <-  axe du corps (mm)  ->  visage")
        a.set_yticks([])

    side(ax[0], -10.0, "Coupe verticale dans une fente de sortie (x = -10 mm)")
    side(ax[1], 0.0, "Coupe verticale au milieu (x = 0) : barrage, baie, prise USB-C")
    k = np.abs(ZC + 12.0).argmin()
    ax[2].imshow(cat(mat[k], lab[k]), origin="lower", extent=(XC[0], XC[-1], YC[0], YC[-1]), cmap=cmap, vmin=0, vmax=7, interpolation="nearest")
    ax[2].set_title("Coupe horizontale 12 mm derrière le plan de joint", fontsize=11)
    ax[2].set_xlim(-50, 50)
    ax[2].set_ylim(-42, 42)
    ax[2].set_xticks([])
    ax[2].set_yticks([])

    for a, text, xy, xytext in (
            (ax[0], "chambre (air et mousse)", (5, 5), (-20, 6)),
            (ax[0], "conduit, 48 mm²", (-11.5, -26.2), (-56, -17)),
            (ax[0], "fente de sortie", (-10.6, -29.8), (-56, -34)),
            (ax[0], "gorge d'ombre : borgne,\n1,5 mm de profondeur", (-6.3, -32.3), (-30, -45)),
            (ax[0], "anneau lumineux", (-1.3, -31.8), (8, -45)),
            (ax[0], "joint mousse", (2.7, -25.5), (14, -38)),
            (ax[0], "en haut : conduit fermé,\nni fente ni gorge", (-11.5, 26.2), (-56, 40)),
            (ax[0], "coussin collé et visage", (38, 38), (20, 45)),
            (ax[1], "barrage : pas de conduit ici", (-11, -26), (-56, -12)),
            (ax[1], "tunnel des fils LED\n(baie vers rainure LED)", (-20, -28.2), (-56, -40)),
            (ax[1], "baie de l'électronique,\nhors de la chambre", (-41, 3), (-56, 30)),
            (ax[1], "prise USB-C", (-44.3, -26), (-35, -45)),
            (ax[1], "paroi pleine de 3 mm", (-34.9, 8), (-25, 22)),
            (ax[1], "pied du micro", (-10, -12.3), (2, 12)),
            (ax[2], "entrée du conduit", (9.5, -22.6), (14, -8)),
            (ax[2], "barrage", (0, -27.5), (-8, -14)),
            (ax[2], "4 fentes, 1 cm² en tout", (-27, -22.5), (-34, 2)),
            (ax[2], "conduit : un tour complet\navant de sortir", (0, 26.2), (-16, 12)),
            (ax[2], "tunnel des fils", (0, -29.3), (14, -39.5))):
        a.annotate(text, xy=xy, xytext=xytext, **note)
    fig.suptitle("Silent Mic v3 : ce qui est ouvert et ce qui ne l'est pas (voxels de 0,25 mm des fichiers à imprimer). "
                 f"Fentes bouchées, la chambre est étanche : {'oui' if res['fentes_bouchees_chambre_etanche'] else 'NON'}.", fontsize=12)
    handles = [plt.Rectangle((0, 0), 1, 1, fc=colors[i], ec="#888888") for i in (1, 4, 5, 0, 2, 3, 6, 7)]
    fig.legend(handles, ["plastique imprimé", "chambre", "conduit et fentes", "air extérieur", "anneau lumineux", "joint mousse",
                         "coussin et visage", "poche fermée (aimant)"], loc="lower center", ncol=8, fontsize=9.5, frameon=False)
    fig.tight_layout(rect=(0, 0.045, 1, 0.95))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--figure")
    a = ap.parse_args()
    res, mat, lab, axes = run()
    (OUT / "leak-check.json").write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(res, indent=2, ensure_ascii=False))
    if a.figure:
        figure(a.figure, mat, lab, axes, res)
    bad = [k for k in ("tel_que_dessine_la_chambre_rejoint_l_exterieur", "fentes_bouchees_chambre_etanche", "entree_bouchee_chambre_etanche",
                       "conduit_bouche_a_midi_chambre_etanche", "conduit_bouche_parois_non_epaissies_chambre_etanche",
                       "temoin_trou_1mm2_detecte") if not res[k]]
    if not 0.95 <= res["event_conductivite_mm"]["rapport"] <= 1.05:
        bad.append("masse acoustique de l'event : le modele 1D ne decrit pas les pieces imprimees")
    if not 0.94 <= res["volume_chambre_cm3"] / res["volume_chambre_modele_1d_cm3"] <= 1.06:
        bad.append("volume de la chambre : le modele 1D ne decrit pas les pieces imprimees")
    if res["fentes_nombre"] != 4 or res["fentes_section_min_mm2"] < 90 or res["entree_surface_mm2"] < 43 or not 44 <= res["conduit_section_mm2"] <= 52:
        bad.append("sections")
    if bad:
        raise SystemExit("ECHEC : " + ", ".join(bad))


if __name__ == "__main__":
    main()
