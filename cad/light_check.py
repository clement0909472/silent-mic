# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright 2026 Clement Barberousse
"""Controle des fuites de lumiere du galet v3, sur les fichiers a imprimer.

Le filament LED eclaire l'air de sa rainure, du tunnel des fils et de la baie. La lumiere ne doit sortir que par
l'anneau translucide. Meme decoupage que cad/leak_check.py : pieces en position de montage, voxels de 0.25 mm,
matiere epaissie d'un demi-voxel (un jeu de montage de moins de 0.25 mm compte comme ferme ; une seconde passe sans
epaissir montre les jeux plus larges).

- volume eclaire : l'air sous la peau (ellipse de la coque arriere, tranche par tranche) relie a la rainure LED. Il
  doit rejoindre la baie par le tunnel et ne pas toucher la chambre, sinon la lumiere sortirait par le col et les
  fentes de l'event ;
- sorties : la ou ce volume touche l'air exterieur relie au coin de la grille. Attendues, et elles servent de
  temoin : la prise USB-C et la fente de l'interrupteur. Rien d'autre ;
- parois : plastique noir minimal entre le volume eclaire et l'air exterieur, hors abords de l'anneau et des sorties.

    cad/guarded.sh -m 4 -t 900 .venv/bin/python cad/light_check.py

Hypotheses non prouvees ici : le PLA noir est opaque des 1 mm ; la gaine thermo noire du filament cache arrete sa
lumiere ; le jeu de 0.1 mm entre l'anneau et le capot ne laisse qu'un filet colle a l'anneau.
"""

import json

import numpy as np
from scipy import ndimage

import leak_check as lc

P = lc.P
# ouvertures voulues de la baie (cad/silent_mic_v3_galet.py, bay_cut), en x et z sur la peau du dessous, avec 0.2 mm
# de marge : fente USB-C (12 x 6, centre a Z_RF + 2.6) et son toit anti-surplomb, fente du levier de l'interrupteur.
# Le 25 nov. 2026, un centre de grappe pris dans un rayon de 8 a 12 mm rangeait parmi elles une fente de 0.4 mm sous
# le chargeur et le coin du logement de l'interrupteur : le tri se fait desormais voxel par voxel dans ces boites.
Z_RF = -47.0
EXPECTED = {"prise USB-C": ((-6.2, 6.2), (Z_RF - 0.6, Z_RF + 9.7)), "fente de l'interrupteur": ((13.1, 17.5), (Z_RF + 1.0, Z_RF + 3.6))}


def at(x, y, z):
    return lc.at(x, y, z)


def exits(mat, solid, interior, seeds):
    air = (mat == 0) & ~solid
    lab_in, _ = ndimage.label(air & interior)
    lit = lab_in[seeds["rainure"]]
    assert lit > 0, "graine de la rainure LED hors de l'air"
    out = {"tunnel_relie_rainure_et_baie": bool(lab_in[seeds["baie"]] == lit),
           "chambre_dans_le_noir": bool(lab_in[seeds["chambre"]] != lit)}
    led = lab_in == lit
    del lab_in
    lab_out, _ = ndimage.label(air & ~interior)
    outside = lab_out == lab_out[0, 0, 0]
    del lab_out
    touch = ndimage.binary_dilation(led) & outside
    every = touch.copy()  # toutes les sorties, voulues ou non : leurs abords sont exclus du calcul de paroi
    xx, zz = lc.XC[None, None, :], lc.ZC[:touch.shape[0], None, None]
    found = []
    for name, ((x0, x1), (z0, z1)) in EXPECTED.items():
        box = (xx >= x0) & (xx <= x1) & (zz >= z0) & (zz <= z1)
        found.append({"ou": name, "voxels": int((touch & box).sum())})
        touch &= ~box
    lab_e, n = ndimage.label(touch, structure=np.ones((3, 3, 3)))
    for sl in ndimage.find_objects(lab_e):
        k, j, i = (np.arange(s.start, s.stop) for s in sl)
        span = lambda c, idx: [round(float(c[idx].min() - P / 2), 1), round(float(c[idx].max() + P / 2), 1)]
        found.append({"ou": "AUTRE", "x_mm": span(lc.XC, i), "y_mm": span(lc.YC, j), "z_mm": span(lc.ZC, k)})
    out["sorties"] = found
    return out, led, outside, every


