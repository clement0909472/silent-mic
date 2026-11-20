# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright 2026 Clement Barberousse
"""Regroupe les STL de cad/out/v3-galet/web en un seul JSON pour la visionneuse concepts/galet-cao.html.

    python3 cad/web_bundle.py [sortie.json]      (defaut : concepts/parts.json)

Les pages publiees ne servent pas les .stl : chaque piece devient ses sommets en float32, encodes en base64.
"""

import base64
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "cad" / "out" / "v3-galet" / "web"


def triangles(stl: Path) -> bytes:
    data = stl.read_bytes()
    (count,) = struct.unpack_from("<I", data, 80)
    assert len(data) == 84 + 50 * count, f"{stl.name} : STL binaire attendu"
    return b"".join(data[84 + 50 * i + 12: 84 + 50 * i + 48] for i in range(count))


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "concepts" / "parts.json"
    manifest = json.loads((WEB / "manifest.json").read_text())
    for part in manifest["parts"]:
        part["positions"] = base64.b64encode(triangles(WEB / part["file"])).decode()
    out.write_text(json.dumps(manifest, ensure_ascii=False))
    print(f"{out} : {len(manifest['parts'])} pieces, {out.stat().st_size // 1024} ko")


if __name__ == "__main__":
    main()
