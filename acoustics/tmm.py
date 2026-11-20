# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright 2026 Clement Barberousse
"""Modele acoustique 1D (elements localises + matrices de transfert) de Silent Mic.

La bouche est une source de debit Q dans la cavite avant. Le son sort par des
chemins rayonnants : l'event (chaine de conduits, chambres, ecrans), la fuite du
joint visage (fente), la paroi souple du coussin et la coque. La perte par
insertion compare le debit rayonne au debit de la bouche nue.

Usage :
    python acoustics/tmm.py --selfcheck
    python acoustics/tmm.py                 # tous les designs de params.json
    python acoustics/tmm.py --sweep v3-A    # balayage autour d'un design

Hypotheses (a recaler sur le banc) : source a debit constant, cavite uniforme
(valable sous le premier mode, environ 2,5 kHz), sommes de puissances entre
chemins, pas de rayonnement des tissus ni du nez.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path

import numpy as np
from scipy.special import jve

HERE = Path(__file__).resolve().parent
RHO, C0, MU, GAMMA, P0, PR = 1.204, 343.2, 1.81e-5, 1.4, 101325.0, 0.71
DJI_MAX_SPL = 120.0  # DJI Mic Mini 2, 1 % THD (fiche constructeur)

# Bandes de tiers d'octave et niveau de voix normale a 1 m (dB SPL par bande).
# 160 Hz a 8 kHz : niveaux spectraux ANSI S3.5-1997 (effort normal) + 10 log(largeur).
# 100 et 125 Hz : estimation (fondamentale de voix masculine), a mesurer.
BANDS = np.array([100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250,
                  1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000], float)
_SPECTRUM = [None, None, 32.41, 34.48, 34.75, 33.98, 34.59, 34.27, 32.06, 28.30,
             25.01, 23.00, 20.15, 17.32, 13.18, 11.55, 9.33, 5.31, 2.59, 1.13]
SPEECH_1M = np.array([45.0, 49.0] + [s + 10 * math.log10(0.2316 * f)
                                      for s, f in zip(_SPECTRUM[2:], BANDS[2:])])
A_WEIGHT = np.array([-19.1, -16.1, -13.4, -10.9, -8.6, -6.6, -4.8, -3.2, -1.9, -0.8,
                     0.0, 0.6, 1.0, 1.2, 1.3, 1.2, 1.0, 0.5, -0.1, -1.1])


# ---------- briques physiques ----------

def zk_fluid(w, r):
    """Zwikker-Kosten : densite et module effectifs d'un tube de rayon r (pertes visco-thermiques)."""
    kv = r * np.sqrt(-1j * w * RHO / MU)
    kt = kv * math.sqrt(PR)
    # jve (mise a l'echelle exponentielle) evite le debordement pour les gros tubes ; le rapport est inchange
    fv = 2 * jve(1, kv) / (kv * jve(0, kv))
    ft = 2 * jve(1, kt) / (kt * jve(0, kt))
    return RHO / (1 - fv), GAMMA * P0 / (1 + (GAMMA - 1) * ft)


def delany_bazley(w, sigma):
    """Mousse ouverte en fluide equivalent (Delany-Bazley), sigma en Pa.s/m2."""
    f = w / (2 * np.pi)
    x = RHO * f / sigma
    zc = RHO * C0 * (1 + 0.0571 * x ** -0.754 - 1j * 0.087 * x ** -0.732)
    k = w / C0 * (1 + 0.0978 * x ** -0.700 - 1j * 0.189 * x ** -0.595)
    return zc * k / w, zc * w / k  # densite, module (convention e^{jwt})


def duct_tm(w, area, length, perimeter, end_correction=0.0):
    r = 2 * area / perimeter  # rayon hydraulique equivalent
    rho_e, k_e = zk_fluid(w, r)
    k = w * np.sqrt(rho_e / k_e)
    zc = np.sqrt(rho_e * k_e) / area
    L = length + end_correction * math.sqrt(area / math.pi)
    c, s = np.cos(k * L), np.sin(k * L)
    return np.array([[c, 1j * zc * s], [1j * s / zc, c]])


