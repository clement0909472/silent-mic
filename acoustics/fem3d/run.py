# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright 2026 Clement Barberousse
"""Simulation acoustique 3D (openCFS, harmonique) du galet v3 assemble, bouche appliquee sur le coussin.

    python acoustics/fem3d/run.py --selfcheck        # tube 3D termine par une impedance : convention et puissance
    python acoustics/fem3d/run.py [--per-band 3]      # galet : perte par insertion, dB(A) voix, niveau au micro

Modele : air de la chambre et du conduit tel que dessine (cad/out/v3-galet/silent-mic-v3-galet-technical.step),
mousses melamine en fluide equivalent (Delany-Bazley, sigma 12 000 Pa.s/m2, comme acoustics/tmm.py), conduit et
fentes en fluide de Zwikker-Kosten (pertes visqueuses), parois rigides, joint capot/coque et coussin hermetiques,
visage rigide. Source : bouche = disque de 10 mm de rayon vibrant a 1 m/s dans le plan du visage. Sortie : les
ouvertures vers l'exterieur (5 fentes et leur gorge d'ombre, 434 mm2 au maillage) portent l'impedance de rayonnement
d'un piston bafle de cette surface (sources en phase ; a basse frequence elle ne depend pas de la surface).
Debit et puissance de sortie sont recalcules sur les triangles des ouvertures a partir des pressions nodales.
shortcut: rayonnement par impedance de piston bafle aux fentes, sans domaine exterieur ni PML ; a remplacer par un
demi-espace maille si l'on veut la directivite ou l'effet d'ecran du corps.
Perte par insertion = puissance de la bouche nue (piston bafle, exact) / puissance sortie par les fentes.
Tous les dB sont des estimations de modele, non mesures. Sortie : acoustics/fem3d/work/result.json.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import subprocess
import sys
import time
from pathlib import Path

import h5py
import numpy as np
from scipy.special import j1, struve

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import tmm  # noqa: E402
from tmm import A_WEIGHT, BANDS, C0, RHO, SPEECH_1M  # noqa: E402

import mesh3d  # noqa: E402


def speech_dba(il):
    """Comme acoustics/fem/run.py : attenuation de la voix normale ponderee A, bandes 100 Hz et plus."""
    n = len(il)
    open_a = SPEECH_1M[:n] + A_WEIGHT[:n]
    return float(10 * np.log10(np.sum(10 ** (open_a / 10))) - 10 * np.log10(np.sum(10 ** ((open_a - il) / 10))))

WORK = HERE / "work"
MIC = (0.0, 0.0, -2.0)  # mm : 1 mm au-dessus du dessus du DJI (ref-mic, z de -31 a -3), capsule sous la bonnette
CAV = (0.0, 12.0, -15.0)  # mm : un point de la chambre, a cote du micro


def z_piston(f, area):
    """Impedance specifique (Pa.s/m) d'un piston plan bafle de surface area (m2), convention e^{jwt}."""
    a = math.sqrt(area / math.pi)
    x = 2 * (2 * np.pi * f / C0) * a
    return RHO * C0 * ((1 - 2 * j1(x) / x) + 1j * 2 * struve(1, x) / x)


def materials(ftab):
    w = 2 * np.pi * ftab
    duct = next(e for e in tmm_design()["vent"]["elements"] if e["type"] == "duct" and e.get("count", 1) == 1)
    slot = next(e for e in tmm_design()["vent"]["elements"] if e["type"] == "duct" and e.get("count", 1) > 1)
    rh = lambda e: e["width"] * e["height"] / (e["width"] + e["height"]) * 1e-3  # comme acoustics/fem/run.py
    foam = tmm.delany_bazley(w, tmm_design()["cavity"].get("foam_sigma", 1.2e4))
    return {"foam_disc": foam, "foam_liner": foam, "duct": tmm.zk_fluid(w, rh(duct)), "slots": tmm.zk_fluid(w, rh(slot))}


def tmm_design():
    return next(d for d in json.loads((HERE.parent / "params.json").read_text())["designs"] if d["name"] == "v3-galet")


