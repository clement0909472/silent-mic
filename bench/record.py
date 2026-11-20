# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright 2026 Clement Barberousse
"""Enregistre en meme temps le micro interieur (DJI) et le micro exterieur (Blue Yeti).

    python bench/record.py --list
    python bench/record.py --inside "DJI" --outside "Yeti" --session v2-2026-11-20

Le script guide le protocole : bruit de fond, puis paires alternees sans / avec
appareil, a voix normale, douce et tres douce, plus deux prises nez pince. Chaque prise donne deux WAV 48 kHz bruts
(`<prise>.inside.wav`, `<prise>.outside.wav`) dans `bench/sessions/<session>/`.
Aucun traitement : regler les gains a la main avant, puis ne plus y toucher.
"""

from __future__ import annotations

import argparse
import json
import threading
import time
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf

HERE = Path(__file__).resolve().parent
RATE = 48000
TEXT = (HERE / "texte.md").read_text(encoding="utf-8")


def find_device(name: str) -> int:
    for i, d in enumerate(sd.query_devices()):
        if name.lower() in d["name"].lower() and d["max_input_channels"] > 0:
            return i
    raise SystemExit(f"Aucune entree audio ne contient « {name} ». Lancer --list.")


def record_pair(inside: int, outside: int, seconds: float):
    """Deux flux independants lances ensemble ; derive d'horloge negligeable sur 60 s."""
    out: dict[str, np.ndarray] = {}

    def grab(key, dev):
        out[key] = sd.rec(int(seconds * RATE), samplerate=RATE, channels=1, device=dev, dtype="float32", blocking=True)[:, 0]

    threads = [threading.Thread(target=grab, args=a) for a in (("inside", inside), ("outside", outside))]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return out["inside"], out["outside"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--inside", default="DJI")
    ap.add_argument("--outside", default="Yeti")
    ap.add_argument("--session", default=time.strftime("session-%Y%m%d-%H%M"))
    ap.add_argument("--device-name", default="v2", help="appareil teste : v2, v3-A...")
    ap.add_argument("--pairs", type=int, default=3)
    ap.add_argument("--seconds", type=float, default=40)
    a = ap.parse_args()
    if a.list:
        print(sd.query_devices())
        return
    inside, outside = find_device(a.inside), find_device(a.outside)
    folder = HERE / "sessions" / a.session
    folder.mkdir(parents=True, exist_ok=True)
    plan = [("fond", "silence", "aucun")]
    for effort in ("normal", "doux", "tres-doux"):
        for n in range(1, a.pairs + 1):
            plan += [(f"{effort}-{n}-sans", effort, "sans"), (f"{effort}-{n}-avec", effort, "avec")]
        if effort == "normal":   # nez pince : mesure ce que le nez laisse sortir quand la bouche est couverte
            plan += [(f"normal-{n}-nez", "normal", "nez") for n in (1, 2)]
    meta = {"rate": RATE, "inside": sd.query_devices(inside)["name"], "outside": sd.query_devices(outside)["name"],
            "device": a.device_name, "seconds": a.seconds, "takes": []}
    print(TEXT)
    for take, effort, cond in plan:
        if (folder / f"{take}.outside.wav").exists():
            continue  # reprise d'une session interrompue
        what = {"silence": "Silence complet, ne bougez pas.",
                "normal": "Lisez le texte a voix normale.", "doux": "Lisez le texte a voix douce.",
                "tres-doux": "Lisez le texte a voix tres douce, presque murmuree mais encore voisee."}[effort]
        hold = {"sans": "Bouche nue, micro DJI tenu a la meme place que dans l'appareil.",
                "avec": f"Appareil {a.device_name} plaque sur la bouche.", "aucun": "",
                "nez": f"Appareil {a.device_name} plaque sur la bouche ET nez pince entre deux doigts."}[cond]
        input(f"\n[{take}] {what} {hold}\nEntree pour demarrer ({a.seconds:.0f} s)...")
        sig_in, sig_out = record_pair(inside, outside, a.seconds if effort != "silence" else 15)
        sf.write(folder / f"{take}.inside.wav", sig_in, RATE, subtype="FLOAT")
        sf.write(folder / f"{take}.outside.wav", sig_out, RATE, subtype="FLOAT")
        clip = float(np.mean(np.abs(sig_in) > 0.99))
        print(f"  ok, crete DJI {20*np.log10(np.abs(sig_in).max()+1e-12):.1f} dBFS"
              + (f"  ATTENTION ecretage sur {clip:.2%} des echantillons" if clip else ""))
        meta["takes"].append({"take": take, "effort": effort, "condition": cond})
        (folder / "session.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"\nTermine. Analyse : python bench/analyze.py bench/sessions/{a.session}")


if __name__ == "__main__":
    main()
