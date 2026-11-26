# SPDX-License-Identifier: CERN-OHL-S-2.0
"""Projet Bambu Studio unique du corps du galet : un plateau par impression, dans l'ordre de la vague.

    python3 cad/bambu_projet.py            -> cad/out/v3-galet/print/silent-mic-vNN.3mf (numero suivant)

Demande de Clement (24 nov. 2026) : un seul projet a ouvrir, ou l'on choisit le plateau, tranche et lance, au lieu
d'un fichier par piece. Les reglages des projets d'une piece (cad/bambu_3mf.sh) sont repris tels quels : procede
commun (A1 mini 0.4, 0.20 mm, 4 parois, 20 %, couture alignee, plaque texturee PEI), puis par objet le plein
(100 %, rectiligne) et les supports sur plateau seulement la ou le projet d'une piece les a. Filament 1 : le
prereglage calibre de Clement (copie aplatie, jamais modifie), seul filament du projet : la ligne de commande de
Bambu Studio 2.9 plante (segfault) des qu'une liste d'assemblage melange deux filaments, et l'anneau attend son
filament blanc : il est la plaque 4, en filament 1 (PLA) comme le reste, a imprimer bobine blanche chargee.
La preuve : le projet se retranche en entier et chaque plateau doit redonner la duree et la masse de son projet
d'une piece (print/resume.txt) a 2 % pres.
"""
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "cad" / "out" / "v3-galet"
APP = "/Applications/BambuStudio.app/Contents/MacOS/BambuStudio"
B = OUT / "silent-mic-v3-galet"
SOLID = {"sparse_infill_density": "100%", "sparse_infill_pattern": "zig-zag"}
ON_PLATE = {"enable_support": "1", "support_type": "normal(auto)", "bridge_no_support": "1", "support_on_build_plate_only": "1"}
# (nom du plateau, stl, filament, reglages de l'objet, projet d'une piece de reference)
# toutes les pieces imprimees, dans l'ordre du montage, du visage au dos (Clement, 26 nov. 2026)
PLATES = [
    ("1 Col", f"{B}-assise-col.stl", 1, SOLID, "corps-assise"),
    ("2 Capot avant", f"{B}-front.stl", 1, SOLID | ON_PLATE, "corps-capot-avant"),
    # anneau : meme filament 1 (PLA) que le reste, imprime avec la bobine blanche ; son projet d'une piece est regle
    # pour du PETG, d'ou l'absence de reference
    ("3 Anneau lumineux (bobine blanche)", f"{B}-ring.stl", 1, {}, None),
    ("4 Coque arriere", f"{B}-rear.stl", 1, SOLID | ON_PLATE, "corps-coque-arriere"),
    ("5 Trappe", f"{B}-cover.stl", 1, SOLID, "corps-trappe"),
    # temoin du col (26 nov. 2026) : anneau d'appui du capot et bas du col, decoupes dans les vraies pieces, pour essayer
    # les 4 diamants, les vis et la mousse avant d'imprimer capot et col
    ("6 Temoin du col (diamants)", [str(OUT / "coupons" / f"temoin-diamant-{n}.stl") for n in ("capot", "col")], 1, {}, "temoin-diamant"),
]


def run(args, log):
    with open(log, "w") as f:
        r = subprocess.run(args, stdout=f, stderr=subprocess.STDOUT)
    assert r.returncode == 0, f"Bambu Studio a echoue ({r.returncode}), voir {log}"


def plates_info(path):
    """(duree en s, masse en g) par plateau, lues dans le slice_info du 3MF tranche."""
    info = zipfile.ZipFile(path).read("Metadata/slice_info.config").decode()
    out = {}
    for block in re.findall(r"<plate>(.*?)</plate>", info, re.S):
        idx = int(re.search(r'key="index" value="(\d+)"', block).group(1))
        pred = int(re.search(r'key="prediction" value="(\d+)"', block).group(1))
        weight = float(re.search(r'key="weight" value="([\d.]+)"', block).group(1))
        out[idx] = (pred, weight)
    return out


def main():
    tmp = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp())
    if not (tmp / "machine.json").exists():  # reglages aplatis, generes par le script des projets d'une piece
        subprocess.run(["cad/bambu_3mf.sh"], cwd=ROOT, env={**__import__("os").environ, "BAMBU_TMP": str(tmp), "ONLY": "aucun"},
                       check=True, stdout=subprocess.DEVNULL)
    assemble = {"plates": [{"plate_name": name, "need_arrange": True,
                            "objects": [{"path": path, "count": 1, "filaments": [fil], "print_params": params}
                                        for path in (stl if isinstance(stl, list) else [stl])]}
                           for name, stl, fil, params, _ in PLATES]}
    (tmp / "assemble.json").write_text(json.dumps(assemble, indent=1, ensure_ascii=False))
    # une version numerotee par livraison : le plus grand numero est la derniere, la seule a ouvrir (Clement, 26 nov. 2026)
    done = [int(f.stem.rsplit("-v", 1)[1]) for f in (OUT / "print").glob("silent-mic-v[0-9][0-9].3mf")]
    target = OUT / "print" / f"silent-mic-v{max(done, default=0) + 1:02d}.3mf"
    build = tmp / "projet"
    run([APP, "--load-settings", f"{tmp}/machine.json;{tmp}/process-off.json", "--load-filaments", f"{tmp}/pla.json",
         "--load-assemble-list", str(tmp / "assemble.json"), "--slice", "0", "--outputdir", str(build), "--export-3mf", target.name],
        tmp / "projet.log")
    built = build / target.name
    subprocess.run([sys.executable, str(ROOT / "cad" / "bambu_3mf_declare.py"), str(built), str(tmp / "process-system.json"),
                    str(tmp / "pla-declare.json")], check=True)
    target.write_bytes(built.read_bytes())
    # preuve : le projet livre se rouvre et se retranche en entier, plateau par plateau comme les projets d'une piece
    redo = tmp / "projet-re"
    run([APP, "--slice", "0", "--outputdir", str(redo), "--export-3mf", "re.3mf", str(target)], tmp / "projet-re.log")
    got = plates_info(redo / "re.3mf")
    ref = {}
    for line in (OUT / "print" / "resume.txt").read_text().splitlines():
        m = re.match(r"(\S+) : (\d+)h(\d+), ([\d.]+) g", line)
        if m:
            ref[m.group(1)] = (int(m.group(2)) * 3600 + int(m.group(3)) * 60, float(m.group(4)))
    bad = []
    for i, (name, _, _, _, single) in enumerate(PLATES, start=1):
        t, w = got[i]
        if single is None:
            print(f"plateau {name} : {t // 3600}h{t % 3600 // 60:02d}, {w:.2f} g (pas de projet d'une piece en PLA pour comparer)")
            continue
        rt, rw = ref[single]
        ok = abs(t - rt) <= 0.02 * rt + 60 and abs(w - rw) <= 0.02 * rw + 0.1
        print(f"plateau {name} : {t // 3600}h{t % 3600 // 60:02d}, {w:.2f} g (projet d'une piece {rt // 3600}h{rt % 3600 // 60:02d}, {rw:.2f} g) {'OK' if ok else 'ECART'}")
        if not ok:
            bad.append(name)
    assert not bad, f"plateaux differents des projets d'une piece : {bad}"
    print(f"-> {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