def write_inputs(work, mats, ftab, z_spec):
    xml = ['<?xml version="1.0"?>\n<cfsMaterialDataBase xmlns="http://www.cfs++.org/material">',
           mat_xml("air", RHO, 0, RHO * C0 ** 2, 0)]
    for name, (rho, kap) in mats.items():
        for tag, arr in (("rhoR", rho.real), ("rhoI", rho.imag), ("kR", kap.real), ("kI", kap.imag)):
            np.savetxt(work / f"{name}_{tag}.txt", np.c_[ftab, arr], fmt="%.8e")
        xml.append(mat_xml(name, *[f"sample1D('{name}_{t}.txt',f,1)" for t in ("rhoR", "rhoI", "kR", "kI")]))
    xml.append("</cfsMaterialDataBase>")
    (work / "mat.xml").write_text("\n".join(xml))
    np.savetxt(work / "zrad_re.txt", np.c_[ftab, z_spec.real], fmt="%.8e")
    np.savetxt(work / "zrad_im.txt", np.c_[ftab, z_spec.imag], fmt="%.8e")


def mat_xml(name, rr, ri, kr, ki):
    return (f'<material name="{name}"><acoustic>'
            f"<density><linear><real>{rr}</real><imag>{ri}</imag></linear></density>"
            f"<compressionModulus><linear><real>{kr}</real><imag>{ki}</imag></linear></compressionModulus>"
            "</acoustic></material>")


def write_sim(work, job, regions, freqs, points, source, imp_surf, imp_vol):
    complex_r = [r for r in regions if r != "air"]
    reg = "".join(f'<region name="{r}" material="{r}"/>' for r in regions)
    pde = "".join(f'<region name="{r}"' + (' complexFluid="yes"' if r in complex_r else "") + "/>" for r in regions)
    surfs = sorted({source[1], imp_surf})
    nodes = "".join(f'<nodes name="{n}"><coord x="{x}" y="{y}" z="{z}"/></nodes>' for n, (x, y, z) in points.items())
    src = (f'<normalVelocity name="{source[1]}" value="1.0"/>' if source[0] == "v"
           else f'<pressure name="{source[1]}" value="1.0"/>')
    xml = f"""<?xml version="1.0"?>
<cfsSimulation xmlns="http://www.cfs++.org/simulation">
  <fileFormats>
    <input><gmsh fileName="{job}.msh"/></input>
    <output><hdf5/></output>
    <materialData file="mat.xml" format="xml"/>
  </fileFormats>
  <domain geometryType="3d">
    <regionList>{reg}</regionList>
    <surfRegionList>{"".join(f'<surfRegion name="{s}"/>' for s in surfs)}</surfRegionList>
    <nodeList>{nodes}</nodeList>
  </domain>
  <sequenceStep>
    <analysis><harmonic><frequencyList>{"".join(f'<freq value="{f:.4f}"/>' for f in freqs)}</frequencyList></harmonic></analysis>
    <pdeList>
      <acoustic formulation="acouPressure">
        <regionList>{pde}</regionList>
        <bcsAndLoads>{src}<impedance name="{imp_surf}" volumeRegion="{imp_vol}" impedanceId="zrad"/></bcsAndLoads>
        <impedanceList><interpolImpedance id="zrad"><dataName_real>zrad_re.txt</dataName_real><dataName_imag>zrad_im.txt</dataName_imag></interpolImpedance></impedanceList>
        <storeResults>
          <surfRegionResult type="acouPower"><surfRegionList>{"".join(f'<surfRegion name="{s}"/>' for s in surfs)}</surfRegionList></surfRegionResult>
          <nodeResult type="acouPressure" complexFormat="realImag"><regionList><region name="{imp_surf}"/></regionList><nodeList>{"".join(f'<nodes name="{n}"/>' for n in points)}</nodeList></nodeResult>
        </storeResults>
      </acoustic>
    </pdeList>
  </sequenceStep>
</cfsSimulation>
"""
    (work / f"{job}.xml").write_text(xml)


def run_cfs(work, job):
    t = time.time()
    p = subprocess.run(["cfs", "-q", "-p", f"{job}.xml", job], cwd=work, capture_output=True, text=True)
    if p.returncode != 0 or not (work / "results_hdf5" / f"{job}.cfs").exists():
        raise RuntimeError(f"cfs a echoue ({job}) :\n{p.stdout[-3000:]}\n{p.stderr[-3000:]}")
    return time.time() - t


