#!/bin/bash
# SPDX-License-Identifier: CERN-OHL-S-2.0
# Tranche un STL avec OrcaSlicer (A1 mini 0.4, 0.20 mm Standard), supports automatiques ACTIVES
# pour voir s'il en faut, et resume temps, filament et lignes de support.
#   cad/orca_slice.sh fichier.stl [PLA|PETG] [dossier de sortie]
set -euo pipefail
stl=$1; mat=${2:-PLA}; out=${3:-$(mktemp -d)}
app=/Applications/OrcaSlicer.app/Contents
p=$app/Resources/profiles/BBL
case $mat in
  PLA) fil="$p/filament/Bambu PLA Matte @BBL A1M.json"; dens=1.24 ;;
  PETG) fil="$p/filament/Bambu PETG Translucent @BBL A1M.json"; dens=1.25 ;;
esac
mkdir -p "$out"
# copie du profil systeme : supports automatiques actives, ponts courts non supportes, (un profil "User" herite n'est pas resolu en CLI)
/usr/bin/python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); d.update(enable_support="1", support_type="normal(auto)", support_threshold_angle="30", bridge_no_support="1"); json.dump(d, open(sys.argv[2], "w"))' \
  "$p/process/0.20mm Standard @BBL A1M.json" "$out/support-on.json"
"$app/MacOS/OrcaSlicer" --load-settings "$p/machine/Bambu Lab A1 mini 0.4 nozzle.json;$out/support-on.json" \
  --load-filaments "$fil" --arrange 1 --slice 0 --outputdir "$out" "$stl" > "$out/orca.log" 2>&1 || true
g=$out/plate_1.gcode
[ -f "$g" ] || { echo "ECHEC tranchage: $(tail -3 "$out/orca.log")"; exit 1; }
mm=$(grep -m1 "filament used \[mm\]" "$g" | awk -F= '{print $2}')
sup=$(grep -c "^; FEATURE: Support" "$g" || true)
echo "$(basename "$stl"): $(grep -m1 "total estimated time" "$g" | sed 's/.*total estimated time: //'), $(awk -v m="$mm" -v d=$dens 'BEGIN{printf "%.1f g", m*3.14159*0.875*0.875*d/1000}'), support=$(grep -m1 '^; enable_support' "$g" | awk '{print $4}') couches avec support=$sup"
