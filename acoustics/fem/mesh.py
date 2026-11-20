# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright 2026 Clement Barberousse
"""Maillage gmsh 2D axisymetrique (r = x, z = y, en metres) pour openCFS.

Baffle rigide plan en z = 0 (le visage), bouche = disque r < a_bouche en z = 0.
Le dispositif est une pile de cylindres coaxiaux poses sur le baffle :
cavite (air + anneau de mousse contre la paroi), puis les elements de l'event
(conduits a section egale, chambres). Les parois sont des trous du domaine
(Neumann = rigide). Champ libre : boite d'air entouree d'une PML rectangulaire.
"""

from __future__ import annotations

import math

import gmsh

WALL = 1.5e-3  # epaisseur des parois rigides


def device_pieces(design, gap_mm):
    """Liste des morceaux fluides (nom, materiau, r_in, r_out, z0, z1) et enveloppes solides."""
    cav, seal = design["cavity"], design["seal"]
    R = seal["perimeter_mm"] * 1e-3 / (2 * math.pi)  # meme perimetre de joint
    V, Vf = cav["volume_cm3"] * 1e-6, cav.get("foam_cm3", 0.0) * 1e-6
    L = V / (math.pi * R * R)
    rf = R * math.sqrt(1 - Vf / V)  # anneau de mousse contre la paroi, volume exact
    depth, h = seal["contact_depth_mm"] * 1e-3, gap_mm * 1e-3
    pieces = [("cav", "air", 0.0, rf, 0.0, L)]
    if Vf:
        pieces.append(("cavfoam", "foam_cav", rf, R, 0.0, L))
    hulls = [(R + depth, h, L + WALL)]  # paroi laterale = profondeur de contact du joint
    if h > 0:
        pieces.append(("slit", "slit", R, R + depth, 0.0, h))
    z = L
    for i, e in enumerate(design["vent"]["elements"]):
        if e["type"] == "screen":
            continue  # shortcut: ecrans resistifs ignores en FEM (impedance << conduit), a ajouter en couche si besoin
        if e["type"] in ("duct", "hole"):
            if e["type"] == "duct":
                area = e["width"] * e["height"] * e.get("count", 1) * 1e-6
            else:
                area = e.get("count", 1) * math.pi * (e["diameter"] * 1e-3) ** 2 / 4
            r, length = math.sqrt(area / math.pi), e["length"] * 1e-3
            pieces.append((f"vent{i}", f"vent{i}", 0.0, r, z, z + length))
            hulls.append((r + WALL, z - WALL, z + length))
        elif e["type"] == "chamber":
            # chambre : meme rayon que la cavite, anneau de mousse contre la paroi
            vc, vcf = e["volume_cm3"] * 1e-6, e.get("foam_cm3", 0.0) * 1e-6
            length = vc / (math.pi * R * R)
            rcf = R * math.sqrt(1 - vcf / vc)
            pieces.append((f"vent{i}", "air", 0.0, rcf, z, z + length))
            if vcf:
                pieces.append((f"vent{i}foam", f"foam{i}", rcf, R, z, z + length))
            hulls.append((R + WALL, z - WALL, z + length + WALL))
        else:
            raise ValueError(e["type"])
        z += length
    geo = {"R": R, "L": L, "rf": rf, "z_out": z, "r_out": pieces[-1][3] if pieces[-1][0].startswith("vent") else None}
    return pieces, hulls, geo


