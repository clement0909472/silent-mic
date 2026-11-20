# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright 2026 Clement Barberousse
"""Chaine elements finis openCFS (2D axisymetrique) pour la perte par insertion de Silent Mic.

Usage :
    python acoustics/fem/run.py --selfcheck            # piston bafle vs formule exacte
    python acoustics/fem/run.py --design v3-A          # jeux 0 et 0,2 mm (perimetre complet)
    python acoustics/fem/run.py --design v2-compact

Perte par insertion = 10 log10(P rayonnee bouche nue / P rayonnee avec dispositif), puissances
integrees (acouPower) sur une frontiere air/air avant la PML, meme source de debit (vitesse imposee
sur la bouche). Sortie : acoustics/fem/work/<design>/result.json.
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
from scipy.special import j1

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import tmm  # noqa: E402
from tmm import A_WEIGHT, BANDS, C0, MU, RHO, SPEECH_1M  # noqa: E402

import mesh  # noqa: E402

MOUTH_R = 10e-3
PER_BAND = 6


def band_freqs(fc):
    """PER_BAND frequences geometriques dans la bande de tiers d'octave fc."""
    return np.array([fc * 2 ** ((k + 0.5) / PER_BAND / 3 - 1 / 6) for k in range(PER_BAND)])


def box_for(fc, r_dev, z_dev):
    """Domaine par bande : la PML axi reflechit en basses frequences si elle est a moins d'environ
    0,6 lambda de la source (piston : +230 % de puissance a 100 Hz avec 0,12 m, 0,3 % avec 4 m).
    Marge = max(0,6 lambda a la frequence basse, 7 cm) ; h <= lambda/6 a la frequence haute."""
    lam_lo, lam_hi = C0 / (fc * 2 ** (-1 / 6)), C0 / (fc * 2 ** (1 / 6))
    m = max(0.6 * lam_lo, 0.07)
    h = min(lam_hi / 6, 0.1)
    return (r_dev + m, z_dev + m, h, m / 2), h


# ---------- materiaux (fluides equivalents tabules en frequence, convention e^{jwt}) ----------

def materials(design, gap_mm, pieces, ftab):
    w = 2 * np.pi * ftab
    out = {}
    cav = design["cavity"]
    out["foam_cav"] = tmm.delany_bazley(w, cav.get("foam_sigma", 1.2e4))
    if gap_mm > 0:
        h = gap_mm * 1e-3
        out["slit"] = (6 * RHO / 5 + 12 * MU / (1j * w * h * h), RHO * C0 ** 2 + 0j * w)  # Poiseuille plan, = tmm.z_slit
    for i, e in enumerate(design["vent"]["elements"]):
        if e["type"] == "duct":
            out[f"vent{i}"] = tmm.zk_fluid(w, e["width"] * e["height"] / (e["width"] + e["height"]) * 1e-3)
        elif e["type"] == "hole":
            out[f"vent{i}"] = tmm.zk_fluid(w, e["diameter"] / 2 * 1e-3)
        elif e["type"] == "chamber" and e.get("foam_cm3"):
            out[f"foam{i}"] = tmm.delany_bazley(w, e.get("foam_sigma", 1.2e4))
    used = {p[1] for p in pieces}
    return {k: v for k, v in out.items() if k in used}


def write_materials(work, mats, ftab):
    xml = ['<?xml version="1.0"?>\n<cfsMaterialDataBase xmlns="http://www.cfs++.org/material">',
           mat_xml("air", RHO, 0, RHO * C0 ** 2, 0)]
    for name, (rho, kap) in mats.items():
        for tag, arr in (("rhoR", rho.real), ("rhoI", rho.imag), ("kR", kap.real), ("kI", kap.imag)):
            np.savetxt(work / f"{name}_{tag}.txt", np.c_[ftab, arr], fmt="%.8e")
        s = [f"sample1D('{name}_{t}.txt',f,1)" for t in ("rhoR", "rhoI", "kR", "kI")]
        xml.append(mat_xml(name, *s))
    xml.append("</cfsMaterialDataBase>")
    (work / "mat.xml").write_text("\n".join(xml))


def mat_xml(name, rr, ri, kr, ki):
    return (f'<material name="{name}"><acoustic>'
            f"<density><linear><real>{rr}</real><imag>{ri}</imag></linear></density>"
            f"<compressionModulus><linear><real>{kr}</real><imag>{ki}</imag></linear></compressionModulus>"
            "</acoustic></material>")


# ---------- XML de simulation ----------