def element_tm(w, e):
    kind = e["type"]
    if kind == "duct":
        a = e["width"] * e["height"] * 1e-6
        per = 2 * (e["width"] + e["height"]) * 1e-3
        n = e.get("count", 1)
        tm = duct_tm(w, a * n, e["length"] * 1e-3, per * n, e.get("end_correction", 0.85))
        return tm
    if kind == "hole":
        d, n = e["diameter"] * 1e-3, e.get("count", 1)
        a = n * math.pi * d * d / 4
        return duct_tm(w, a, e["length"] * 1e-3, n * math.pi * d, e.get("end_correction", 1.7))
    if kind == "chamber":
        c = compliance(w, e["volume_cm3"], e.get("foam_cm3", 0.0), e.get("foam_sigma", 1.2e4))
        return np.array([[np.ones_like(w), 0 * w], [1j * w * c, np.ones_like(w)]])
    if kind == "screen":  # ecran resistif : resistance specifique (Rayl) sur une surface
        z = e["rayl"] / (e["area_mm2"] * 1e-6)
        return np.array([[np.ones_like(w), z + 0 * w], [0 * w, np.ones_like(w)]])
    raise ValueError(kind)


def chain(w, elements):
    tm = np.array([[np.ones_like(w), 0 * w], [0 * w, np.ones_like(w)]], complex)
    for e in elements:
        tm = np.einsum("ijf,jkf->ikf", tm, element_tm(w, e))
    return tm


def compliance(w, volume_cm3, foam_cm3=0.0, sigma=1.2e4):
    c = (volume_cm3 - foam_cm3) * 1e-6 / (RHO * C0 ** 2) + 0j * w
    if foam_cm3:
        _, k_foam = delany_bazley(w, sigma)
        c = c + foam_cm3 * 1e-6 / k_foam
    return c


def z_radiation(w, area):
    a = math.sqrt(area / math.pi)
    ka = w / C0 * a
    return RHO * C0 / area * (0.25 * ka ** 2 + 1j * 0.61 * ka)


def z_slit(w, gap_mm, width_mm, depth_mm):
    """Fente du joint visage : jeu h, longueur le long du perimetre, profondeur de contact."""
    h, b, L = gap_mm * 1e-3, width_mm * 1e-3, depth_mm * 1e-3
    return 12 * MU * L / (b * h ** 3) + 1j * w * 6 * RHO * L / (5 * b * h)


# ---------- modele complet ----------

def solve(design, freqs):
    w = 2 * np.pi * freqs
    cav = design["cavity"]
    c_cav = compliance(w, cav["volume_cm3"], cav.get("foam_cm3", 0.0), cav.get("foam_sigma", 1.2e4))
    y_total = 1j * w * c_cav

    # event : p_in = (T11 Zr + T12) U_out ; U_in = (T21 Zr + T22) U_out
    vent = design["vent"]
    tm = chain(w, vent["elements"])
    zr = z_radiation(w, vent["outlet_area_mm2"] * 1e-6)
    a_out = tm[0, 0] * zr + tm[0, 1]
    b_in = tm[1, 0] * zr + tm[1, 1]
    y_total = y_total + b_in / a_out
    paths = {"event": 1 / a_out}  # U_out / p_in

    seal = design["seal"]
    if seal.get("gap_mm", 0) > 0:
        y = 1 / z_slit(w, seal["gap_mm"], seal["leak_width_mm"], seal["contact_depth_mm"])
        y_total, paths["joint"] = y_total + y, y

    # paroi souple du coussin : C = surface exposee / raideur surfacique
    c_cush = seal["soft_wall_area_mm2"] * 1e-6 / seal["soft_wall_stiffness_pa_per_m"]
    y = 1j * w * c_cush
    y_total, paths["coussin"] = y_total + y, y * seal.get("radiating_fraction", 1.0)

    shell = design.get("shell", {})
    if shell:
        y = 1j * w * shell["wall_area_mm2"] * 1e-6 / shell["stiffness_pa_per_m"]
        y_total, paths["coque"] = y_total + y, y

    z_in = 1 / y_total
    contributions = {k: np.abs(v * z_in) ** 2 for k, v in paths.items()}  # |U_k/Q|^2
    leak = sum(contributions.values())  # shortcut: somme de puissances, chemins supposes incoherents
    mic_gain = np.abs(z_in) * 4 * np.pi / (RHO * w)  # p_cavite / p_1m bouche nue
    return {"leak": leak, "parts": contributions, "mic_gain": mic_gain, "z_in": z_in}