def build(path, pieces, hulls, mouth_r, box, h_far, order=2):
    """Ecrit le maillage MSH 2.2. box = (r, z) de la surface de mesure, couche d'air, PML. Retourne les groupes."""
    rmax, zmax, shell, pml = box
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add("silentmic")
    occ = gmsh.model.occ
    # la puissance est integree sur une frontiere interne air/air (pas sur l'interface PML)
    box_air = occ.addRectangle(0, 0, 0, rmax, zmax)
    box_mid = occ.addRectangle(0, 0, 0, rmax + shell, zmax + shell)
    box_all = occ.addRectangle(0, 0, 0, rmax + shell + pml, zmax + shell + pml)
    pml_tag = occ.cut([(2, box_all)], [(2, box_mid)], removeTool=False)[0][0][1]
    air2 = occ.cut([(2, box_mid)], [(2, box_air)], removeTool=False)[0][0][1]
    fluids = [(p[0], p[1], occ.addRectangle(p[2], p[4], 0, p[3] - p[2], p[5] - p[4])) for p in pieces]
    solids = [occ.addRectangle(0, z0, 0, r, z1 - z0) for r, z0, z1 in hulls]
    tools = [(2, t) for t in solids] + [(2, f[2]) for f in fluids]
    if tools:
        air = occ.cut([(2, box_air)], tools, removeObject=True, removeTool=False)[0]
        occ.remove([(2, t) for t in solids])
    else:
        air = [(2, box_air)]
    mouth = occ.addLine(occ.addPoint(0, 0, 0), occ.addPoint(mouth_r, 0, 0))
    objs = air + [(2, f[2]) for f in fluids] + [(2, air2), (2, pml_tag)]
    _, mapping = occ.fragment(objs, [(1, mouth)])
    occ.synchronize()
    surf_of = {}
    for (dim, tag), new in zip(objs, mapping):
        surf_of[(dim, tag)] = [t for d, t in new if d == 2]
    groups = {"air": [t for a in air for t in surf_of[a]], "air2": surf_of[(2, air2)], "pml": surf_of[(2, pml_tag)]}
    for name, _, tag in fluids:
        groups[name] = surf_of[(2, tag)]

    # lignes : bouche (z = 0, r < a) et surface de mesure de la puissance (air/air, avant la PML)
    def lines(pred):
        out = []
        for _, c in gmsh.model.getEntities(1):
            x0, y0, _, x1, y1, _ = gmsh.model.getBoundingBox(1, c)
            if pred(x0, y0, x1, y1):
                out.append(c)
        return out

    eps = 1e-6  # tolerance OCC des boites englobantes
    lgroups = {
        "mouth": lines(lambda x0, y0, x1, y1: y1 < eps and x1 <= mouth_r + eps),
        "far": lines(lambda x0, y0, x1, y1: (abs(x0 - rmax) < eps and abs(x1 - rmax) < eps and y1 <= zmax + eps)
                     or (abs(y0 - zmax) < eps and abs(y1 - zmax) < eps and x1 <= rmax + eps)),
    }
    # pas de puissance sur les sorties internes (fente, event) : acouPower y prend la vitesse d'un seul cote
    # et ne conserve pas l'energie (essai v3-A : signe et module faux), on mesure le debit par deux micros
    for name, tags in groups.items():
        gmsh.model.addPhysicalGroup(2, tags, name=name)
    for name, tags in lgroups.items():
        assert tags, f"groupe de lignes vide : {name}"
        gmsh.model.addPhysicalGroup(1, tags, name=name)

    # tailles : h_far loin, plus fin dans le dispositif, >= 3 elements dans conduits et fente
    fields = []
    for name, mat, r0, r1, z0, z1 in pieces:
        size = min((r1 - r0) / 3, (z1 - z0) / 3, 3e-3)
        f = gmsh.model.mesh.field.add("Box")
        for k, v in (("VIn", size), ("VOut", h_far), ("XMin", r0), ("XMax", r1), ("YMin", z0), ("YMax", z1),
                     ("Thickness", 10 * size)):
            gmsh.model.mesh.field.setNumber(f, k, v)
        fields.append(f)
    f = gmsh.model.mesh.field.add("Ball")  # bouche
    for k, v in (("Radius", 2 * mouth_r), ("VIn", mouth_r / 4), ("VOut", h_far), ("Thickness", 0.02)):
        gmsh.model.mesh.field.setNumber(f, k, v)
    fields.append(f)
    # gradation 3 mm -> h_far en s'eloignant du dispositif (grands domaines en basses frequences)
    r_dev = max([mouth_r] + [p[3] for p in pieces] + [h[0] for h in hulls])
    z_dev = max([0.0] + [p[5] for p in pieces] + [h[2] for h in hulls])
    f = gmsh.model.mesh.field.add("Distance")
    gmsh.model.mesh.field.setNumbers(f, "CurvesList", lines(lambda x0, y0, x1, y1: x1 <= r_dev + eps and y1 <= z_dev + eps))
    g = gmsh.model.mesh.field.add("Threshold")
    for k, v in (("InField", f), ("SizeMin", 3e-3), ("SizeMax", h_far), ("DistMin", 0), ("DistMax", h_far / 0.3)):
        gmsh.model.mesh.field.setNumber(g, k, v)
    fields.append(g)
    fmin = gmsh.model.mesh.field.add("Min")
    gmsh.model.mesh.field.setNumbers(fmin, "FieldsList", fields)
    gmsh.model.mesh.field.setAsBackgroundMesh(fmin)
    gmsh.option.setNumber("Mesh.MeshSizeMax", h_far)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.model.mesh.generate(2)
    gmsh.model.mesh.setOrder(order)
    gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
    gmsh.write(str(path))
    n = len(gmsh.model.mesh.getNodes()[0])
    gmsh.finalize()
    return list(groups), list(lgroups), n