def outlet_flow(work, job, msh, z_spec, surf="outlets"):
    """Debit U et puissance P sortant par la surface d'impedance, par frequence, recalcules sur ses triangles a partir
    des pressions nodales (v = p / z). L'acouPower d'openCFS sur cette surface s'est montre faux sur le galet (x13 a
    100 Hz, gradient mal estime sur les petites faces des fentes) alors qu'il etait juste sur le tube de validation."""
    lines = msh.read_text().split("\n")
    k = lines.index("$PhysicalNames")
    names = {int(l.split()[1]): l.split()[2].strip('"') for l in lines[k + 2:k + 2 + int(lines[k + 1])]}
    j = lines.index("$Elements")
    tri = np.array([[int(x) - 1 for x in l.split()[5:8]] for l in lines[j + 2:j + 2 + int(lines[j + 1])]
                    if l.split()[1] == "2" and names[int(l.split()[3])] == surf])
    with h5py.File(work / "results_hdf5" / f"{job}.cfs", "r") as f:
        xyz = f["Mesh/Nodes/Coordinates"][:]
        nodes = f[f"Mesh/Regions/{surf}/Nodes"][:] - 1
        steps = f["Results/Mesh/MultiStep_1"]
        keys = sorted((k for k in steps if k.startswith("Step_")), key=lambda k: int(k.split("_")[1]))
        p = np.array([steps[k]["acouPressure"][surf]["Nodes"]["Real"][:].ravel()
                      + 1j * steps[k]["acouPressure"][surf]["Nodes"]["Imag"][:].ravel() for k in keys])
    col = np.full(len(xyz), -1)
    col[nodes] = np.arange(len(nodes))
    area = 0.5 * np.linalg.norm(np.cross(xyz[tri[:, 1]] - xyz[tri[:, 0]], xyz[tri[:, 2]] - xyz[tri[:, 0]]), axis=1)
    pt = p[:, col[tri]].mean(2)  # pression moyenne de chaque triangle, par frequence
    u = (pt / z_spec[:, None] * area).sum(1)
    pw = (np.abs(pt) ** 2 * (1 / np.conj(z_spec))[:, None].real * area).sum(1)
    return u, pw


def read_history(work, job, names):
    power, pres = {}, {}
    with h5py.File(work / "results_hdf5" / f"{job}.cfs", "r") as f:
        hist = f["Results/History/MultiStep_1"]
        for name, g in hist["acouPower/ElementGroup"].items():
            power[name] = (g["Real"][:] + 1j * g["Imag"][:]).ravel()
        xyz = f["Mesh/Nodes/Coordinates"][:]
        for nid, g in hist["acouPressure/Nodes"].items():
            pres[tuple(xyz[int(nid) - 1].round(5))] = (g["Real"][:] + 1j * g["Imag"][:]).ravel()
    # un point par nom, dans l'ordre de la nodeList (noeud le plus proche de chaque coordonnee demandee)
    out = {}
    for n, c in names.items():
        k = min(pres, key=lambda q: np.linalg.norm(np.array(q) - np.array(c)))
        out[n] = pres[k]
        out[n + "_xyz"] = np.array(k)  # coordonnees du noeud retenu
    return power, out


# ---------- validation : tube 3D termine par une impedance ----------

