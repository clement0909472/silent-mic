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
# ce que l'interface inscrit pour ce filament dans ses propres projets : son parent et les cles qu'il change
meta = ("name", "inherits", "from", "filament_settings_id", "setting_id", "version", "filament_id", "base_id")
json.dump({"inherits": user.get("inherits", ""), "diff": sorted(k for k, v in user.items() if k in base and base[k] != v and k not in meta)},
          open(f"{tmp}/pla-declare.json", "w"))
# La CLI ne resout pas "inherits" pour un fichier charge par chemin : un prereglage systeme passe tel quel
# n'apporte que ses quelques cles propres, et tout le reste prend les valeurs par defaut du trancheur.
# Jusqu'au 23 nov. 2026 la machine et le procede etaient passes ainsi : G-code de demarrage generique
# (G28 seul, sans la sequence de l'A1 mini), accelerations de 500 a 1000 mm/s2, parois a 60 mm/s.
# Chaque prereglage systeme est donc aplati ici avec toute sa chaine d'heritage.
import glob
def system(kind):
    out = {}
    for f in glob.glob(f"{p}/{kind}/**/*.json", recursive=True):
        try:
            d = json.load(open(f))
            out[d.get("name")] = d
        except Exception:
            pass
    def resolve(name):
        d = out[name]
        full = resolve(d["inherits"]) if d.get("inherits") else {}
        # les sequences de G-code de l'A1 mini (demarrage, fin, changement de couche) sont dans des modeles inclus
        for inc in d.get("include", []):
            full |= {k: v for k, v in resolve(inc).items() if k not in ("name", "instantiation")}
        return full | d
    return resolve
def flat(kind, name):
    d = system(kind)(name)
    d.pop("inherits", None)
    d.pop("include", None)
    return d
petg = flat("filament", "Bambu PETG Translucent @BBL A1M")
petg["type"] = "filament"
json.dump(petg, open(f"{tmp}/petg.json", "w"), indent=1)
# blanc legerement translucide fourni avec l'imprimante (bobine de 20 g de Clement) : anneau et eprouvette du premier proto
plab = flat("filament", "Bambu PLA Basic @BBL A1M")
plab["type"] = "filament"
json.dump(plab, open(f"{tmp}/pla-basic.json", "w"), indent=1)
machine = flat("machine", "Bambu Lab A1 mini 0.4 nozzle")
# la sequence de demarrage de l'A1 mini fait plus de 10 000 caracteres ; la generique tient en deux lignes
assert "M1002" in machine["machine_start_gcode"] and len(machine["machine_start_gcode"]) > 5000 and len(machine) > 100, "prereglage machine A1 mini incomplet"
json.dump(machine, open(f"{tmp}/machine.json", "w"), indent=1)
proc = flat("process", "0.20mm Standard @BBL A1M")
assert len(proc) > 150, "prereglage de procede incomplet"
json.dump(proc, open(f"{tmp}/process-system.json", "w"), indent=1)  # reference pour les ecarts declares dans le 3MF
# reduce_crossing_wall : la buse contourne les vides au lieu de les traverser (fils dans la cavite du capot v05, 26 nov. 2026)
proc.update(wall_loops="4", sparse_infill_density="20%", seam_position="aligned", curr_bed_type="Textured PEI Plate",
            reduce_crossing_wall="1")
for name, sup in (("process-off", "0"), ("process-auto", "1"), ("process-plate", "1")):
    q = dict(proc, enable_support=sup)
    if sup == "1":
        q.update(support_type="normal(auto)", bridge_no_support="1")
    if name == "process-plate":  # supports poses sur le plateau seulement : rien dans une cavite fermee ni dans un logement d'ecrou
        q["support_on_build_plate_only"] = "1"
    json.dump(q, open(f"{tmp}/{name}.json", "w"), indent=1)
    # pieces qui ferment la chambre du corps : pleines, sans vide entre les parois (question de Clement, 23 nov. 2026)
    # (Bambu Studio refuse le motif en grille a 100 % : rectiligne)
    json.dump(dict(q, sparse_infill_density="100%", sparse_infill_pattern="zig-zag"), open(f"{tmp}/{name}-solid.json", "w"), indent=1)
EOF