def write_sim(work, job, regions, complex_regions, lines, freqs, points):
    reg = "".join(f'<region name="{r}" material="{complex_regions.get(r, "air")}"/>' for r in regions)
    pde_reg = "".join(
        f'<region name="{r}"' + (' dampingId="pml"' if r == "pml" else "") + (' complexFluid="yes"' if r in complex_regions else "") + "/>"
        for r in regions)
    surf = "".join(f'<surfRegion name="{s}"/>' for s in lines)
    nodes = "".join(f'<nodes name="{n}"><coord r="{r}" z="{z}"/></nodes>' for n, (r, z) in points.items())
    fl = "".join(f'<freq value="{f:.4f}"/>' for f in freqs)
    power = "".join(f'<surfRegion name="{s}"/>' for s in lines if s != "mouth")
    node_res = (f'<nodeResult type="acouPressure" complexFormat="realImag"><nodeList>'
                + "".join(f'<nodes name="{n}"/>' for n in points) + "</nodeList></nodeResult>") if points else ""
    xml = f"""<?xml version="1.0"?>
<cfsSimulation xmlns="http://www.cfs++.org/simulation">
  <fileFormats>
    <input><gmsh fileName="{job}.msh"/></input>
    <output><hdf5/></output>
    <materialData file="mat.xml" format="xml"/>
  </fileFormats>
  <domain geometryType="axi">
    <regionList>{reg}</regionList>
    <surfRegionList>{surf}</surfRegionList>
    <nodeList>{nodes}</nodeList>
  </domain>
  <sequenceStep>
    <analysis><harmonic><frequencyList>{fl}</frequencyList></harmonic></analysis>
    <pdeList>
      <acoustic formulation="acouPressure">
        <regionList>{pde_reg}</regionList>
        <dampingList><pml id="pml"><type>inverseDist</type><dampFactor>1.0</dampFactor></pml></dampingList>
        <bcsAndLoads><normalVelocity name="mouth" value="1.0"/></bcsAndLoads>
        <storeResults>
          <surfRegionResult type="acouPower"><surfRegionList>{power}</surfRegionList></surfRegionResult>
          {node_res}
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


def read_history(work, job):
    """Resultats d'historique du HDF5 : acouPower par surface, acouPressure par noeud {(r, z): valeurs}."""
    power, pres = {}, {}
    with h5py.File(work / "results_hdf5" / f"{job}.cfs", "r") as f:
        xyz = f["Mesh/Nodes/Coordinates"][:]
        hist = f["Results/History/MultiStep_1"]
        for name, g in hist["acouPower/ElementGroup"].items():
            power[name] = (g["Real"][:] + 1j * g["Imag"][:]).ravel()
        if "acouPressure" in hist:
            for nid, g in hist["acouPressure/Nodes"].items():
                pres[tuple(xyz[int(nid) - 1, :2])] = (g["Real"][:] + 1j * g["Imag"][:]).ravel()
    return power, pres


def simulate(work, job, design, gap, pieces, hulls, fc, points=None, mouth_r=MOUTH_R, dev=None):
    """Une bande de tiers d'octave : maillage, materiaux, XML, cfs, lecture. dev = (r, z) du dispositif."""
    work.mkdir(parents=True, exist_ok=True)
    freqs = band_freqs(fc)
    ftab = np.geomspace(freqs[0] / 1.01, freqs[-1] * 1.01, 50)
    write_materials(work, materials(design, gap, pieces, ftab) if pieces else {}, ftab)
    r_dev, z_dev = dev or (mouth_r, 0.0)
    box, h = box_for(fc, r_dev, z_dev)
    t = time.time()
    regions, lines, nnodes = mesh.build(work / f"{job}.msh", pieces, hulls, mouth_r, box, h)
    t_mesh = time.time() - t
    complex_regions = {p[0]: p[1] for p in pieces if p[1] != "air"}
    write_sim(work, job, regions, complex_regions, lines, freqs, points or {})
    t_cfs = run_cfs(work, job)
    power, pres = read_history(work, job)
    return {"f": freqs, "power": power, "pres": pres, "nodes": nnodes, "t_mesh": t_mesh, "t_cfs": t_cfs}


# ---------- validation analytique : piston plan bafle ----------