def selfcheck():
    """Tube 8 x 8 x 200 mm, pression 1 Pa a l'entree, impedance z = rho c (0.4 + 0.9j) a la sortie.
    Attendu : R = (z - rho c) / (z + rho c) (convention e^{jwt}) et puissance sortante |p|^2 Re(1/z*) S."""
    import gmsh
    work = WORK / "selfcheck"
    work.mkdir(parents=True, exist_ok=True)
    L, s = 0.2, 0.008
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.occ.addBox(0, 0, 0, s, s, L)
    gmsh.model.occ.synchronize()
    faces = {round(gmsh.model.occ.getCenterOfMass(2, t)[2], 4): t for _, t in gmsh.model.getEntities(2)}
    gmsh.model.addPhysicalGroup(3, [1], name="air")
    gmsh.model.addPhysicalGroup(2, [faces[0.0]], name="inlet")
    gmsh.model.addPhysicalGroup(2, [faces[L]], name="outlets")
    gmsh.option.setNumber("Mesh.MeshSizeMax", 0.002)
    gmsh.model.mesh.generate(3)
    gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
    gmsh.write(str(work / "tube.msh"))
    gmsh.finalize()
    freqs = np.array([200.0, 500.0, 1000.0, 1500.0])
    ftab = np.geomspace(100, 3000, 40)
    zr = RHO * C0 * (0.4 + 0.9j) * np.ones_like(ftab)
    write_inputs(work, {}, ftab, zr)
    z1, z2 = 0.05, 0.08
    pts = {"m1": (s / 2, s / 2, z1), "m2": (s / 2, s / 2, z2), "end": (s / 2, s / 2, L)}
    write_sim(work, "tube", ["air"], freqs, pts, ("p", "inlet"), "outlets", "air")
    run_cfs(work, "tube")
    power, p = read_history(work, "tube", pts)
    k = 2 * np.pi * freqs / C0
    zc = RHO * C0 * (0.4 + 0.9j)
    r_th = (zc - RHO * C0) / (zc + RHO * C0)
    # p(z) = A e^{-jkz} + B e^{jkz} ; R a la sortie = B e^{jkL} / (A e^{-jkL})
    z1, z2 = p["m1_xyz"][2], p["m2_xyz"][2]  # noeuds reellement lus
    m = np.array([[np.exp(-1j * k * z1), np.exp(1j * k * z1)], [np.exp(-1j * k * z2), np.exp(1j * k * z2)]])
    ab = np.linalg.solve(np.moveaxis(m, -1, 0), np.stack([p["m1"], p["m2"]], -1)[..., None])[..., 0]
    r_fem = ab[:, 1] * np.exp(1j * k * L) / (ab[:, 0] * np.exp(-1j * k * L))
    p_th = np.abs(p["end"]) ** 2 * (1 / np.conj(zc)).real * s * s
    rows = []
    for i, f in enumerate(freqs):
        rows.append((f, abs(r_fem[i] - r_th), power["outlets"][i].real / p_th[i]))
        print(f"{f:6.0f} Hz : R FEM {r_fem[i]:.3f} / attendu {r_th:.3f} ; puissance sortie / |p|^2 Re(1/z*) S = {rows[-1][2]:.3f}")
    _, pw = outlet_flow(work, "tube", work / "tube.msh", zc * np.ones(len(freqs)))
    print("puissance recalculee sur les triangles / acouPower :", (pw / power["outlets"].real).round(3))
    assert np.allclose(pw, power["outlets"].real, rtol=0.03), "puissance recalculee incoherente"
    worst = max(r[1] for r in rows)
    assert worst < 0.03, f"impedance : convention ou valeur fausse ({worst:.3f})"
    assert all(abs(r[2] - 1) < 0.05 for r in rows), "puissance sortante incoherente"
    print(f"selfcheck OK : |R FEM - R attendu| <= {worst:.3f}")


# ---------- galet assemble ----------

def band_freqs(fc, n):
    return np.array([fc * 2 ** ((k + 0.5) / n / 3 - 1 / 6) for k in range(n)])