def main():
    mat, thick, axes = lc.voxelize()
    nz = int(np.searchsorted(lc.ZC, 3.0))  # la rainure s'ouvre au plan de joint : 3 mm au-dessus suffisent
    mat, thick = mat[:nz], thick[:nz]
    # peau exterieure, tranche par tranche, sur toutes les pieces (cote y >= 0, sans gorge d'ombre) : la coque arriere
    # seule est creusee par l'anneau et la rainure a ces hauteurs
    interior = np.zeros(mat.shape, bool)
    up = lc.YC >= 0
    for k in range(nz):
        ys, xs = np.nonzero(mat[k][up])
        if len(xs):
            a, b = np.abs(lc.XC[xs]).max() + P / 2, lc.YC[up][ys].max() + P / 2
            interior[k] = (lc.XX / (a - 0.3)) ** 2 + (lc.YY / (b - 0.3)) ** 2 <= 1.0
    # graine de la rainure : a midi, 1.1 mm sous le plan de joint, premier air derriere l'anneau
    k, ix = at(0, 0, -1.1)[0], np.abs(lc.XC).argmin()
    col = mat[k, :, ix]
    ring_j = np.nonzero((col == lc.RING) & up)[0]
    assert len(ring_j), "anneau absent a midi"
    j = ring_j.min() - 1
    while j > 0 and not (col[j] == 0 and not thick[k, j, ix]):
        assert col[j] in (0, lc.RING), "pas d'air entre l'anneau et la coque a midi"
        j -= 1
    seeds = {"rainure": (k, j, ix), "baie": at(0, -4, -40), "chambre": at(0, 10, 0)}
    for name, s in seeds.items():
        assert mat[s] == 0 and not thick[s], f"graine {name} hors de l'air"

    res = {"pas_mm": P}
    res["jeux_de_moins_de_0_25_mm_fermes"], led, outside, touch = exits(mat, thick, interior, seeds)
    # plastique minimal entre l'air eclaire et l'air exterieur, loin de l'anneau et des sorties
    dist = ndimage.distance_transform_edt(~led) * P
    del led
    far = ndimage.distance_transform_edt(~(touch | (mat == lc.RING))) * P > 3.0
    sel = outside & far
    i = np.unravel_index(np.argmin(np.where(sel, dist, np.inf)), dist.shape)
    res["paroi_noire_min_mm"] = round(float(dist[i] - P), 2)  # centres de voxels : une demi-maille de chaque cote
    res["paroi_noire_min_ou_mm"] = [round(float(lc.XC[i[2]]), 1), round(float(lc.YC[i[1]]), 1), round(float(lc.ZC[i[0]]), 1)]
    del dist, far, sel, outside, touch
    res["jeux_de_plus_de_0_25_mm"] = exits(mat, np.zeros_like(thick), interior, seeds)[0]

    (lc.OUT / "light-check.json").write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(res, indent=2, ensure_ascii=False))
    bad = []
    for case in ("jeux_de_moins_de_0_25_mm_fermes", "jeux_de_plus_de_0_25_mm"):
        r = res[case]
        if not (r["tunnel_relie_rainure_et_baie"] and r["chambre_dans_le_noir"]):
            bad.append(f"{case} : volume eclaire")
        if any(s["ou"] == "AUTRE" for s in r["sorties"]):
            bad.append(f"{case} : sortie de lumiere imprevue")
        if case == "jeux_de_moins_de_0_25_mm_fermes" and not all(s["voxels"] > 20 for s in r["sorties"] if s["ou"] != "AUTRE"):
            bad.append("temoin : les ouvertures de la baie ne sont pas vues")
    if res["paroi_noire_min_mm"] < 1.0:
        bad.append("paroi noire de moins de 1 mm")
    if bad:
        raise SystemExit("ECHEC : " + ", ".join(bad))


if __name__ == "__main__":
    main()
