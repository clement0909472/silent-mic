# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright 2026 Clement Barberousse
"""Compare les cols du capot d'essai : quelle hauteur de col laisse le moins sortir le son ?

    python bench/cap_test.py --make-noise                     # ecrit bench/bruit-rose.wav, a jouer en boucle
    python bench/cap_test.py --inside DJI --outside Yeti --session capot-20261121
    python bench/cap_test.py --report bench/sessions/capot-20261121
    python bench/cap_test.py --selfcheck

Montage : un ecouteur sans fil qui joue le bruit rose et l'emetteur DJI sont dans le capot, coussin
monte ; le capot est plaque sur le visage, bouche fermee. Blue Yeti a 50 cm. Pour chaque col, trois
poses de 12 s en reposant le capot a chaque fois.

Mesure principale : la fuite = niveau dehors - niveau dedans. Elle ne depend pas du volume de
l'ecouteur. Plus elle est basse, mieux le col isole.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import soundfile as sf

from analyze import BANDS, bands, laeq

HERE = Path(__file__).resolve().parent
RATE = 48000


def pink_noise(seconds: float, seed: int = 1) -> np.ndarray:
    n = int(seconds * RATE)
    spec = np.fft.rfft(np.random.default_rng(seed).normal(size=n))
    f = np.fft.rfftfreq(n, 1 / RATE)
    spec[1:] /= np.sqrt(f[1:])
    spec[f < 60] = 0   # un ecouteur ne rend rien en dessous, inutile de le saturer
    x = np.fft.irfft(spec, n)
    return (x / np.abs(x).max() * 10 ** (-6 / 20)).astype("float32")


def record(a):
    from record import find_device, record_pair
    inside, outside = find_device(a.inside), find_device(a.outside)
    folder = HERE / "sessions" / a.session
    folder.mkdir(parents=True, exist_ok=True)
    collars = [int(c) for c in a.collars.split(",")]
    plan = [("fond", None, "Ecouteur en PAUSE, capot en place, silence.")]
    for rep in range(1, a.reps + 1):   # les cols alternent, pour moyenner toute derive
        plan += [(f"col{c}-{rep}", c, f"Col de {c} mm, bruit rose en lecture, capot repose sur le visage.") for c in collars]
    meta = {"rate": RATE, "collars": collars, "takes": []}
    for take, collar, text in plan:
        if (folder / f"{take}.outside.wav").exists():
            continue
        input(f"\n[{take}] {text}\nEntree pour demarrer ({a.seconds:.0f} s)...")
        sig_in, sig_out = record_pair(inside, outside, a.seconds)
        sf.write(folder / f"{take}.inside.wav", sig_in, RATE, subtype="FLOAT")
        sf.write(folder / f"{take}.outside.wav", sig_out, RATE, subtype="FLOAT")
        if np.mean(np.abs(sig_in) > 0.99) > 1e-5:
            print("  ATTENTION : le DJI ecrete, baisser le volume de l'ecouteur et refaire la session")
        meta["takes"].append({"take": take, "collar": collar})
        (folder / "cap-session.json").write_text(json.dumps(meta, indent=2))
    print(f"\nTermine. Rapport : python bench/cap_test.py --report bench/sessions/{a.session}")


def report(folder: Path):
    meta = json.loads((folder / "cap-session.json").read_text())
    rate = meta["rate"]
    load = lambda take, mic: sf.read(folder / f"{take}.{mic}.wav")[0]
    floor = bands(load("fond", "outside"), rate)
    out = {"collars": {}}
    print("| col | fuite dB(A) | ecart-type | " + " | ".join(f"{b:.0f}" for b in BANDS) + " |")
    print("|---|---|---|" + "---|" * len(BANDS))
    for c in meta["collars"]:
        takes = [t["take"] for t in meta["takes"] if t["collar"] == c]
        leak = [laeq(load(t, "outside"), rate) - laeq(load(t, "inside"), rate) for t in takes]
        b_out = np.array([bands(load(t, "outside"), rate) for t in takes])
        b_in = np.array([bands(load(t, "inside"), rate) for t in takes])
        per_band = (b_out - b_in).mean(0)
        ok = b_out.mean(0) - floor >= 6   # sinon la bande est noyee dans le bruit de fond : la fuite reelle est plus basse
        out["collars"][str(c)] = {"leak_dba": float(np.mean(leak)), "sd": float(np.std(leak)), "bands": per_band.round(1).tolist(), "reliable": ok.tolist()}
        print(f"| {c} mm | {np.mean(leak):.1f} | {np.std(leak):.1f} | " + " | ".join(f"{v:.0f}" if k else f"<={v:.0f}" for v, k in zip(per_band, ok)) + " |")
    best = min(out["collars"], key=lambda k: out["collars"][k]["leak_dba"])
    worst = max(out["collars"], key=lambda k: out["collars"][k]["leak_dba"])
    gain = out["collars"][worst]["leak_dba"] - out["collars"][best]["leak_dba"]
    print(f"\nMeilleur col : {best} mm, {gain:.1f} dB(A) de mieux que le col de {worst} mm.")
    (folder / "cap-report.json").write_text(json.dumps(out, indent=2))
    return out


def selfcheck():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        folder, noise = Path(tmp), pink_noise(4)
        hiss = lambda: np.random.default_rng().normal(0, 1e-5, len(noise))
        sf.write(folder / "fond.inside.wav", hiss(), RATE); sf.write(folder / "fond.outside.wav", hiss(), RATE)
        takes = []
        for c, g in ((3, 0.1), (16, 0.01)):   # le col de 16 mm fuit 20 dB de moins
            sf.write(folder / f"col{c}-1.inside.wav", noise + hiss(), RATE); sf.write(folder / f"col{c}-1.outside.wav", g * noise + hiss(), RATE)
            takes.append({"take": f"col{c}-1", "collar": c})
        (folder / "cap-session.json").write_text(json.dumps({"rate": RATE, "collars": [3, 16], "takes": takes}))
        r = report(folder)["collars"]
        assert abs(r["3"]["leak_dba"] - r["16"]["leak_dba"] - 20) < 0.5, r
    print("selfcheck OK : 20 dB d'ecart retrouves entre deux cols simules")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--make-noise", action="store_true")
    ap.add_argument("--report")
    ap.add_argument("--selfcheck", action="store_true")
    ap.add_argument("--inside", default="DJI")
    ap.add_argument("--outside", default="Yeti")
    ap.add_argument("--session", default=time.strftime("capot-%Y%m%d-%H%M"))
    ap.add_argument("--collars", default="3,10,16")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--seconds", type=float, default=12)
    a = ap.parse_args()
    if a.selfcheck:
        selfcheck()
    elif a.make_noise:
        sf.write(HERE / "bruit-rose.wav", pink_noise(60), RATE, subtype="PCM_16")
        print(f"{HERE / 'bruit-rose.wav'} : 60 s de bruit rose, a jouer en boucle dans l'ecouteur")
    elif a.report:
        report(Path(a.report))
    else:
        record(a)


if __name__ == "__main__":
    main()