def band_average(freqs, values):
    out = []
    for fc in BANDS:
        sel = (freqs >= fc * 2 ** (-1 / 6)) & (freqs < fc * 2 ** (1 / 6))
        out.append(values[sel].mean())
    return np.array(out)


def pressure_drop(design, flow_lps=0.2):
    """Perte de charge en expiration (Pa) : Poiseuille + pertes singulieres + ecrans."""
    q = flow_lps * 1e-3
    dp = 0.0
    for e in design["vent"]["elements"]:
        if e["type"] in ("duct", "hole"):
            if e["type"] == "duct":
                a = e["width"] * e["height"] * 1e-6 * e.get("count", 1)
                dh = 2 * e["width"] * e["height"] / (e["width"] + e["height"]) * 1e-3
            else:
                a = e.get("count", 1) * math.pi * (e["diameter"] * 1e-3) ** 2 / 4
                dh = e["diameter"] * 1e-3
            v = q / a
            dp += 32 * MU * e["length"] * 1e-3 * v / dh ** 2 + e.get("minor_k", 1.5) * 0.5 * RHO * v ** 2
        elif e["type"] == "screen":
            dp += e["rayl"] * q / (e["area_mm2"] * 1e-6)
    return dp


def evaluate(design, n=4000):
    freqs = np.geomspace(89, 8980, n)
    res = solve(design, freqs)
    il = -10 * np.log10(band_average(freqs, res["leak"]))
    parts = {k: -10 * np.log10(band_average(freqs, v)) for k, v in res["parts"].items()}
    gain = 10 * np.log10(band_average(freqs, res["mic_gain"] ** 2))
    open_a = SPEECH_1M + A_WEIGHT
    dba = 10 * np.log10(np.sum(10 ** (open_a / 10))) - 10 * np.log10(np.sum(10 ** ((open_a - il) / 10)))
    mic = SPEECH_1M + gain
    return {
        "il_bands": il,
        "il_parts": parts,
        "speech_dba": dba,
        "worst_band": (BANDS[il.argmin()], il.min()),
        "mic_spl_normal": 10 * np.log10(np.sum(10 ** (mic / 10))),
        "mic_peak_normal": 10 * np.log10(np.sum(10 ** (mic / 10))) + 12,  # facteur de crete parole
        "dp_02": pressure_drop(design, 0.2),
        "dp_03": pressure_drop(design, 0.3),
    }


# ---------- verifications analytiques ----------

def selfcheck():
    f = np.geomspace(20, 2000, 20000)
    w = 2 * np.pi * f
    # 1. Resonateur de Helmholtz : V = 100 cm3, col 10 mm2 x 20 mm, sans pertes notables
    neck = {"type": "duct", "width": 10, "height": 10, "length": 20, "end_correction": 0.0}
    tm = element_tm(w, neck)
    c = compliance(w, 100)
    # col ferme cote exterieur par une impedance de rayonnement nulle -> resonance de |p_cavite|
    y = 1j * w * c + tm[1, 1] / tm[0, 1]
    f_peak = f[np.argmax(np.abs(1 / y))]
    s, L = 1e-4, 0.02
    f_th = C0 / (2 * np.pi) * math.sqrt(s / (100e-6 * L))
    assert abs(f_peak / f_th - 1) < 0.03, (f_peak, f_th)
    # 2. Piston : partie reelle de rayonnement -> rho c k^2 / (4 pi) * ... loi en ka^2 a basse frequence
    z = z_radiation(np.array([2 * np.pi * 100.0]), 1e-4)[0]
    assert abs(z.real / (RHO * C0 / 1e-4 * 0.25 * (2 * np.pi * 100 / C0) ** 2 * 1e-4 / math.pi) - 1) < 1e-9
    # 3. Fente : resistance de Poiseuille plan en 12 mu L / (b h^3)
    zs = z_slit(np.array([1e-3]), 0.2, 30, 8)[0]
    assert abs(zs.real / (12 * MU * 8e-3 / (30e-3 * (0.2e-3) ** 3)) - 1) < 1e-9
    # 4. Tube large sans pertes : ZK tend vers l'air libre ; mousse DB : vitesse < c0 et attenuation > 0
    rho_e, k_e = zk_fluid(np.array([2 * np.pi * 1000.0]), 0.05)
    assert abs(rho_e[0] / RHO - 1) < 0.01 and abs(k_e[0] / (GAMMA * P0) - 1) < 0.01
    rho_f, k_f = delany_bazley(np.array([2 * np.pi * 1000.0]), 1.2e4)
    kf = 2 * np.pi * 1000 * np.sqrt(rho_f / k_f)[0]
    assert kf.real > 2 * np.pi * 1000 / C0 and kf.imag < 0
    print(f"selfcheck OK : Helmholtz {f_peak:.1f} Hz (theorie {f_th:.1f}), rayonnement, fente, fluides")


