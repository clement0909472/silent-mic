# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright 2026 Clement Barberousse
"""Tenue des vissages du galet : statique lineaire 3D openCFS, tetraedres quadratiques gmsh.

Unites coherentes mm, N, MPa. PLA plein isotrope (le PLA imprime est anisotrope : les couches tiennent moins entre
elles que dans leur plan, d'ou deux seuils au compte rendu). Les ecrous M3 sont des volumes d'acier colles au plafond
de leur logement seulement (0.17 mm de jeu sur les cotes), tires vers le haut par la vis : la force s'applique en
pression sur leur face du bas.

    python mechanics/fem/run.py --selfcheck          poutre console sous charge repartie, contre la theorie
    python mechanics/fem/run.py --col [--step f]     capot : 4 ecrous du col tires de 1 N, diamants tenus
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
from pathlib import Path

import gmsh
import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "mechanics" / "fem" / "work"
PLA = (3500.0, 0.36)  # MPa ; fiches PLA 2.3 a 3.6 GPa, piece pleine a 100 %
STEEL = (200000.0, 0.30)
NUT_AC, NUT_H, NUT_HOLE = 6.35, 2.4, 2.5  # ecrou M3 reel : 5.5 sur plats, 2.4 de haut, filet ~2.5


def mat_xml(path):
    def m(name, e, nu):
        return (f'<material name="{name}"><mechanical><density><linear><real>1e-9</real></linear></density>'
                f"<elasticity><linear><isotropic><elasticityModulus><real>{e}</real></elasticityModulus>"
                f"<poissonNumber><real>{nu}</real></poissonNumber></isotropic></linear></elasticity></mechanical></material>")
    path.write_text('<?xml version="1.0"?>\n<cfsMaterialDataBase xmlns="http://www.cfs++.org/material">'
                    + m("pla", *PLA) + m("steel", *STEEL) + "</cfsMaterialDataBase>")


# gradient conjugue natif d'openCFS (LIS, PETSc et Pardiso ne sont pas compiles ; CHOLMOD sature la memoire au-dela de
# 100 000 tetras quadratiques)
LIS = """<linearSystems><system><solutionStrategy><standard><matrix storage="{st}"/></standard></solutionStrategy>
  <solverList><cg><tol>1e-9</tol><maxIter>40000</maxIter><consoleConvergence>no</consoleConvergence></cg></solverList>
  <precondList><{pc}/></precondList></system></linearSystems>"""


def sim_xml(path, job, regions, fixed, pressures, solver=""):
    reg = "".join(f'<region name="{r}" material="{m}"/>' for r, m in regions.items())
    surfs = "".join(f'<surfRegion name="{s}"/>' for s in [fixed] + list(pressures))
    loads = "".join(f'<pressure name="{s}" value="{v:.9g}"/>' for s, v in pressures.items())
    path.write_text(f"""<?xml version="1.0"?>
<cfsSimulation xmlns="http://www.cfs++.org/simulation">
  <fileFormats><input><gmsh fileName="{job}.msh"/></input><output><hdf5/></output>
    <materialData file="mat.xml" format="xml"/></fileFormats>
  <domain geometryType="3d"><regionList>{reg}</regionList><surfRegionList>{surfs}</surfRegionList></domain>
  <sequenceStep><analysis><static/></analysis><pdeList><mechanic subType="3d">
    <regionList>{"".join(f'<region name="{r}"/>' for r in regions)}</regionList>
    <bcsAndLoads><fix name="{fixed}"><comp dof="x"/><comp dof="y"/><comp dof="z"/></fix>{loads}</bcsAndLoads>
    <storeResults><nodeResult type="mechDisplacement"><allRegions/></nodeResult>
      <elemResult type="mechStress"><allRegions/></elemResult></storeResults>
  </mechanic></pdeList>{solver}</sequenceStep>
