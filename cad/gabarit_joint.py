# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright 2026 Clement Barberousse
"""Gabarit de decoupe du joint capot/coque (Clement, 26 nov. 2026) : un anneau de PLA a la forme du joint, pose sur la
mousse et suivi au cutter, bord exterieur puis bord interieur. Un anneau d'une piece, sans raccord : une bande droite
recollee bout a bout laisse un jour ou une surepaisseur au raccord.

Le joint est la forme de la CAO (offsets 6.0 a 9.0 mm de la peau, au fond de la rainure de 3.2 mm) ; le gabarit fait
0.1 mm de moins par bord, ce que la lame rajoute en suivant l'arete. Mousse : deux couches de neoprene adhesif de
1.5 mm (3 mm, ecrasees a 1.45 mm, 52 %) ou une plaque d'EPDM cellulaire de 3 mm.

    cad/guarded.sh -m 3 -t 300 .venv/bin/python cad/gabarit_joint.py   -> cad/out/v3-galet/coupons/gabarit-joint.stl
"""
import sys
from pathlib import Path

import cadquery as cq

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import silent_mic_v3_galet as g  # noqa: E402

THICK = 2.0  # assez haut pour guider la lame
z = g.GROOVE_DEPTH  # fond de la rainure : la mousse y est posee
d0, d1 = g.GROOVE[0] + 0.2, g.GROOVE[1] - 0.2
part = g.ring(d0, d1, z, z + THICK).translate((0, 0, -z))
bb = part.val().BoundingBox()
assert abs(bb.zmin) < 1e-6 and abs(bb.zlen - THICK) < 1e-6, bb
out = HERE / "out/v3-galet/coupons/gabarit-joint.stl"
cq.exporters.export(part, str(out), tolerance=0.02, angularTolerance=0.1)
print(f"{out.name} : {bb.xlen:.1f} x {bb.ylen:.1f} mm, anneau de {d1 - d0:.1f} mm, joint de la CAO 3.0 mm, rainure "
      f"{g.GROOVE[1] - g.GROOVE[0]:.1f} mm ; ecrasement d'une mousse de 3 mm : {(3.0 - (g.GROOVE_DEPTH - g.TONGUE[2])) / 3.0 * 100:.0f} %")