def selfcheck(work):
    """Piston rigide de rayon a dans un baffle infini (meme bouche, meme axi + PML que les calculs).
    Puissance exacte (sans le 1/2, openCFS integre Re(p v*)) : rho c S v^2 (1 - J1(2ka)/ka).
    Pression exacte sur l'axe : rho c v (e^{-jkz} - e^{-jk sqrt(z^2+a^2)})."""
    rows, t_tot, n_f = [], 0.0, 0
    for fc in BANDS:
        z = 0.05  # dans la boite d air meme aux hautes bandes (marge 7 cm)
        r = simulate(work / "selfcheck", "piston", None, 0, [], [], fc, {"axe": (0.0, z)})
        f = r["f"]
        k, a = 2 * np.pi * f / C0, MOUTH_R
        p_th = RHO * C0 * MOUTH_R ** 2 * np.pi * (1 - 2 * j1(2 * k * a) / (2 * k * a))
        (zz, pz), = ((key[1], v) for key, v in r["pres"].items())
        pa = RHO * C0 * (np.exp(-1j * k * zz) - np.exp(-1j * k * np.hypot(zz, a)))
        e_p = 10 * np.log10(r["power"]["far"].real.mean() / p_th.mean())
        e_axis = 20 * np.log10(np.abs(pz).mean() / np.abs(pa).mean())
        rows.append((fc, e_p, e_axis, r["nodes"]))
        t_tot += r["t_cfs"]
        n_f += len(f)
    print("| bande Hz | erreur puissance dB | erreur pression axe dB | noeuds |")
    print("|---|---|---|---|")
    for fc, e1, e2, n in rows:
        print(f"| {fc:.0f} | {e1:+.2f} | {e2:+.2f} | {n} |")
    worst = max(abs(x[1]) for x in rows)
    print(f"pire erreur puissance : {worst:.2f} dB ; cfs {t_tot:.1f} s pour {n_f} frequences")
    assert worst < 0.5, "validation piston hors tolerance (0,5 dB)"
    return rows


# ---------- comparaison TMM ----------

def tmm_equivalent(design, gap_mm, geo):
    """Meme design avec les simplifications FEM : sans ecrans, parois rigides, fente sur tout le perimetre,
    sortie = section du dernier conduit."""
    d = copy.deepcopy(design)
    d["vent"]["elements"] = [e for e in d["vent"]["elements"] if e["type"] != "screen"]
    d["vent"]["outlet_area_mm2"] = math.pi * (geo["r_out"] * 1e3) ** 2
    d["seal"]["soft_wall_area_mm2"] = 0.0
    d.pop("shell", None)
    d["seal"]["gap_mm"] = gap_mm
    R, depth = geo["R"] * 1e3, d["seal"]["contact_depth_mm"]
    d["seal"]["leak_width_mm"] = 2 * math.pi * depth / math.log((R + depth) / R)  # anneau radial equivalent
    return d


def speech_dba(il):
    n = len(il)
    open_a = SPEECH_1M[:n] + A_WEIGHT[:n]
    return float(10 * np.log10(np.sum(10 ** (open_a / 10))) - 10 * np.log10(np.sum(10 ** ((open_a - il) / 10))))


def tube_volume_velocity(pres, w, rho_e, k_e, area, z_out):
    """Debit a la sortie du dernier conduit par deux pressions sur l'axe (ondes planes dans le fluide equivalent)."""
    (z1, p1), (z2, p2) = sorted((key[1], v) for key, v in pres.items())
    kk, zc = w * np.sqrt(rho_e / k_e), np.sqrt(rho_e * k_e) / area
    a_mat = np.array([[np.exp(-1j * kk * z1), np.exp(1j * kk * z1)], [np.exp(-1j * kk * z2), np.exp(1j * kk * z2)]])
    a_mat = np.moveaxis(a_mat, -1, 0)
    ab = np.linalg.solve(a_mat, np.stack([p1, p2], -1)[..., None])[..., 0]
    return (ab[:, 0] * np.exp(-1j * kk * z_out) - ab[:, 1] * np.exp(1j * kk * z_out)) / zc


