# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright 2026 Clement Barberousse
"""Maillage gmsh 3D de l'air du galet v3 assemble, pour openCFS (coordonnees ecrites en metres).

Source : cad/out/v3-galet/silent-mic-v3-galet-technical.step (repere de montage, mm). On maille l'air de la
chambre et du conduit (air-cavity-and-duct, qui exclut deja pieces, micro et passages de vis). Les deux mousses
(ref-foam-disc, ref-foam-liner) sont les tetraedres dont le centre tombe dans le voxel de leurs STL. Le visage
ferme le haut de l'air (le col depasse partout le coussin comprime : le coussin ne borde pas l'air).

Les frontieres sont classees sur le maillage, triangle par triangle (les sondes sur les surfaces BSpline de la
CAO se sont montrees peu fiables) :
- bouche : triangles du haut (visage), normale vers le haut, a moins de MOUTH_R de l'axe ;
- fentes de sortie : triangles dont le cote exterieur est de l'air libre dans le voxel des pieces imprimees
  (cad/leak_check.py, pas de 0.25 mm, matiere epaissie), entre z = -29 et -15 mm, a moins de 3 mm de la peau ;
- tout le reste : paroi rigide (omis du fichier : condition naturelle).
Les tetraedres d'air du conduit et des fentes recoivent leurs propres groupes (fluide de Zwikker-Kosten), d'apres
leur distance a la peau exterieure de la coque lue dans le meme voxel.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import gmsh
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "cad"))
import leak_check as lc  # noqa: E402

STEP = ROOT / "cad" / "out" / "v3-galet" / "silent-mic-v3-galet-technical.step"
MOUTH_R = 10.0  # mm, comme acoustics/fem/run.py
DUCT_OFFSET, SLOT_OFFSET = 9.0, 2.3  # mm depuis la peau : cloison conduit/chambre a 7.6-9.35, fentes dans la paroi de 0 a 2.3
# tranche du conduit (un tour, z de -17 a -6) et des goulottes de sortie (z de -25 a -19, cote gauche-arriere) ; plus bas,
# le fond de la chambre approche la peau et serait pris pour du conduit (essai du 27 nov. 2026 : 3,7 cm3 de trop)
Z_VENT = (-26.0, -2.5)
Z_SLOTS = (-26.0, -15.0)


def _by_name(key):
    hits = [t for d, t in gmsh.model.getEntities(3) if gmsh.model.getEntityName(3, t).endswith("/" + key)]
    assert len(hits) == 1, (key, hits)
    return hits[0]


def skin_offset(xyz, axes):
    """Distance a la peau exterieure de la coque (ellipse reduite, comme leak_check.band), mm ; nan hors plage."""
    zs = np.array(sorted(axes))
    ab = np.array([axes[k] for k in zs])
    zc = lc.ZC[zs]
    a = np.interp(xyz[:, 2], zc, ab[:, 0], left=np.nan, right=np.nan)
    b = np.interp(xyz[:, 2], zc, ab[:, 1], left=np.nan, right=np.nan)
    rho = np.sqrt((xyz[:, 0] / a) ** 2 + (xyz[:, 1] / b) ** 2)
    return (1 - rho) * np.sqrt(a * b)  # shortcut: ellipse quasi circulaire (84 x 66), erreur < 1 mm a 9 mm de la peau


def build(path, h_wall=0.8, h_bulk=3.5):
    t0 = time.time()
    log = lambda m: print(f"  [{time.time() - t0:6.1f} s] {m}", file=sys.stderr, flush=True)
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.option.setNumber("Geometry.OCCImportLabels", 1)
    occ = gmsh.model.occ
    occ.importShapes(str(STEP))
    occ.synchronize()
    air = _by_name("air-cavity-and-duct")
    # les mousses ne sont pas decoupees dans la CAO (le fragment laisse des facettes en double : maillage impossible) :
    # leurs tetraedres sont reconnus apres maillage, dans le voxel de leurs STL (cad/out/v3-galet/web)
    occ.remove([(3, t) for d, t in gmsh.model.getEntities(3) if t != air], recursive=True)
    occ.synchronize()
    vols, region = [air], {air: "air"}
    zmax = max(gmsh.model.getBoundingBox(3, v)[5] for v in vols)

    bnd = sorted({t for d, t in gmsh.model.getBoundary([(3, v) for v in vols], combined=True, oriented=False) if d == 2})
    allsurf = sorted({t for d, t in gmsh.model.getBoundary([(3, v) for v in vols], combined=False, oriented=False) if d == 2})
    f = gmsh.model.mesh.field.add("Distance")
    gmsh.model.mesh.field.setNumbers(f, "SurfacesList", allsurf)
    gmsh.model.mesh.field.setNumber(f, "Sampling", 30)
    g = gmsh.model.mesh.field.add("Threshold")
    for k, v in (("InField", f), ("SizeMin", h_wall), ("SizeMax", h_bulk), ("DistMin", 0.6), ("DistMax", 6.0)):
        gmsh.model.mesh.field.setNumber(g, k, v)
    b = gmsh.model.mesh.field.add("Ball")  # bouche : contour a peu pres rond
    for k, v in (("XCenter", 0), ("YCenter", 0), ("ZCenter", zmax), ("Radius", 2 * MOUTH_R), ("VIn", 1.0), ("VOut", h_bulk)):
        gmsh.model.mesh.field.setNumber(b, k, v)
    m = gmsh.model.mesh.field.add("Min")
    gmsh.model.mesh.field.setNumbers(m, "FieldsList", [g, b])
    gmsh.model.mesh.field.setAsBackgroundMesh(m)
    for k, v in (("Mesh.MeshSizeMax", h_bulk), ("Mesh.MeshSizeMin", 0.3), ("Mesh.MeshSizeExtendFromBoundary", 0),
                 ("Mesh.MeshSizeFromPoints", 0), ("Mesh.MeshSizeFromCurvature", 0), ("Mesh.Algorithm3D", 1),
                 ("Mesh.AngleToleranceFacetOverlap", 0.01)):
        gmsh.option.setNumber(k, v)
    gmsh.model.mesh.generate(3)
    log("maillage gmsh fait")
    node_tags, coords, _ = gmsh.model.mesh.getNodes()
    xyz = coords.reshape(-1, 3)
    pos = np.zeros(int(node_tags.max()) + 1, int)
    pos[node_tags.astype(int)] = np.arange(len(node_tags))
    tets = {}
    for v in vols:
        et, _, en = gmsh.model.mesh.getElements(3, v)
        assert list(et) == [4], et
        tets.setdefault(region[v], []).append(pos[en[0].astype(int)].reshape(-1, 4))
    tets = {k: np.concatenate(v) for k, v in tets.items()}
    tris = []
    for s in bnd:
        et, _, en = gmsh.model.mesh.getElements(2, s)
        tris.append(pos[en[0].astype(int)].reshape(-1, 3))
    tris = np.concatenate(tris)
    gmsh.finalize()
    log(f"{len(xyz)} noeuds, {sum(len(v) for v in tets.values())} tetraedres, {len(tris)} triangles de frontiere")
    return classify(path, xyz, tets, tris, zmax, log)


def classify(path, xyz, tets, tris, zmax, log):
    mat, thick, axes = lc.voxelize()
    log("voxels des pieces imprimees faits")
    # normale sortante de chaque triangle : opposee au quatrieme noeud de son tetraedre
    allt = np.concatenate(list(tets.values()))
    face_of = {}
    for t in allt:
        for j in range(4):
            face_of[tuple(sorted(np.delete(t, j)))] = t[j]
    tri_c = xyz[tris].mean(1)
    n = np.cross(xyz[tris[:, 1]] - xyz[tris[:, 0]], xyz[tris[:, 2]] - xyz[tris[:, 0]])
    area = 0.5 * np.linalg.norm(n, axis=1)
    n /= 2 * area[:, None]
    opp = np.array([face_of[tuple(sorted(t))] for t in tris])
    n *= -np.sign(np.einsum("ij,ij->i", xyz[opp] - tri_c, n))[:, None]
    probe = tri_c + 0.4 * n
    idx = [np.clip(np.floor((probe[:, i] - lc.LO[i]) / lc.P).astype(int), 0, s - 1) for i, s in enumerate((lc.NX, lc.NY, lc.NZ))]
    free = (mat[idx[2], idx[1], idx[0]] == 0) & ~thick[idx[2], idx[1], idx[0]]
    off = skin_offset(tri_c, axes)
    mouth = (tri_c[:, 2] > zmax - 8) & (n[:, 2] > 0.7) & (np.hypot(tri_c[:, 0], tri_c[:, 1]) < MOUTH_R)
    outlets = free & (tri_c[:, 2] > Z_SLOTS[0]) & (tri_c[:, 2] < Z_SLOTS[1]) & (off < 3.0)
    other = free & ~mouth & ~outlets & (tri_c[:, 2] < zmax - 8)
    info = {"mouth_mm2": round(float(area[mouth].sum()), 1), "outlets_mm2": round(float(area[outlets].sum()), 1),
            "ouvertures_ignorees_mm2": round(float(area[other].sum()), 1),
            "ouvertures_ignorees_z": np.unique(np.round(tri_c[other, 2])).tolist()[:40]}
    assert mouth.any() and outlets.any(), info

    # mousses : centre du tetraedre dans le voxel de la mousse ; conduit et fentes : pres de la peau, tranche de l'event
    air = tets.pop("air")
    c = xyz[air].mean(1)
    vidx = [np.clip(np.floor((c[:, i] - lc.LO[i]) / lc.P).astype(int), 0, s - 1) for i, s in enumerate((lc.NX, lc.NY, lc.NZ))]
    foam = {}
    for name in ("foam-disc", "foam-liner"):
        grid = foam_voxels(ROOT / "cad" / "out" / "v3-galet" / "web" / f"{name}.stl")
        foam[name] = grid[vidx[2], vidx[1], vidx[0]]
    tets["foam_disc"], tets["foam_liner"] = air[foam["foam-disc"]], air[foam["foam-liner"] & ~foam["foam-disc"]]
    keep = ~(foam["foam-disc"] | foam["foam-liner"])
    air, c = air[keep], c[keep]
    d = skin_offset(c, axes)
    in_vent = (c[:, 2] > Z_VENT[0]) & (c[:, 2] < Z_VENT[1]) & (d < DUCT_OFFSET)
    is_slot = in_vent & (d < SLOT_OFFSET) & (c[:, 2] > Z_SLOTS[0]) & (c[:, 2] < Z_SLOTS[1])
    tets.update(air=air[~in_vent], duct=air[in_vent & ~is_slot], slots=air[is_slot])
    vol = lambda t: float(np.abs(np.linalg.det(xyz[t[:, 1:]] - xyz[t[:, :1]])).sum() / 6000)
    info["volumes_cm3"] = {k: round(vol(v), 2) for k, v in tets.items()}
    info["n_nodes"] = len(xyz)
    info["n_tets"] = {k: len(v) for k, v in tets.items()}
    write_msh(path, xyz * 1e-3, tets, {"mouth": tris[mouth], "outlets": tris[outlets]})
    log(f"classement : {info}")
    return info


def foam_voxels(stl):
    """Voxel booleen d'un STL ferme sur la grille de cad/leak_check.py."""
    tri = lc.load(stl)
    out = np.zeros((lc.NZ, lc.NY, lc.NX), bool)
    z0, z1 = tri[:, :, 2].min(), tri[:, :, 2].max()
    for k, c in enumerate(lc.ZC):
        if z0 < c < z1:
            out[k] = lc.raster(lc.layer_segments(tri, c))
    return out


def write_msh(path, xyz, vols, surfs):
    groups = [(3, k) for k in vols] + [(2, k) for k in surfs]
    lines = ["$MeshFormat", "2.2 0 8", "$EndMeshFormat", "$PhysicalNames", str(len(groups))]
    lines += [f'{dim} {i + 1} "{name}"' for i, (dim, name) in enumerate(groups)]
    lines += ["$EndPhysicalNames", "$Nodes", str(len(xyz))]
    lines += [f"{i + 1} {x:.9g} {y:.9g} {z:.9g}" for i, (x, y, z) in enumerate(xyz)]
    lines += ["$EndNodes", "$Elements"]
    els, k = [], 0
    for i, (dim, name) in enumerate(groups):
        typ = 4 if dim == 3 else 2
        for e in (vols[name] if dim == 3 else surfs[name]):
            k += 1
            els.append(f"{k} {typ} 2 {i + 1} {i + 1} " + " ".join(str(int(x) + 1) for x in e))
    lines += [str(len(els))] + els + ["$EndElements"]
    path.write_text("\n".join(lines) + "\n")
