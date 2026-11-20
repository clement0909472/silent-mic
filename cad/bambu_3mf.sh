#!/bin/bash
# SPDX-License-Identifier: CERN-OHL-S-2.0
# Projets 3MF Bambu Studio (A1 mini 0.4, 0.20 mm, 4 perimetres, 20 % de remplissage,
# couture alignee) des pieces d'essai et du corps du galet v3, tranches et retranchables.
# Le prereglage filament calibre de Clement est lu, jamais modifie : une copie aplatie
# (parent + debit calibre) est ecrite dans un dossier temporaire.
#   cad/bambu_3mf.sh [essai|corps]   -> cad/out/v3-galet/print/*.3mf et print/resume.txt
set -euo pipefail
cd "$(dirname "$0")/.."
app=/Applications/BambuStudio.app/Contents
p=$app/Resources/profiles/BBL
u="$HOME/Library/Application Support/BambuStudio/user/2260888086/filament"
c=cad/out/v3-galet/coupons
out=cad/out/v3-galet/print
tmp=${BAMBU_TMP:-$(mktemp -d)}  # BAMBU_TMP garde les G-code de controle
mkdir -p "$out"

/usr/bin/python3 - "$u" "$p" "$tmp" <<'EOF'
import json, sys
u, p, tmp = sys.argv[1:]
base = json.load(open(f"{u}/base/ELEGOO PLA Mat @Bambu Lab A1 mini 0.4 nozzle.json"))
user = json.load(open(f"{u}/ELEGOO PLA Mat Flow Rate Calibrated.json"))
flat = base | {k: v for k, v in user.items() if k != "inherits"}
flat.pop("inherits", None)
flat["type"] = "filament"
json.dump(flat, open(f"{tmp}/pla.json", "w"), indent=1)
# PETG translucide systeme : la CLI ne resout pas "inherits" pour un fichier charge par chemin
import glob
by_name = {}
for f in glob.glob(f"{p}/filament/*.json"):
    try:
        d = json.load(open(f))
        by_name[d.get("name")] = d
    except Exception:
        pass
def resolve(name):
    d = by_name[name]
    return (resolve(d["inherits"]) if d.get("inherits") else {}) | d
petg = resolve("Bambu PETG Translucent @BBL A1M")
petg.pop("inherits", None)
petg["type"] = "filament"
json.dump(petg, open(f"{tmp}/petg.json", "w"), indent=1)
proc = json.load(open(f"{p}/process/0.20mm Standard @BBL A1M.json"))
proc.update(wall_loops="4", sparse_infill_density="20%", seam_position="aligned", curr_bed_type="Textured PEI Plate")
for name, sup in (("process-off", "0"), ("process-auto", "1"), ("process-plate", "1")):
    q = dict(proc, enable_support=sup)
    if sup == "1":
        q.update(support_type="normal(auto)", bridge_no_support="1")
    if name == "process-plate":  # coque arriere : rien dans la cavite, sous les butees du nid
        q["support_on_build_plate_only"] = "1"
    json.dump(q, open(f"{tmp}/{name}.json", "w"), indent=1)
EOF

project() {  # nom filament stl...
  local name=$1 fil=$2
  shift 2
  local machine="$p/machine/Bambu Lab A1 mini 0.4 nozzle.json"
  # 1) controle : supports automatiques actifs, ponts courts non supportes
  "$app/MacOS/BambuStudio" --load-settings "$machine;$tmp/process-auto.json" --load-filaments "$fil" \
    --arrange 1 --orient 0 --slice 0 --outputdir "$tmp/$name-auto" --export-3mf "$name.3mf" "$@" > "$tmp/$name-auto.log" 2>&1
  local n_sup need=false
  n_sup=$(grep -c "^; FEATURE: Support" "$tmp/$name-auto/plate_1.gcode" || true)
  [ "$n_sup" -gt 0 ] && need=true
  # 2) projet livre : supports seulement si le controle en demande
  local proc="$tmp/process-off.json"
  [ "$need" = "true" ] && proc="$tmp/process-${SUP:-auto}.json"
  "$app/MacOS/BambuStudio" --load-settings "$machine;$proc" --load-filaments "$fil" \
    --arrange 1 --orient 0 --slice 0 --outputdir "$tmp/$name" --export-3mf "$name.3mf" "$@" > "$tmp/$name.log" 2>&1
  cp "$tmp/$name/$name.3mf" "$out/$name.3mf"
  # 3) preuve : le 3MF livre se rouvre et se retranche a l'identique
  "$app/MacOS/BambuStudio" --slice 0 --outputdir "$tmp/$name-re" "$out/$name.3mf" > "$tmp/$name-re.log" 2>&1
  local info pred weight re_t
  info=$(unzip -p "$out/$name.3mf" Metadata/slice_info.config)
  pred=$(echo "$info" | grep -o 'prediction" value="[0-9]*' | head -1 | sed 's/.*"//')
  weight=$(echo "$info" | grep -o 'weight" value="[0-9.]*' | head -1 | sed 's/.*"//')
  re_t=$(grep -m1 "total estimated time" "$tmp/$name-re/plate_1.gcode" | sed 's/.*total estimated time: //')
  grep -v "^$name :" "$out/resume.txt" > "$tmp/resume" || true
  mv "$tmp/resume" "$out/resume.txt"
  printf "%s : %dh%02d, %s g, blocs de support au controle=%s, retranche : %s\n" "$name" $((pred / 3600)) $((pred % 3600 / 60)) "$weight" "$n_sup" "$re_t" | tee -a "$out/resume.txt"
}

only=${1:-tout}
touch "$out/resume.txt"
if [ "$only" != corps ]; then
project capot-essai "$tmp/pla.json" "$c/pad-test-cap.stl"
# ordre de chargement voulu : dans l'ordre inverse, le placement automatique faisait apparaitre
# 11 petits blocs de support qu'aucune piece ne demande seule
project cols-et-joint "$tmp/pla.json" "$c/joint-coupon-rear.stl" "$c/joint-coupon-front.stl" \
  "$c/collar-insert-16mm.stl" "$c/collar-insert-10mm.stl" "$c/collar-insert-3mm.stl"
project lumiere-petg "$tmp/petg.json" "$c/light-coupon-petg.stl"
fi
if [ "$only" != essai ]; then
  b=cad/out/v3-galet/silent-mic-v3-galet
  project corps-capot-avant "$tmp/pla.json" "$b-front.stl"
  SUP=plate project corps-coque-arriere "$tmp/pla.json" "$b-rear.stl"
  project corps-trappe-col "$tmp/pla.json" "$b-cover.stl" "$b-collar-insert-14mm.stl"
  project corps-anneau-petg "$tmp/petg.json" "$b-ring.stl"
fi
