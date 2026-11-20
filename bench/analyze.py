# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright 2026 Clement Barberousse
"""Analyse une session du banc : attenuation, spectre par tiers d'octave, ecretage, dictee.

    python bench/analyze.py bench/sessions/<session> [--no-stt]
    python bench/analyze.py --selfcheck

Sorties : tableau Markdown dans le terminal et `report.json` dans la session.
L'attenuation est la difference de niveau au micro exterieur entre les prises
« sans » et « avec », par effort de voix. Une bande n'est retenue que si la prise
« avec » depasse le bruit de fond de 6 dB ; sinon elle est notee « >= ».
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal

HERE = Path(__file__).resolve().parent
BANDS = np.array([100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250,
                  1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000], float)
WHISPER = "/opt/homebrew/bin/whisper-cli"
MODEL = Path.home() / ".local/share/global-agent-connector/tools/plaud-local/models/ggml-large-v3-turbo.bin"


def a_weighting(rate):
    """Filtre de ponderation A (IEC 61672) par transformation bilineaire."""
    f1, f2, f3, f4 = 20.598997, 107.65265, 737.86223, 12194.217
    num = [(2 * np.pi * f4) ** 2 * 10 ** (1.9997 / 20), 0, 0, 0, 0]
    den = np.polymul([1, 4 * np.pi * f4, (2 * np.pi * f4) ** 2], [1, 4 * np.pi * f1, (2 * np.pi * f1) ** 2])
    den = np.polymul(np.polymul(den, [1, 2 * np.pi * f3]), [1, 2 * np.pi * f2])
    b, a = signal.bilinear(num, den, rate)
    return signal.tf2sos(b, a)


def level(x):
    return 10 * np.log10(np.mean(x ** 2) + 1e-20)


def laeq(x, rate):
    return level(signal.sosfilt(a_weighting(rate), x))


def bands(x, rate):
    out = []
    for fc in BANDS:
        sos = signal.butter(6, [fc * 2 ** (-1 / 6), fc * 2 ** (1 / 6)], btype="band", fs=rate, output="sos")
        out.append(level(signal.sosfilt(sos, x)))
    return np.array(out)


def transcribe(wav: Path, gain: float | None = None) -> str:
    """gain None : normalise (dictee, seule l'intelligibilite compte). Sinon gain fixe (oreille d'un voisin)."""
    with tempfile.TemporaryDirectory() as tmp:
        x, rate = sf.read(wav)
        x = signal.resample_poly(x, 1, rate // 16000) if rate % 16000 == 0 else x
        x = x * (gain if gain is not None else 0.9 / (np.abs(x).max() or 1.0))
        src = Path(tmp) / "in.wav"
        sf.write(src, np.clip(x, -1, 1), 16000, subtype="PCM_16")
        subprocess.run([WHISPER, "-m", str(MODEL), "-l", "fr", "-nt", "-otxt", "-of", str(Path(tmp) / "out"), str(src)],
                       check=True, capture_output=True)
        return (Path(tmp) / "out.txt").read_text(encoding="utf-8")


def words(text: str) -> list[str]:
    return re.findall(r"[\w']+", text.lower())


def wer(ref: str, hyp: str) -> float:
    r, h = words(ref), words(hyp)
    d = np.arange(len(h) + 1)
    for i, rw in enumerate(r, 1):
        prev, d[0] = d.copy(), i
        for j, hw in enumerate(h, 1):
            d[j] = min(prev[j] + 1, d[j - 1] + 1, prev[j - 1] + (rw != hw))
    return d[len(h)] / max(len(r), 1)


def reference_text() -> str:
    text = (HERE / "texte.md").read_text(encoding="utf-8")
    return text.split("---", 1)[1] if "---" in text else text


def analyze(folder: Path, stt: bool):
    meta = json.loads((folder / "session.json").read_text())
    rate = meta["rate"]
    load = lambda take, mic: sf.read(folder / f"{take}.{mic}.wav")[0]
    floor_b = bands(load("fond", "outside"), rate)
    floor_a = laeq(load("fond", "outside"), rate)
    report = {"device": meta["device"], "floor_dba_fs": floor_a, "efforts": {}}
    ref = reference_text() if stt else ""
    for effort in ("normal", "doux", "tres-doux"):
        takes = [t["take"] for t in meta["takes"] if t["effort"] == effort]
        if not takes:
            continue
        rows = {cond: [t for t in takes if t.endswith(cond)] for cond in ("sans", "avec")}
        out = {cond: np.array([bands(load(t, "outside"), rate) for t in rows[cond]]) for cond in rows}
        la = {cond: [laeq(load(t, "outside"), rate) for t in rows[cond]] for cond in rows}
        il = 10 * np.log10(np.mean(10 ** (out["sans"] / 10), 0)) - 10 * np.log10(np.mean(10 ** (out["avec"] / 10), 0))
        above = 10 * np.log10(np.mean(10 ** (out["avec"] / 10), 0)) - floor_b
        peaks = [20 * np.log10(np.abs(load(t, "inside")).max() + 1e-12) for t in rows["avec"]]
        clipped = [t for t in rows["avec"] if np.mean(np.abs(load(t, "inside")) > 0.99) > 1e-5]
        res = {
            "attenuation_dba": float(np.mean(la["sans"]) - np.mean(la["avec"])),
            "attenuation_sd": float(np.std(np.array(la["sans"]) - np.array(la["avec"]))),
            "bands_il": il.round(1).tolist(), "bands_reliable": (above >= 6).tolist(),
            "dji_peak_dbfs": float(max(peaks)), "dji_clipped_takes": clipped,
        }
        nez = [t for t in takes if t.endswith("nez")]
        if nez:   # ecart avec les prises "avec" = part du son qui sortait par le nez
            res["attenuation_nez_pince_dba"] = float(np.mean(la["sans"]) - np.mean([laeq(load(t, "outside"), rate) for t in nez]))
        if stt:
            res["wer_inside_avec"] = float(np.mean([wer(ref, transcribe(folder / f"{t}.inside.wav")) for t in rows["avec"]]))
            res["wer_inside_sans"] = float(np.mean([wer(ref, transcribe(folder / f"{t}.inside.wav")) for t in rows["sans"]]))
            # meme gain que les prises sans appareil : on mesure ce qu'un voisin comprend, pas un signal renormalise
            g = 0.9 / max(np.abs(load(t, "outside")).max() for t in rows["sans"])
            res["wer_outside_sans"] = float(np.mean([wer(ref, transcribe(folder / f"{t}.outside.wav", g)) for t in rows["sans"]]))
            res["wer_outside_avec"] = float(np.mean([wer(ref, transcribe(folder / f"{t}.outside.wav", g)) for t in rows["avec"]]))
        report["efforts"][effort] = res
        print(f"\n## Voix {effort} ({meta['device']}, {len(rows['avec'])} paires)")
        print(f"Attenuation au micro exterieur : {res['attenuation_dba']:.1f} dB(A) (ecart-type {res['attenuation_sd']:.1f})")
        if nez:
            print(f"Nez pince : {res['attenuation_nez_pince_dba']:.1f} dB(A), soit {res['attenuation_nez_pince_dba'] - res['attenuation_dba']:+.1f} dB par rapport au nez libre")
        print(f"Crete DJI : {res['dji_peak_dbfs']:.1f} dBFS, prises ecretees : {clipped or 'aucune'}")
        if stt:
            print(f"Erreurs de transcription : dedans avec {res['wer_inside_avec']:.0%}, dedans sans {res['wer_inside_sans']:.0%}, "
                  f"dehors sans {res['wer_outside_sans']:.0%}, dehors avec {res['wer_outside_avec']:.0%} (plus c'est haut dehors, mieux c'est)")
        print("| Hz | " + " | ".join(f"{b:.0f}" for b in BANDS) + " |")
        print("|---|" + "---|" * len(BANDS))
        print("| dB | " + " | ".join(f"{v:.0f}" if ok else f">={v:.0f}" for v, ok in zip(il, above >= 6)) + " |")
    (folder / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))


def selfcheck():
    rate = 48000
    t = np.arange(rate * 2) / rate
    tone = lambda f: np.sin(2 * np.pi * f * t)
    assert abs(laeq(tone(1000), rate) - level(tone(1000))) < 0.2           # A(1 kHz) = 0 dB
    assert abs(laeq(tone(100), rate) - level(tone(100)) + 19.1) < 0.5      # A(100 Hz) = -19,1 dB
    b = bands(tone(1000), rate)
    assert b.argmax() == list(BANDS).index(1000) and b.max() - np.sort(b)[-2] > 10
    assert wer("le chat dort", "le chat dort") == 0 and abs(wer("le chat dort", "le chien dort") - 1 / 3) < 1e-9
    print("selfcheck OK : ponderation A, tiers d'octave, taux d'erreur")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", nargs="?")
    ap.add_argument("--no-stt", action="store_true")
    ap.add_argument("--selfcheck", action="store_true")
    a = ap.parse_args()
    if a.selfcheck:
        selfcheck()
    else:
        analyze(Path(a.folder), stt=not a.no_stt)


if __name__ == "__main__":
    main()