def galet(per_band, fmax, remesh, h_wall=0.8, h_bulk=3.5, name="galet"):
    work = WORK / name
    work.mkdir(parents=True, exist_ok=True)
    msh = work / "galet.msh"
    info_path = work / "mesh.json"
    if remesh or not msh.exists():
        t = time.time()
        info = mesh3d.build(msh, h_wall, h_bulk)
        info["t_mesh_s"] = round(time.time() - t, 1)
        info_path.write_text(json.dumps(info, indent=1, ensure_ascii=False))
    info = json.loads(info_path.read_text())
    nb = int(np.searchsorted(BANDS, fmax)) + 1
    freqs = np.concatenate([band_freqs(fc, per_band) for fc in BANDS[:nb]])
    ftab = np.geomspace(freqs[0] / 1.02, freqs[-1] * 1.02, 120)
    a_out = info["outlets_mm2"] * 1e-6
    write_inputs(work, materials(ftab), ftab, z_piston(ftab, a_out))
    regions = ["air", "foam_disc", "foam_liner", "duct", "slots"]
    pts = {"mic": tuple(c * 1e-3 for c in MIC), "cav": tuple(c * 1e-3 for c in CAV)}
    write_sim(work, "galet", regions, freqs, pts, ("v", "mouth"), "outlets", "slots")
    t_cfs = run_cfs(work, "galet")
    power, p = read_history(work, "galet", pts)

    s_m = info["mouth_mm2"] * 1e-6
    q = s_m * 1.0  # debit de la bouche (vitesse normale 1 m/s)
    k = 2 * np.pi * freqs / C0
    a = math.sqrt(s_m / math.pi)
    p_ref = RHO * C0 * s_m * (1 - 2 * j1(2 * k * a) / (2 * k * a))  # bouche nue, piston bafle (sans le 1/2, comme openCFS)
    zs = z_piston(freqs, a_out)
    u_out, p_out = outlet_flow(work, "galet", msh, zs)
    u_out2 = np.abs(u_out) ** 2
    per = lambda v: np.asarray(v).reshape(nb, per_band).mean(1)
    il = -10 * np.log10(per(p_out / p_ref))
    il_u = -10 * np.log10(per(u_out2 / q ** 2))
    w = 2 * np.pi * freqs
    gain = lambda pp: 10 * np.log10(per((np.abs(pp / q) * 4 * np.pi / (RHO * w)) ** 2))  # p / p_1m bouche nue
    mic_bands = SPEECH_1M[:nb] + gain(p["mic"])
    mic_spl = 10 * np.log10(np.sum(10 ** (mic_bands / 10)))

    d = tmm_design()
    d0 = copy.deepcopy(d)
    d0["seal"]["gap_mm"] = 0.0
    ev = tmm.evaluate(d0)
    fem2d = HERE.parent / "fem" / "work" / "v3-galet" / "result.json"
    c2 = json.loads(fem2d.read_text())["cases"].get("gap_0.0mm") if fem2d.exists() else None
    res = {
        "modele": "3D openCFS, air dessine + mousses Delany-Bazley + conduit et fentes Zwikker-Kosten, joint et coussin "
                  "hermetiques, visage rigide, fentes rayonnant comme un piston bafle (estimation, non mesure)",
        "bands": BANDS[:nb].tolist(), "per_band": per_band, "n_freq": len(freqs),
        "il_fem3d": il.round(2).tolist(), "il_fem3d_debit": il_u.round(2).tolist(),
        "speech_dba_fem3d": round(speech_dba(il), 2), "speech_dba_fem3d_debit": round(speech_dba(il_u), 2),
        "mic_spl_normal_db": round(float(mic_spl), 1), "mic_peak_normal_db": round(float(mic_spl) + 12, 1),
        "mic_bands_db": mic_bands.round(1).tolist(), "cav_gain_db": gain(p["cav"]).round(1).tolist(),
        "mic_gain_db": gain(p["mic"]).round(1).tolist(),
        "acoupower_openCFS_sur_recalcule_sorties": per(power["outlets"].real / p_out).round(2).tolist(),
        "tmm_1d_hermetique": {"il": ev["il_bands"][:nb].round(2).tolist(), "speech_dba": round(float(ev["speech_dba"]), 2),
                              "mic_spl_normal": round(float(ev["mic_spl_normal"]), 1)},
        "fem2d_hermetique": {"il": c2["il_fem"], "speech_dba": c2["speech_dba_fem"]} if c2 else None,
        "maillage": info, "t_cfs_s": round(t_cfs, 1), "t_par_frequence_s": round(t_cfs / len(freqs), 2),
    }
    (work / "result.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selfcheck", action="store_true")
    ap.add_argument("--per-band", type=int, default=3)
    ap.add_argument("--fmax", type=float, default=8000)
    ap.add_argument("--remesh", action="store_true")
    ap.add_argument("--h-wall", type=float, default=0.8, help="maille pres des parois (mm)")
    ap.add_argument("--h-bulk", type=float, default=3.5, help="maille au coeur de la chambre (mm)")
    ap.add_argument("--name", default="galet", help="sous-dossier de work/")
    a = ap.parse_args()
    if a.selfcheck:
        selfcheck()
        return
    r = galet(a.per_band, a.fmax, a.remesh, a.h_wall, a.h_bulk, a.name)
    print(f"3D : {r['speech_dba_fem3d']:.1f} dB(A) (debit : {r['speech_dba_fem3d_debit']:.1f}) ; 1D hermetique "
          f"{r['tmm_1d_hermetique']['speech_dba']:.1f} ; 2D hermetique "
          f"{r['fem2d_hermetique']['speech_dba'] if r['fem2d_hermetique'] else 'n/a'} ; micro {r['mic_spl_normal_db']:.0f} dB SPL")
    print("| Hz | " + " | ".join(f"{b:.0f}" for b in r["bands"]) + " |")
    print("|---|" + "---|" * len(r["bands"]))
    for key, v in (("IL 3D", r["il_fem3d"]), ("IL 3D debit", r["il_fem3d_debit"]), ("IL 1D", r["tmm_1d_hermetique"]["il"]),
                   ("IL 2D", r["fem2d_hermetique"]["il"] if r["fem2d_hermetique"] else None), ("micro dB", r["mic_bands_db"])):
        if v:
            print(f"| {key} | " + " | ".join(f"{x:.1f}" for x in v[:len(r['bands'])]) + " |")
    print(f"cfs {r['t_cfs_s']} s ({r['t_par_frequence_s']} s par frequence) -> {WORK / a.name / 'result.json'}")


if __name__ == "__main__":
    main()