def run_design(design, gaps, fmax, work):
    nb = int(np.searchsorted(BANDS, fmax)) + 1
    q = np.pi * MOUTH_R ** 2  # debit de la bouche (vitesse normale 1 m/s)
    out = {"design": design["name"], "bands": BANDS[:nb].tolist(), "cases": {}}
    ref = {}
    t0 = time.time()
    for gap in gaps:
        pieces, hulls, geo = mesh.device_pieces(design, gap)
        dev = (max(h[0] for h in hulls), geo["z_out"])
        last = [p for p in pieces if p[0].startswith("vent") and not p[0].endswith("foam")][-1]
        z_out, r_out = last[5], last[3]
        # deux micros dans le dernier conduit s'il est assez long (v3-A : 200 mm ; v2 : trous de 4 mm, non mesurable)
        mics = z_out - last[4] >= 0.03
        points = {"m1": (0.0, z_out - 0.025), "m2": (0.0, z_out - 0.005)} if mics else {}
        rows = {k: [] for k in ("il", "il_u", "pcav")}
        t_cfs = n_f = 0
        for fc in BANDS[:nb]:
            f = band_freqs(fc)
            if fc not in ref:  # reference bouche nue, meme boite que le dispositif
                ref[fc] = simulate(work / f"ref-{fc:.0f}", "ref", design, 0, [], [], fc, dev=dev)
            r = simulate(work / f"gap{gap}-{fc:.0f}", "dev", design, gap, pieces, hulls, fc,
                         dict(points, pcav=(0.0, geo["L"] / 2)), dev=dev)
            p_ref = ref[fc]["power"]["far"].real
            rows["il"].append(np.mean(r["power"]["far"].real / p_ref))
            pcav = {k: v for k, v in r["pres"].items() if abs(k[1] - geo["L"] / 2) < 0.005}
            if mics:
                tube = {k: v for k, v in r["pres"].items() if k not in pcav}
                rho_e, k_e = materials(design, 0, [last], f)[last[1]]
                u = tube_volume_velocity(tube, 2 * np.pi * f, rho_e, k_e, np.pi * r_out ** 2, z_out)
                rows["il_u"].append(np.mean(np.abs(u / q) ** 2))
            rows["pcav"].append(np.mean(np.abs(next(iter(pcav.values())) / q) ** 2))
            t_cfs += r["t_cfs"] + ref[fc]["t_cfs"]
            n_f += len(f)
        il = -10 * np.log10(rows["il"])
        # TMM : modele complet (grille dense) et equivalent FEM, sur les memes frequences que la FEM
        f_all = np.concatenate([band_freqs(fc) for fc in BANDS[:nb]])
        eq = tmm.solve(tmm_equivalent(design, gap, geo), f_all)
        per = lambda v: v.reshape(nb, PER_BAND).mean(1)
        il_tmm_eq = -10 * np.log10(per(eq["leak"]))
        nominal = copy.deepcopy(design)
        nominal["seal"]["gap_mm"] = gap
        il_tmm = tmm.evaluate(nominal)["il_bands"][:nb]
        out["cases"][f"gap_{gap}mm"] = {
            "il_fem": il.round(2).tolist(),
            "il_fem_debit_event": (-10 * np.log10(rows["il_u"])).round(2).tolist() if mics else None,
            "il_tmm_equivalent": il_tmm_eq.round(2).tolist(),
            "il_tmm_event_equivalent": (-10 * np.log10(per(eq["parts"]["event"]))).round(2).tolist(),
            "il_tmm_nominal": il_tmm.round(2).tolist(),
            "zcav_fem_db": (10 * np.log10(rows["pcav"])).round(2).tolist(),
            "zcav_tmm_db": (10 * np.log10(per(np.abs(eq["z_in"]) ** 2))).round(2).tolist(),
            "speech_dba_fem": round(speech_dba(il), 2),
            "speech_dba_tmm_equivalent": round(speech_dba(il_tmm_eq), 2),
            "speech_dba_tmm_nominal": round(speech_dba(il_tmm), 2),
            "geometry_mm": {k: round(v * 1e3, 2) for k, v in geo.items() if v is not None},
            "time_cfs_s": round(t_cfs, 1), "n_freq": n_f, "time_per_freq_s": round(t_cfs / (2 * n_f), 3),
        }
    out["time_total_s"] = round(time.time() - t0, 1)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--design")
    ap.add_argument("--selfcheck", action="store_true")
    ap.add_argument("--gaps", default="0,0.2", help="jeux du joint en mm (perimetre complet)")
    ap.add_argument("--fmax", type=float, default=8000, help="bande de tiers d'octave maximale")
    ap.add_argument("--params", default=HERE.parent / "params.json")
    a = ap.parse_args()
    if a.selfcheck:
        selfcheck(HERE / "work")
        return
    design = next(d for d in json.loads(Path(a.params).read_text())["designs"] if d["name"] == a.design)
    work = HERE / "work" / a.design
    res = run_design(design, [float(g) for g in a.gaps.split(",")], a.fmax, work)
    (work / "result.json").write_text(json.dumps(res, indent=1))
    for case, c in res["cases"].items():
        print(f"\n## {a.design} {case} : FEM {c['speech_dba_fem']:.1f} dB(A), TMM equivalent "
              f"{c['speech_dba_tmm_equivalent']:.1f}, TMM nominal {c['speech_dba_tmm_nominal']:.1f} "
              f"(cfs {c['time_cfs_s']} s, {c['time_per_freq_s']} s/frequence)")
        print("| Hz | " + " | ".join(f"{b:.0f}" for b in res["bands"]) + " |")
        print("|---|" + "---|" * len(res["bands"]))
        for k in ("il_fem", "il_tmm_equivalent", "il_fem_debit_event", "il_tmm_event_equivalent", "il_tmm_nominal",
                  "zcav_fem_db", "zcav_tmm_db"):
            if c[k] is not None:
                print(f"| {k} | " + " | ".join(f"{x:.1f}" for x in c[k]) + " |")
    print(f"\ntotal {res['time_total_s']} s -> {work / 'result.json'}")


if __name__ == "__main__":
    main()