# ---------- sorties ----------

def report(name, r):
    print(f"\n## {name}")
    print(f"Attenuation voix (dB(A)) : {r['speech_dba']:.1f}   pire bande : {r['worst_band'][0]:.0f} Hz "
          f"({r['worst_band'][1]:+.1f} dB)")
    print(f"Micro : {r['mic_spl_normal']:.0f} dB SPL efficace, {r['mic_peak_normal']:.0f} dB crete "
          f"(limite DJI {DJI_MAX_SPL:.0f})   Perte de charge : {r['dp_02']:.0f} Pa a 0,2 L/s, "
          f"{r['dp_03']:.0f} Pa a 0,3 L/s")
    print("| Hz | " + " | ".join(f"{b:.0f}" for b in BANDS) + " |")
    print("|---|" + "---|" * len(BANDS))
    print("| total | " + " | ".join(f"{v:.0f}" for v in r["il_bands"]) + " |")
    for k, v in r["il_parts"].items():
        print(f"| {k} | " + " | ".join(f"{x:.0f}" for x in v) + " |")


def with_gap(design, gap, width=None):
    d = copy.deepcopy(design)
    d["seal"]["gap_mm"] = gap
    if width:
        d["seal"]["leak_width_mm"] = width
    return d


def sweep(base):
    print(f"\n### Fuite du joint ({base['name']})")
    print("| jeu | largeur | dB(A) |")
    print("|---|---|---|")
    perim = base["seal"]["perimeter_mm"]
    for gap in (0.0, 0.2, 0.5, 1.0):
        for width in (30, perim):
            r = evaluate(with_gap(base, gap, width), 1500)
            print(f"| {gap} mm | {width} mm | {r['speech_dba']:.1f} |")
    print(f"\n### Event ({base['name']}, fuite nominale)")
    print("| volume cm3 | section mm2 | longueur mm | dB(A) | pire bande | Pa a 0,2 L/s | micro crete dB |")
    print("|---|---|---|---|---|---|---|")
    for vol in (90, 130, 170):
        for area in (30, 42, 60):
            for length in (120, 200, 280):
                d = copy.deepcopy(base)
                d["cavity"]["volume_cm3"] = vol
                d["cavity"]["foam_cm3"] = 0.3 * vol
                duct = next(e for e in d["vent"]["elements"] if e["type"] == "duct")
                duct["height"] = 4.5 if area <= 42 else 6.0
                duct["width"] = area / duct["height"]
                duct["length"] = length
                r = evaluate(d, 1500)
                print(f"| {vol} | {area} | {length} | {r['speech_dba']:.1f} | {r['worst_band'][0]:.0f} Hz "
                      f"{r['worst_band'][1]:+.0f} | {r['dp_02']:.0f} | {r['mic_peak_normal']:.0f} |")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", default=HERE / "params.json")
    ap.add_argument("--selfcheck", action="store_true")
    ap.add_argument("--sweep")
    ap.add_argument("--json")
    a = ap.parse_args()
    if a.selfcheck:
        selfcheck()
        return
    designs = json.loads(Path(a.params).read_text())["designs"]
    out = {}
    for d in designs:
        r = evaluate(d)
        report(d["name"], r)
        out[d["name"]] = {"speech_dba": r["speech_dba"], "il_bands": r["il_bands"].round(1).tolist(),
                          "mic_peak_normal": r["mic_peak_normal"], "dp_02": r["dp_02"]}
    if a.sweep:
        sweep(next(d for d in designs if d["name"] == a.sweep))
    if a.json:
        Path(a.json).write_text(json.dumps({"bands": BANDS.tolist(), "designs": out}, indent=2))


if __name__ == "__main__":
    main()
