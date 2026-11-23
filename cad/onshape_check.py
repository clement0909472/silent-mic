# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright 2026 Clement Barberousse
"""Collisions de l'assemblage vues par Onshape (noyau Parasolid), par son API, sans interface.

Le STEP d'assemblage est importe a plat dans un seul Part Studio, ou toutes les pieces gardent leur
position. Un script FeatureScript (evCollision) y cherche les paires de pieces qui se recouvrent. C'est
un second avis sur les interferences calculees par OCCT dans cad/silent_mic_v3_galet.py.

    python3 cad/onshape_check.py --document <URL du document Onshape>   (une seule fois)
    python3 cad/onshape_check.py [chemin.step]

La cle d'API vient du trousseau macOS (cad/onshape_key.sh save). Le document et les deux onglets du
controle (le fichier et son Part Studio, reutilises a chaque fois) sont notes dans cad/.onshape.local.json,
hors Git. Sortie : cad/out/v3-galet/onshape-check.json.
"""

from pathlib import Path
import base64
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

HERE = Path(__file__).resolve().parent
LOCAL = HERE / ".onshape.local.json"
STEP = HERE / "out" / "v3-galet" / "silent-mic-v3-galet-technical.step"
OUT = HERE / "out" / "v3-galet" / "onshape-check.json"
API = "https://cad.onshape.com/api/v10"
SERVICE = "ai.clement-assistant.onshape-api"
# le volume d'air recouvre par construction les mousses, le joint et le ruban LED qui l'occupent
SKIP = ("air-cavity-and-duct",)
# corps souples, tailles sur les coques puis ecrits en NURBS (volume a 1 % pres) : un recouvrement avec eux
# est une lamelle d'approximation, signalee sans faire echouer le controle
SOFT = ("ref-foam-disc", "ref-foam-liner", "ref-earpad", "ref-gasket", "ref-bonnette", "ref-led-filament")
OVERLAP = ("INTERFERE", "TARGET_IN_TOOL", "TOOL_IN_TARGET")

SCRIPT = r"""
function(context is Context, queries)
{
    const bodies = evaluateQuery(context, qAllModifiableSolidBodies());
    var names = [];
    for (var b in bodies)
    {
        names = append(names, getProperty(context, { "entity" : b, "propertyType" : PropertyType.NAME }));
    }
    var pairs = {};
    for (var i = 0; i < size(bodies); i += 1)
    {
        var others = [];
        for (var j = i + 1; j < size(bodies); j += 1)
        {
            others = append(others, bodies[j]);
        }
        if (size(others) == 0)
        {
            break;
        }
        const found = evCollision(context, { "tools" : bodies[i], "targets" : qUnion(others) });
        for (var c in found)
        {
            const other = getProperty(context, { "entity" : c["targetBody"], "propertyType" : PropertyType.NAME });
            pairs[names[i] ~ "|" ~ other ~ "|" ~ toString(c["type"])] = true;
        }
    }
    return { "names" : names, "pairs" : keys(pairs) };
}
"""


def secret(account):
    return subprocess.run(["security", "find-generic-password", "-s", SERVICE, "-a", account, "-w"],
                          check=True, capture_output=True, text=True).stdout.strip()


def call(method, path, body=None, content_type="application/json"):
    token = base64.b64encode(f"{secret('access-key')}:{secret('secret-key')}".encode()).decode()
    data = json.dumps(body).encode() if isinstance(body, (dict, list)) else body
    req = urllib.request.Request(API + path, data=data, method=method,
                                 headers={"Authorization": "Basic " + token, "Accept": "application/json;charset=UTF-8; qs=0.09",
                                          "Content-Type": content_type})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Onshape {method} {path.split('?')[0]} : HTTP {e.code} {e.read()[:300].decode(errors='replace')}")


def multipart(fields, filename, payload):
    edge = uuid.uuid4().hex
    out = b""
    for k, v in fields.items():
        out += f'--{edge}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    out += (f'--{edge}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            "Content-Type: application/octet-stream\r\n\r\n").encode() + payload + f"\r\n--{edge}--\r\n".encode()
    return out, f"multipart/form-data; boundary={edge}"