project() {  # nom filament stl...   (ONLY=nom : ce seul plateau, les autres 3MF restent tels quels)
  [ -n "${ONLY:-}" ] && [ "$ONLY" != "$1" ] && return 0
  local name=$1 fil=$2
  shift 2
  local machine="$tmp/machine.json"
  # 1) controle : supports automatiques actifs, ponts courts non supportes
  "$app/MacOS/BambuStudio" --load-settings "$machine;$tmp/process-auto.json" --load-filaments "$fil" \
    --arrange 1 --orient 0 --slice 0 --outputdir "$tmp/$name-auto" --export-3mf "$name.3mf" "$@" > "$tmp/$name-auto.log" 2>&1
  local n_sup need=false
  n_sup=$(grep -c "^; FEATURE: Support" "$tmp/$name-auto/plate_1.gcode" || true)
  [ "$n_sup" -gt 0 ] && need=true
  # 2) projet livre : supports seulement si le controle en demande
  local proc="$tmp/process-off.json"
  [ "$need" = "true" ] && proc="$tmp/process-${SUP:-auto}.json"
  [ "${SOLID:-0}" = 1 ] && proc="${proc%.json}-solid.json"
  "$app/MacOS/BambuStudio" --load-settings "$machine;$proc" --load-filaments "$fil" \
    --arrange 1 --orient 0 --slice 0 --outputdir "$tmp/$name" --export-3mf "$name.3mf" "$@" > "$tmp/$name.log" 2>&1
  cp "$tmp/$name/$name.3mf" "$out/$name.3mf"
  # Bambu Studio, a l'ouverture, recharge le procede systeme par son nom et n'y applique que les cles
  # declarees dans different_settings_to_system : sans elles, l'interface perdait les 4 parois, les 20 %
  # de remplissage et les supports. On y inscrit donc les cles du projet qui different du procede systeme.
  /usr/bin/python3 cad/bambu_3mf_declare.py "$out/$name.3mf" "$tmp/process-system.json" "${fil%.json}-declare.json"
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
project capot-essai "$tmp/pla.json" "$c/pad-test-cap.stl" "$c/temoin-bonnette.stl"
# ordre de chargement voulu : dans l'ordre inverse, le placement automatique faisait apparaitre
# 11 petits blocs de support qu'aucune piece ne demande seule
# supports sur plateau seulement, comme au corps : un plot sous chaque tete de vis de l'eprouvette avant,
# rien dans les logements d'ecrou de l'eprouvette arriere (leur plafond s'imprime en pont, comme dans la coque)
# l'assise de 10 mm sert d'abord sur le capot d'essai (le corps a la sienne depuis le 24 nov. 2026 : corps-assise)
SOLID=1 SUP=plate project cols-et-joint "$tmp/pla.json" "$c/joint-coupon-rear.stl" "$c/joint-coupon-front.stl" "$c/assise-col-10mm.stl"
# essai du 24 nov. 2026 : col de 20 mm, assise plus courbee (rayons 85 et 70 au lieu de 105). Essai de forme a
# 20 % (2 h 15 au lieu de 3 h 27 pleines) : l'assise retenue sera reimprimee pleine avec le corps
project assises-20mm "$tmp/pla.json" "$c/assise-col-20mm-r85.stl" "$c/assise-col-20mm-r70.stl"
# essai suivant : bords encore 12 mm plus haut, par deux cales posees sur l'assise R85 deja imprimee (une par cote)
project cales-assise "$tmp/pla.json" "$c/cale-assise-r85-12mm.stl" "$c/cale-assise-r85-12mm.stl"
# puis encore 12 mm : seconde paire posee sur la premiere
project cales-assise-2 "$tmp/pla.json" "$c/cale-assise-r60-12mm.stl" "$c/cale-assise-r60-12mm.stl"
project lumiere-petg "$tmp/petg.json" "$c/light-coupon-petg.stl"
# parois debout de 0.8 a 2.4 mm, la lumiere les traverse comme l'anneau : choix de son epaisseur (25 nov. 2026)
project lumiere-pla-basic "$tmp/pla-basic.json" "$c/light-walls.stl"
# temoin du col visse sur diamants (26 nov. 2026) : anneaux decoupes dans le vrai capot et le vrai col
project temoin-diamant "$tmp/pla.json" "$c/temoin-diamant-capot.stl" "$c/temoin-diamant-col.stl"
# gabarit de decoupe du joint capot/coque (26 nov. 2026) : anneau d'une piece suivi au cutter (cad/gabarit_joint.py)
project gabarit-joint "$tmp/pla.json" "$c/gabarit-joint.stl"
fi
if [ "$only" != essai ]; then
  b=cad/out/v3-galet/silent-mic-v3-galet
  # capot : dessine sans support depuis le 26 nov. 2026 (imprime joint au plateau). Supports coupes depuis la v12 :
  # avec la rainure de 3.1 mm (v10), Bambu Studio n'y reconnaissait plus un pont et la remplissait de supports
  SOLID=1 SUP=off project corps-capot-avant "$tmp/pla.json" "$b-front.stl"
  SOLID=1 SUP=plate project corps-coque-arriere "$tmp/pla.json" "$b-rear.stl"
  # assise du corps : celle des essais du 24 nov. 2026 (R85 et ses deux paires de cales) d'une piece, pleine
  SOLID=1 project corps-assise "$tmp/pla.json" "$b-assise-col.stl"
  # trappe pleine aussi : poids et sensation de produit fini (Clement, 24 nov. 2026)
  SOLID=1 project corps-trappe "$tmp/pla.json" "$b-cover.stl"
  project corps-anneau-petg "$tmp/petg.json" "$b-ring.stl"
  # premier proto : anneau en PLA Basic blanc (bobine de 20 g de Clement), epaisseur choisie sur lumiere-pla-basic
  project corps-anneau-pla-basic "$tmp/pla-basic.json" "$b-ring.stl"
fi
