# SPDX-License-Identifier: CERN-OHL-S-2.0
"""Inscrit dans un projet 3MF Bambu Studio les cles du procede qui different du prereglage systeme.

    python3 cad/bambu_3mf_declare.py projet.3mf procede-systeme-aplati.json [filament-declare.json]

A l'ouverture, Bambu Studio recharge le procede systeme par son nom et n'y applique que les cles listees
dans different_settings_to_system. Un 3MF ecrit par la ligne de commande laisse cette liste vide : l'interface
ignorait alors les reglages du projet (4 parois, 20 % de remplissage, supports) et retranchait en standard.
"""
import json
import os
import sys
import zipfile

path, ref = sys.argv[1], json.load(open(sys.argv[2]))
src = zipfile.ZipFile(path)
cfg = json.loads(src.read("Metadata/project_settings.config"))
skip = {"name", "from", "setting_id", "type", "instantiation", "description", "print_settings_id", "filename_format"}
diff = sorted(k for k, v in ref.items() if k not in skip and k in cfg and cfg[k] != v)
cfg["different_settings_to_system"] = [";".join(diff)] + list(cfg.get("different_settings_to_system", ["", "", ""]))[1:]
# filament personnalise : meme declaration que dans les projets enregistres par l'interface (parent et cles changees)
if len(sys.argv) > 3 and os.path.exists(sys.argv[3]):
    fil = json.load(open(sys.argv[3]))
    groups = list(cfg.get("inherits_group", ["", "", ""]))
    cfg["different_settings_to_system"][1], groups[1] = ";".join(fil["diff"]), fil["inherits"]
    cfg["inherits_group"] = groups
tmp = path + ".tmp"
with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
    for item in src.infolist():
        data = json.dumps(cfg, indent=4).encode() if item.filename == "Metadata/project_settings.config" else src.read(item.filename)
        dst.writestr(item, data)
src.close()
os.replace(tmp, path)
print("  ecarts declares au procede systeme :", ", ".join(diff))