</cfsSimulation>
""")


def run_cfs(work, job, mem_gb=8, max_s=1800):
    t = time.time()
    p = subprocess.run([str(ROOT / "cad" / "guarded.sh"), "-m", str(mem_gb), "-t", str(max_s), "cfs", "-q", "-p", f"{job}.xml", job],
                       cwd=work, capture_output=True, text=True)
    if p.returncode != 0 or not (work / "results_hdf5" / f"{job}.cfs").exists():
        raise RuntimeError(f"cfs a echoue ({job}) :\n{p.stdout[-3000:]}\n{p.stderr[-3000:]}")
    return time.time() - t


def read(work, job):
    """Deplacements aux noeuds, contraintes aux elements (xx yy zz yz xz xy) et barycentres, par region."""
    with h5py.File(work / "results_hdf5" / f"{job}.cfs", "r") as f:
        xyz = f["Mesh/Nodes/Coordinates"][:]
        conn = f["Mesh/Elements/Connectivity"][:]
        step = f["Results/Mesh/MultiStep_1/Step_1"]
        disp = {r: g["Nodes/Real"][:] for r, g in step["mechDisplacement"].items()}
        out = {}
        for r, g in step["mechStress"].items():
            ids = f[f"Mesh/Regions/{r}/Elements"][:] - 1
            c = conn[ids, :4] - 1  # sommets du tetra
            out[r] = (xyz[c].mean(axis=1), g["Elements/Real"][:])
        nodes = {r: f[f"Mesh/Regions/{r}/Nodes"][:] - 1 for r in disp}
    return xyz, disp, nodes, out


def von_mises(s):
    xx, yy, zz, yz, xz, xy = s.T
    return np.sqrt(0.5 * ((xx - yy) ** 2 + (yy - zz) ** 2 + (zz - xx) ** 2) + 3 * (yz ** 2 + xz ** 2 + xy ** 2))


def principal_max(s):
    xx, yy, zz, yz, xz, xy = s.T
    m = np.stack([np.stack([xx, xy, xz], -1), np.stack([xy, yy, yz], -1), np.stack([xz, yz, zz], -1)], -2)
    return np.linalg.eigvalsh(m)[:, -1]


def finish_mesh(path, order=2):
    gmsh.model.mesh.generate(3)
    gmsh.option.setNumber("Mesh.SecondOrderLinear", 1)  # noeuds milieux droits : courbes, ils retournaient des tetras dans les parois minces
    gmsh.model.mesh.setOrder(order)
    gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
    gmsh.write(str(path))
    n = len(gmsh.model.mesh.getNodes()[0])
    gmsh.finalize()
    return n


# ---------- validation : poutre console ----------

def selfcheck(pc=None):
    """Console L x b x h encastree en x = 0, pression q sur le dessus : fleche et contrainte a mi-portee."""
    L, b, h, q = 40.0, 4.0, 4.0, 0.01  # mm, MPa
    work = WORK / "selfcheck"
    work.mkdir(parents=True, exist_ok=True)
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    v = gmsh.model.occ.addBox(0, 0, 0, L, b, h)
    gmsh.model.occ.synchronize()
    faces = {}
    for _, t in gmsh.model.getBoundary([(3, v)], oriented=False):
        c = gmsh.model.occ.getCenterOfMass(2, t)
        if abs(c[0]) < 1e-6:
            faces["clamp"] = t
        elif abs(c[2] - h) < 1e-6:
            faces["top"] = t
    gmsh.model.addPhysicalGroup(3, [v], name="beam")
    for k, t in faces.items():
        gmsh.model.addPhysicalGroup(2, [t], name=k)
    gmsh.option.setNumber("Mesh.MeshSizeMax", 1.0)
    n = finish_mesh(work / "beam.msh")
    mat_xml(work / "mat.xml")
    sim_xml(work / "beam.xml", "beam", {"beam": "pla"}, "clamp", {"top": q}, LIS.format(pc=pc, st="sparseNonSym" if pc == "MG" else "sparseSym") if pc else "")
    t = run_cfs(work, "beam")
    xyz, disp, nodes, st = read(work, "beam")
    d = disp["beam"]
    ids = nodes["beam"]
    tip = np.abs(xyz[ids, 0] - L) < 1e-6
    w, I, E, nu = q * b, b * h ** 3 / 12, PLA[0], PLA[1]
    G = E / (2 * (1 + nu))
    fleche = w * L ** 4 / (8 * E * I) + w * L ** 2 / (2 * (5 / 6) * G * b * h)  # flexion + cisaillement (Timoshenko)
    dz = d[tip, 2].mean()
    cen, s = st["beam"]
    sel = (np.abs(cen[:, 0] - L / 2) < 1.0) & (cen[:, 2] > h - 0.5)
    sxx = s[sel, 0].mean()
    sxx_th = (w * (L / 2) ** 2 / 2) / (b * h ** 2 / 6) * (h - 0.25 - h / 2) / (h / 2)  # au niveau moyen des barycentres
    print(f"noeuds {n}, cfs {t:.1f} s")
    print(f"fleche : FEM {dz:+.5f} mm, theorie {fleche:.5f} mm ({(abs(dz) / fleche - 1) * 100:+.1f} %) ; signe : pression positive = vers la face")
    print(f"sigma_xx a mi-portee, haut : FEM {sxx:+.3f} MPa, theorie {sxx_th:.3f} MPa ({(abs(sxx) / sxx_th - 1) * 100:+.1f} %)")
    ok = abs(abs(dz) / fleche - 1) < 0.03 and abs(abs(sxx) / sxx_th - 1) < 0.05
    print("VALIDATION", "OK" if ok else "ECHEC")
    return ok


# ---------- capot : ecrous du col ----------

def col_model(step, label, h_near=0.3, h_far=1.6, precond="MG"):
    sys.path.insert(0, str(ROOT / "cad"))
    import silent_mic_v3_galet as g  # cotes de la CAO (rien n'est construit a l'import)
    work = WORK / label
    work.mkdir(parents=True, exist_ok=True)
    # ecrous : plafond du logement retrouve dans le STEP (face horizontale percee la plus haute au-dessus de chaque vis)
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    shell = gmsh.model.occ.importShapes(str(step))
    # seul le haut du capot porte les efforts (ecrous -> plaque -> diamants) : coupe libre 12 mm sous l'appui, ce qui
    # assouplit un peu la plaque (prudent) et tient sous la limite du solveur direct (CHOLMOD 32 bits)
    top = gmsh.model.occ.addBox(-100, -100, g.Z_SEAT - 12.0, 200, 200, 30)
    shell, _ = gmsh.model.occ.intersect(shell, [(3, top)])
    gmsh.model.occ.synchronize()
    vols = [t for d, t in shell if d == 3]
    assert len(vols) == 1, vols
    ceil = []
    for x, y in g.col_screw_xy():
        best = None
        for _, t in gmsh.model.getBoundary([(3, vols[0])], oriented=False):
            bb = gmsh.model.getBoundingBox(2, t)
            if abs(bb[5] - bb[2]) < 1e-4 and bb[0] < x < bb[3] and bb[1] < y < bb[4] and bb[2] < g.Z_SEAT - 0.5:
                if bb[0] > x - 8 and bb[3] < x + 16 and bb[1] > y - 16 and bb[4] < y + 16:
                    n = gmsh.model.getNormal(t, [0.5, 0.5])
                    if n[2] < -0.9 and (best is None or bb[2] > best):
                        best = bb[2]
        assert best is not None, (x, y)
        ceil.append((x, y, best))
    nuts = []
    for x, y, z1 in ceil:
        rot = math.atan2(-y, -x) + math.radians(30)  # comme le logement : un angle vers la fente
        pts = [gmsh.model.occ.addPoint(x + NUT_AC / 2 * math.cos(rot + k * math.pi / 3), y + NUT_AC / 2 * math.sin(rot + k * math.pi / 3), z1 - NUT_H)
               for k in range(6)]
        lines = [gmsh.model.occ.addLine(pts[k], pts[(k + 1) % 6]) for k in range(6)]
        face = gmsh.model.occ.addPlaneSurface([gmsh.model.occ.addCurveLoop(lines)])
        prism = gmsh.model.occ.extrude([(2, face)], 0, 0, NUT_H)
        body = [t for d, t in prism if d == 3][0]
        hole = gmsh.model.occ.addCylinder(x, y, z1 - NUT_H - 1, 0, 0, NUT_H + 2, NUT_HOLE / 2)
        nut, _ = gmsh.model.occ.cut([(3, body)], [(3, hole)])
        nuts.append(nut[0][1])
    out, mp = gmsh.model.occ.fragment([(3, vols[0])], [(3, n) for n in nuts])
    gmsh.model.occ.synchronize()
    pla = [t for d, t in mp[0] if d == 3]
    steel = [t for i in range(len(nuts)) for d, t in mp[1 + i] if d == 3]
    # faces : bas des ecrous (charge), surfaces des diamants (tenues)
    load, fix = [], []
    for t in steel:
        for _, f in gmsh.model.getBoundary([(3, t)], oriented=False):
            bb = gmsh.model.getBoundingBox(2, f)
            if abs(bb[5] - bb[2]) < 1e-4 and any(abs(bb[2] - (z1 - NUT_H)) < 1e-3 for _, _, z1 in ceil):
                load.append(f)
    for t in pla:
        for _, f in gmsh.model.getBoundary([(3, t)], oriented=False):
            bb = gmsh.model.getBoundingBox(2, f)
            c = ((bb[0] + bb[3]) / 2, (bb[1] + bb[4]) / 2)
            if bb[2] > g.Z_SEAT + 0.05 and any(math.hypot(c[0] - dx, c[1] - dy) < 3.0 for dx, dy in g.col_diamond_xy()):
                fix.append(f)
    assert len(load) == 4 and len(fix) >= 4, (load, fix)
    gmsh.model.addPhysicalGroup(3, pla, name="pla")
    gmsh.model.addPhysicalGroup(3, steel, name="nuts")
    gmsh.model.addPhysicalGroup(2, load, name="nutload")
    gmsh.model.addPhysicalGroup(2, fix, name="diamonds")
    area = sum(gmsh.model.occ.getMass(2, f) for f in load) / 4
    # maillage fin autour des 4 ecrous
    pts = [gmsh.model.occ.addPoint(x, y, z1) for x, y, z1 in ceil]
    gmsh.model.occ.synchronize()
    fd = gmsh.model.mesh.field.add("Distance")
    gmsh.model.mesh.field.setNumbers(fd, "PointsList", pts)
    ft = gmsh.model.mesh.field.add("Threshold")
    for k, v in (("InField", fd), ("SizeMin", h_near), ("SizeMax", h_far), ("DistMin", 4.0), ("DistMax", 9.0)):
        gmsh.model.mesh.field.setNumber(ft, k, v)
    gmsh.model.mesh.field.setAsBackgroundMesh(ft)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    t0 = time.time()
    n = finish_mesh(work / "col.msh")
    t_mesh = time.time() - t0
    mat_xml(work / "mat.xml")
    sim_xml(work / "col.xml", "col", {"pla": "pla", "nuts": "steel"}, "diamonds", {"nutload": 1.0 / area}, LIS.format(pc=precond, st="sparseNonSym" if precond == "MG" else "sparseSym"))  # 1 N par ecrou
    t_cfs = run_cfs(work, "col")
    res = {"step": str(step), "noeuds": n, "maillage_s": round(t_mesh, 1), "cfs_s": round(t_cfs, 1)}
    return col_post(work, ceil, res)


def col_post(work, ceil, res):
    """Contraintes autour de chaque ecrou pour 1 N : peau au-dessus (moyenne de von Mises), zone de 8 mm (99e centile,
    pour ecarter les pointes des angles vifs, singularites du modele) en traction entre couches (sigma_zz) et dans le
    plan des couches ; puis les forces de premiers degats et de rupture pour deux jeux de seuils du PLA imprime."""
    sys.path.insert(0, str(ROOT / "cad"))
    import silent_mic_v3_galet as g
    xyz, disp, nodes, st = read(work, "col")
    cen, s = st["pla"]
    xx, yy, zz, yz, xz, xy = s.T
    vm = von_mises(s)
    inpl = (xx + yy) / 2 + np.sqrt(((xx - yy) / 2) ** 2 + xy ** 2)
    nd = nodes["nuts"]
    res["ecrous"] = []
    for x, y, z1 in ceil:
        r = np.hypot(cen[:, 0] - x, cen[:, 1] - y)
        skin = (r < NUT_AC / 2 + 0.6) & (cen[:, 2] > z1) & (cen[:, 2] < g.Z_SEAT)
        near = (r < 8.0) & (cen[:, 2] > z1 - 4) & (cen[:, 2] < g.Z_SEAT + 0.1)
        on = np.hypot(xyz[nd, 0] - x, xyz[nd, 1] - y) < 4
        res["ecrous"].append({"xy": [round(x, 1), round(y, 1)], "peau_mm": round(g.Z_SEAT - z1, 2),
                              "peau_vm_moyen": float(vm[skin].mean()), "entre_couches_p99": float(np.percentile(zz[near], 99)),
                              "plan_p99": float(np.percentile(inpl[near], 99)), "vm_max_angles": float(vm[near].max()),
                              "montee_ecrou_um": float(disp["nuts"][on, 2].mean() * 1000)})
    m = {k: float(np.mean([e[k] for e in res["ecrous"]])) for k in ("peau_vm_moyen", "entre_couches_p99", "plan_p99")}
    res["unite"] = "MPa (ou um) pour 1 N par ecrou"
    res["forces_N"] = {f"seuils {z}/{pl} MPa": {"premiers_degats": round(min(z / m["entre_couches_p99"], pl / m["plan_p99"])),
                                                 "rupture_peau": round(pl / m["peau_vm_moyen"])} for z, pl in ((15, 40), (25, 50))}
    (work / "result.json").write_text(json.dumps(res, indent=1))
    return res


# ---------- souplesse des parois de la chambre ----------

def shell_model(label="coque", h=1.5, precond="Jacobi"):
    """Capot et coque colles au plan de joint (les bords se touchent, la precharge des vis depasse de loin une
    pression acoustique), appui du col tenu (le col visse est bien plus raide), 1 Pa sur toutes les faces qui bordent
    l'air de la chambre et du conduit. Sortie : variation de volume de l'air par pascal, a comparer a la souplesse de
    l'air (V / rho c2) et a l'hypothese du modele 1D (shell dans acoustics/params.json)."""
    sys.path.insert(0, str(ROOT / "cad"))
    import silent_mic_v3_galet as g
    work = WORK / label
    work.mkdir(parents=True, exist_ok=True)
    d = ROOT / "cad/out/v3-galet"
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    parts = {n: [t for dd, t in gmsh.model.occ.importShapes(str(d / f"silent-mic-v3-galet-{n}.step")) if dd == 3] for n in ("front", "rear", "air-volume")}
    _, mp = gmsh.model.occ.fragment([(3, t) for t in parts["front"] + parts["rear"]], [(3, t) for t in parts["air-volume"]])
    gmsh.model.occ.synchronize()
    n_solid = len(parts["front"]) + len(parts["rear"])
    solids = [t for m in mp[:n_solid] for dd, t in m if dd == 3]
    air = [t for m in mp[n_solid:] for dd, t in m if dd == 3]
    solid_faces = {f for t in solids for _, f in gmsh.model.getBoundary([(3, t)], oriented=False)}
    sign = {}  # +1 si la normale geometrique de la face sort de l'air (donc entre dans la paroi)
    for t in air:
        for _, f in gmsh.model.getBoundary([(3, t)], oriented=True):
            if abs(f) in solid_faces:
                sign[abs(f)] = 1 if f > 0 else -1
    assert sign, "aucune face commune air / parois"
    fix = []
    for f in solid_faces:
        bb = gmsh.model.getBoundingBox(2, f)
        if abs(bb[2] - g.Z_SEAT) < 1e-3 and abs(bb[5] - g.Z_SEAT) < 1e-3:
            fix.append(f)
    assert fix, "appui du col introuvable"
    v_air = sum(gmsh.model.occ.getMass(3, t) for t in air)  # mm3
    gmsh.model.occ.remove([(3, t) for t in air])
    gmsh.model.occ.synchronize()
    gmsh.model.addPhysicalGroup(3, solids, name="pla")
    gmsh.model.addPhysicalGroup(2, fix, name="appui")
    gmsh.model.addPhysicalGroup(2, sorted(sign), name="chambre")
    gmsh.option.setNumber("Mesh.MeshSizeMax", h)
    gmsh.option.setNumber("Mesh.MeshSizeMin", h / 3)
    gmsh.model.mesh.generate(3)
    gmsh.option.setNumber("Mesh.SecondOrderLinear", 1)
    gmsh.model.mesh.setOrder(2)
    gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
    gmsh.write(str(work / "shell.msh"))
    n_nodes = len(gmsh.model.mesh.getNodes()[0])
    gmsh.finalize()
    mat_xml(work / "mat.xml")
    sim_xml(work / "shell.xml", "shell", {"pla": "pla"}, "appui", {"chambre": 1e-6},
            LIS.format(pc=precond, st="sparseNonSym" if precond == "MG" else "sparseSym"))  # 1 Pa = 1e-6 MPa
    t_cfs = run_cfs(work, "shell", max_s=5400)
    res = {"noeuds": n_nodes, "cfs_s": round(t_cfs, 1), "volume_air_cm3": round(v_air / 1000, 1)}
    return shell_post(work, res)


def shell_post(work, res):
    """Variation du volume d'air par pascal : u.n sur les triangles charges, n orientee vers la matiere par le
    tetraedre voisin. Controle : le champ u = x/3 redonne le volume borde par ces faces. Les triangles qui bougent
    plus de 50 fois le 99e centile (lamelles de quelques centiemes de mm laissees par le decoupage, tenues par rien)
    sont ecartes et comptes."""
    from scipy.spatial import cKDTree
    lines = (work / "shell.msh").read_text().split("\n")
    k = lines.index("$PhysicalNames")
    phys = {int(l.split()[1]): l.split()[2].strip('"') for l in lines[k + 2:k + 2 + int(lines[k + 1])]}
    k = lines.index("$Nodes")
    arr = np.array([l.split() for l in lines[k + 2:k + 2 + int(lines[k + 1])]], float)
    pos = {int(t): j for j, t in enumerate(arr[:, 0])}
    P = arr[:, 1:]
    k = lines.index("$Elements")
    tris, tets = [], []
    for l in lines[k + 2:k + 2 + int(lines[k + 1])]:
        v = l.split()
        typ, ntag = int(v[1]), int(v[2])
        nd = [pos[int(x)] for x in v[3 + ntag:]]
        if typ == 9 and phys.get(int(v[3])) == "chambre":
            tris.append(nd[:3])
        elif typ == 11:
            tets.append(nd[:4])
    tris, tets = np.array(tris), np.array(tets)
    opp = {}
    for c in range(4):
        for f, o in zip(map(tuple, np.sort(np.delete(tets, c, axis=1), axis=1)), tets[:, c]):
            opp[f] = o
    o = np.array([opp[tuple(sorted(t))] for t in tris])
    a, b, c = P[tris[:, 0]], P[tris[:, 1]], P[tris[:, 2]]
    nrm = np.cross(b - a, c - a) / 2
    nrm *= np.sign(((P[o] - a) * nrm).sum(1))[:, None]
    xyz, disp, nodes, _ = read(work, "shell")
    _, kk = cKDTree(xyz[nodes["pla"]]).query(np.vstack([a, b, c]))
    u = disp["pla"][kk].reshape(3, len(tris), 3).mean(0)
    mag = np.linalg.norm(u, axis=1)
    ok = mag < 50 * np.percentile(mag, 99)
    dV = float((u[ok] * nrm[ok]).sum())  # mm3 par Pa
    C = dV * 1e-9
    c_air = res.get("volume_air_cm3", 208.5) * 1e-6 / (1.204 * 343.0 ** 2)
    res.update({"controle_volume_cm3": round(float(((a + b + c) / 3 * nrm).sum() / 3 / 1000), 1),
                "aire_chargee_mm2": round(float(np.linalg.norm(nrm, axis=1).sum())),
                "triangles_ecartes": int((~ok).sum()), "aire_ecartee_mm2": round(float(np.linalg.norm(nrm[~ok], axis=1).sum()), 2),
                "souplesse_m3_par_Pa": C, "souplesse_air_m3_par_Pa": c_air, "rapport_paroi_sur_air": C / c_air,
                "hypothese_1d_m3_par_Pa": 26000e-6 / 8.5e9})
    (work / "result.json").write_text(json.dumps(res, indent=1))
    return res


# ---------- capot sur coque : tete fraisee dans le bossage du capot ----------

def boss_model(step, label="joint-v06", h_near=0.3, h_far=1.8, precond="Jacobi"):
    """4 vis du joint : la tete fraisee (90 deg) appuie sur la fraisure du bossage du capot ; le capot est tenu sur
    toutes ses faces du plan de joint (bossages et bords posent sur la coque, butee). Charge : 1 N axial par vis.
    Regarde l'eclatement du bossage par l'effet de coin de la fraisure et la flexion des nervures."""
    sys.path.insert(0, str(ROOT / "cad"))
    import silent_mic_v3_galet as g
    cp = g.cp
    work = WORK / label
    work.mkdir(parents=True, exist_ok=True)
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    shell = gmsh.model.occ.importShapes(str(step))
    low = gmsh.model.occ.addBox(-100, -100, -5.0, 200, 200, 25.0)  # bas du capot : bossages, nervures, paroi
    shell, _ = gmsh.model.occ.intersect(shell, [(3, low)])
    gmsh.model.occ.synchronize()
    vol = [t for d, t in shell if d == 3]
    assert len(vol) == 1, vol
    r, rh, h = cp.SCREW[0] / 2, cp.SCREW[1] / 2, cp.BOSS_FRONT_H
    cones, joint = [], []
    for _, f in gmsh.model.getBoundary([(3, vol[0])], oriented=False):
        bb = gmsh.model.getBoundingBox(2, f)
        # STEP en NURBS : la fraisure se reconnait a sa place (sous le dessus du bossage, autour de l'axe), pas a son type
        # (boites englobantes des NURBS trop larges : centre de gravite sur l'axe, hauteur entre bas et haut de la fraisure)
        c = gmsh.model.occ.getCenterOfMass(2, f)
        if (bb[2] > h - cp.SCREW[2] - 0.1 and bb[5] < h + 0.1 and bb[5] - bb[2] > 0.5
                and any(math.hypot(c[0] - x, c[1] - y) < 0.3 for x, y in g.screw_xy())):
            cones.append(f)
        elif abs(bb[2]) < 1e-3 and abs(bb[5]) < 1e-3:
            joint.append(f)
    assert len(cones) == 4 and joint, (cones, joint)
    gmsh.model.addPhysicalGroup(3, vol, name="pla")
    gmsh.model.addPhysicalGroup(2, cones, name="fraisure")
    gmsh.model.addPhysicalGroup(2, joint, name="plan_joint")
    a_proj = sum(gmsh.model.occ.getMass(2, f) for f in cones) * math.cos(math.radians(45)) / 4
    pts = [gmsh.model.occ.addPoint(x, y, h) for x, y in g.screw_xy()]
    gmsh.model.occ.synchronize()
    fd = gmsh.model.mesh.field.add("Distance")
    gmsh.model.mesh.field.setNumbers(fd, "PointsList", pts)
    ft = gmsh.model.mesh.field.add("Threshold")
    for k, v in (("InField", fd), ("SizeMin", h_near), ("SizeMax", h_far), ("DistMin", 5.0), ("DistMax", 10.0)):
        gmsh.model.mesh.field.setNumber(ft, k, v)
    gmsh.model.mesh.field.setAsBackgroundMesh(ft)
    for k in ("Mesh.MeshSizeExtendFromBoundary", "Mesh.MeshSizeFromPoints", "Mesh.MeshSizeFromCurvature"):
        gmsh.option.setNumber(k, 0)
    n = finish_mesh(work / "col.msh")
    mat_xml(work / "mat.xml")
    sim_xml(work / "col.xml", "col", {"pla": "pla"}, "plan_joint", {"fraisure": 1.0 / a_proj},
            LIS.format(pc=precond, st="sparseNonSym" if precond == "MG" else "sparseSym"))  # 1 N axial par vis
    t_cfs = run_cfs(work, "col", max_s=5400)
    xyz, disp, nodes, st = read(work, "col")
    cen, s = st["pla"]
    xx, yy, zz, yz, xz, xy = s.T
    inpl = (xx + yy) / 2 + np.sqrt(((xx - yy) / 2) ** 2 + xy ** 2)
    out = []
    for x, y in g.screw_xy():
        near = (np.hypot(cen[:, 0] - x, cen[:, 1] - y) < 9.0) & (cen[:, 2] < 20)
        out.append([np.percentile(zz[near], 99), np.percentile(inpl[near], 99), np.percentile(von_mises(s[near]), 99), von_mises(s[near]).max()])
    m = np.array(out).mean(0)
    res = {"noeuds": n, "cfs_s": round(t_cfs, 1), "aire_projetee_fraisure_mm2": a_proj,
           "entre_couches_p99_MPa_par_N": m[0], "plan_p99_MPa_par_N": m[1], "vm_p99_MPa_par_N": m[2], "vm_max_MPa_par_N": m[3]}
    (work / "result.json").write_text(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selfcheck", action="store_true")
    ap.add_argument("--iter", default=None, help="validation avec le gradient conjugue et ce preconditionneur (MG, ILDLK, Jacobi)")
    ap.add_argument("--col", action="store_true")
    ap.add_argument("--shell", action="store_true")
    ap.add_argument("--boss", action="store_true")
    ap.add_argument("--post", help="relit un calcul deja fait (col-v05, col-v06, coque) sans le relancer")
    ap.add_argument("--step", default=str(ROOT / "cad/out/v3-galet/silent-mic-v3-galet-front.step"))
    ap.add_argument("--label", default="col-v06")
    ap.add_argument("--h-near", type=float, default=0.3)
    ap.add_argument("--precond", default="MG")
    a = ap.parse_args()
    if a.selfcheck:
        sys.exit(0 if selfcheck(a.iter) else 1)
    if a.col:
        print(json.dumps(col_model(Path(a.step), a.label, a.h_near, precond=a.precond), indent=1))
    if a.post:
        w = WORK / a.post
        r = json.loads((w / "result.json").read_text())
        if a.post == "coque":
            print(json.dumps(shell_post(w, {k: r[k] for k in ("noeuds", "cfs_s") if k in r}), indent=1))
        else:
            sys.path.insert(0, str(ROOT / "cad"))
            import silent_mic_v3_galet as g
            ceil = [(e["xy"][0], e["xy"][1], g.Z_SEAT - e["peau_mm"]) for e in r["ecrous"]]
            print(json.dumps(col_post(w, ceil, {k: r[k] for k in ("step", "noeuds", "maillage_s", "cfs_s")}), indent=1))
    if a.boss:
        print(json.dumps(boss_model(Path(a.step), precond=a.precond), indent=1))
    if a.shell:
        print(json.dumps(shell_model(precond=a.precond), indent=1))