def plain(v):
    """Valeur FeatureScript serialisee (BTFSValue...) -> valeur Python."""
    if isinstance(v, dict) and "btType" in v:
        kind, val = v["btType"], v.get("value")
        if kind.endswith("BTFSValueMap"):
            return {plain(e["key"]): plain(e["value"]) for e in val}
        if kind.endswith("BTFSValueArray"):
            return [plain(x) for x in val]
        return val
    return v


def import_step(cfg, step):
    """Envoie le STEP dans le document et le fait traduire a plat (un seul Part Studio, pieces en position).
    La premiere fois, cree un onglet fichier et son Part Studio ; ensuite, met a jour ce meme fichier, et
    Onshape regenere le meme Part Studio sur place : le document ne grossit pas d'un controle a l'autre."""
    body, ctype = multipart({"formatName": "", "flattenAssemblies": "true", "translate": "true", "storeInDocument": "true",
                             "yAxisIsUp": "false", "importAppearances": "false", "notifyUser": "false"},
                            "silent-mic-controle-api.step", step.read_bytes())
    base = f"/blobelements/d/{cfg['did']}/w/{cfg['wid']}"
    r = call("POST", base + (f"/e/{cfg['blob']}" if cfg.get("blob") else ""), body, ctype)
    t, wait = call("GET", f"/translations/{r['translationId']}"), 3.0
    while t.get("requestState") == "ACTIVE":
        time.sleep(wait)
        wait = min(wait * 1.5, 20.0)
        t = call("GET", f"/translations/{t['id']}")
    if t.get("requestState") != "DONE":
        raise SystemExit(f"import Onshape en echec : {t.get('requestState')} {t.get('failureReason')}")
    if not cfg.get("blob"):
        cfg.update(blob=r["id"], studio=t["resultElementIds"][0])
        LOCAL.write_text(json.dumps(cfg, indent=1))


def main():
    args = sys.argv[1:]
    cfg = json.loads(LOCAL.read_text()) if LOCAL.exists() else {}
    if args[:1] == ["--document"]:
        m = re.search(r"/documents/([0-9a-f]{24})/w/([0-9a-f]{24})", args[1])
        assert m, "URL de document Onshape attendue (.../documents/<id>/w/<id>/...)"
        cfg.update(did=m.group(1), wid=m.group(2))
        LOCAL.write_text(json.dumps(cfg, indent=1))
        print("document note dans", LOCAL.name)
        return
    assert cfg.get("did"), "lancer d'abord : cad/onshape_check.py --document <URL du document Onshape>"
    step = Path(args[0]) if args else STEP
    t0 = time.time()
    import_step(cfg, step)
    res = call("POST", f"/partstudios/d/{cfg['did']}/w/{cfg['wid']}/e/{cfg['studio']}/featurescript?rollbackBarIndex=-1", {"script": SCRIPT})
    result = plain(res.get("result"))
    if not isinstance(result, dict):
        raise SystemExit("FeatureScript sans resultat : " + json.dumps({k: res.get(k) for k in ("notices", "console")})[:900])
    names, overlaps, soft, contacts = result["names"], [], [], []
    for row in result["pairs"]:
        a, b, kind = row.split("|")
        if a in SKIP or b in SKIP:
            continue
        if kind not in OVERLAP:
            contacts.append((a, b))
        else:
            (soft if a in SOFT or b in SOFT else overlaps).append([a, b, kind])
    report = {"step": step.name, "pieces": len(names), "noms": sorted(set(names)), "recouvrements": sorted(overlaps),
              "recouvrements_avec_corps_souples_info": sorted(soft), "contacts_sans_recouvrement": len(set(contacts)),
              "exclus": list(SKIP), "controle_le": time.strftime("%Y-%m-%d %H:%M"), "duree_s": round(time.time() - t0, 1)}
    OUT.write_text(json.dumps(report, indent=1, ensure_ascii=False))
    print(json.dumps({k: v for k, v in report.items() if k != "noms"}, indent=1, ensure_ascii=False))
    if overlaps:
        raise SystemExit(f"ECHEC : {len(overlaps)} recouvrement(s) selon Onshape")


if __name__ == "__main__":
    main()
