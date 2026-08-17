# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright 2026 Clement Barberousse

from pathlib import Path
import math

import cadquery as cq


# Dimensions officielles DJI, en millimetres.
MIC_SIZE = (28.58, 28.04, 13.52)
DONGLE_SIZE = (39.26, 27.26, 8.97)

# Dimensions nominales du coussin Brainwavz B00X5ISRGI. Le fabricant annonce
# une variation de quelques millimetres: valider le fit-test avant la coque.
PAD_OUTER = (110.0, 90.0)
PAD_OPENING = (70.0, 50.0)
PAD_THICKNESS = 30.0
LIP_CLEARANCE = 2.5
LIP_WALL = 2.0
LIP_HEIGHT = 3.0
LIP_EDGE_FILLET = 0.95
CUSHION_EDGE_FILLET = 2.0
LIP_OUTER = tuple(size - 2 * LIP_CLEARANCE for size in PAD_OPENING)
LIP_INNER = tuple(size - 2 * LIP_WALL for size in LIP_OUTER)

# Une coupelle compacte, mais assez profonde pour placer le micro au fond.
SHELL_DEPTH = 62.0
WALL = 3.0
TIP_OUTER = (44.0, 32.0)
SHOULDER_OUTER = (72.0, 54.0)
BACK_OUTER = (92.0, 72.0)
FRONT_OUTER = (110.0, 92.0)
FLOOR_INNER = (58.0, 46.0)
BACK_INNER = (84.0, 64.0)
FRONT_INNER = (104.0, 86.0)
THROAT_OPENING = LIP_INNER
SHOULDER_Z = 7.0
FLOOR_Z = 12.0
BACK_SECTION_Z = 18.0
FRONT_LOFT_Z = 86.0
# Rayon transversal mesure sur les headforms NIOSH small/large autour de la
# bouche. Le coussin souple absorbe le reste de la variabilite du visage.
FACE_RADIUS = 105.0

FOAM_THICKNESS = 12.7  # 0.5 inch, mousse Amazon B0FFBG6ZZZ
FOAM_MIC_CLEARANCE = 0.5
MIC_X = 0.0
MIC_Z = FLOOR_Z + FOAM_THICKNESS + FOAM_MIC_CLEARANCE
MOUNT_WIDTH = 28.0
MOUNT_BASE_WIDTH = 42.0  # renfort uniquement a gauche/droite, pas avant/arriere
MOUNT_BASE_HEIGHT = 9.0
MOUNT_THICKNESS = 4.0
MOUNT_HEIGHT = 42.0
MOUNT_EDGE_FILLET = 2.4
MIC_STEEL_DISC_DIAMETER = 30.0  # plaque PATIKIL deja achetee
MIC_STEEL_DISC_THICKNESS = 0.3
MOUNT_SHIFT_Y = 5.5
MOUNT_Y = -(MIC_STEEL_DISC_THICKNESS + MIC_SIZE[2]) / 2 + MOUNT_SHIFT_Y
DONGLE_Z = 28.0
DONGLE_MAGNET_DIAMETER = 8.0
DONGLE_MAGNET_THICKNESS = 1.0
DONGLE_STEEL_DISC_DIAMETER = 30.0  # depasse le dongle de 1.37 mm en haut/bas
DONGLE_STEEL_DISC_THICKNESS = 0.3
STEEL_DISC_MAX_OVERHANG = 1.5
DONGLE_CLEARANCE = 0.5
COMPONENT_TOLERANCE = 1.0
AIR_GAP_TARGET = 8.0


def ellipse_prism(width: float, height: float, depth: float, z: float = 0.0):
    return (
        cq.Workplane("XY", origin=(0, 0, z))
        .ellipse(width / 2, height / 2)
        .extrude(depth)
    )


def ellipse_wire(width: float, height: float, z: float):
    return (
        cq.Workplane("XY", origin=(0, 0, z))
        .ellipse(width / 2, height / 2)
        .wire()
        .val()
    )


def face_cut_cylinder(radius: float, center_depth: float = SHELL_DEPTH):
    """Cylinder above the concave face surface, used as a cutting tool."""
    center_z = center_depth + radius
    solid = cq.Solid.makeCylinder(
        radius,
        240,
        cq.Vector(0, -120, center_z),
        cq.Vector(0, 1, 0),
    )
    return cq.Workplane("XY").newObject([solid])


def face_volume_below(radius: float, center_depth: float):
    stock = (
        cq.Workplane("XY", origin=(0, 0, -5))
        .box(180, 160, center_depth + 70, centered=(True, True, False))
    )
    return stock.cut(face_cut_cylinder(radius, center_depth))


def face_depth_at_x(x: float, radius: float = FACE_RADIUS):
    return SHELL_DEPTH + radius - math.sqrt(radius**2 - x**2)


def inner_half_size_at_z(z: float, axis: int):
    if z <= BACK_SECTION_Z:
        ratio = (z - FLOOR_Z) / (BACK_SECTION_Z - FLOOR_Z)
        start, end = FLOOR_INNER[axis], BACK_INNER[axis]
    else:
        ratio = (z - BACK_SECTION_Z) / (FRONT_LOFT_Z - BACK_SECTION_Z)
        start, end = BACK_INNER[axis], FRONT_INNER[axis]
    return (start + ratio * (end - start)) / 2


def build_inner_cavity():
    cavity = cq.Workplane("XY").newObject(
        [
            cq.Solid.makeLoft(
                [
                    ellipse_wire(*FLOOR_INNER, FLOOR_Z),
                    ellipse_wire(*BACK_INNER, BACK_SECTION_Z),
                    ellipse_wire(*FRONT_INNER, FRONT_LOFT_Z),
                ],
                ruled=True,
            )
        ]
    )
    ceiling = (
        cq.Workplane("XY", origin=(0, 0, -5))
        .box(180, 160, SHELL_DEPTH - WALL + 5, centered=(True, True, False))
    )
    return cavity.intersect(ceiling)


def build_vertical_mount():
    mount = (
        cq.Workplane("XZ", origin=(MIC_X, MOUNT_Y, FLOOR_Z - 0.4))
        .moveTo(-MOUNT_BASE_WIDTH / 2, 0)
        .lineTo(MOUNT_BASE_WIDTH / 2, 0)
        .lineTo(MOUNT_WIDTH / 2, MOUNT_BASE_HEIGHT)
        .lineTo(MOUNT_WIDTH / 2, MOUNT_HEIGHT + 0.4)
        .lineTo(-MOUNT_WIDTH / 2, MOUNT_HEIGHT + 0.4)
        .lineTo(-MOUNT_WIDTH / 2, MOUNT_BASE_HEIGHT)
        .close()
        .extrude(MOUNT_THICKNESS / 2, both=True)
        .edges("|Y")
        .fillet(MOUNT_EDGE_FILLET)
    )
    return mount


def build_face_lip():
    ring = ellipse_prism(*LIP_OUTER, 300, -150).cut(
        ellipse_prism(*LIP_INNER, 300, -150)
    )
    lip = (
        face_volume_below(FACE_RADIUS, SHELL_DEPTH + LIP_HEIGHT)
        .cut(face_volume_below(FACE_RADIUS, SHELL_DEPTH - 0.4))
        .intersect(ring)
    )
    return lip.edges().fillet(LIP_EDGE_FILLET)


def build_shell():
    outer = cq.Workplane("XY").newObject(
        [
            cq.Solid.makeLoft(
                [
                    ellipse_wire(*TIP_OUTER, 0),
                    ellipse_wire(*SHOULDER_OUTER, SHOULDER_Z),
                    ellipse_wire(*BACK_OUTER, BACK_SECTION_Z),
                    ellipse_wire(*FRONT_OUTER, FRONT_LOFT_Z),
                ],
                ruled=False,
            )
        ]
    ).intersect(
        cq.Workplane("XY")
        .box(180, 160, FRONT_LOFT_Z + 10, centered=(True, True, False))
    )
    # On retire le cylindre situe devant le visage. La surface restante est
    # concave: les cotes avancent vers les joues au lieu de reculer.
    outer = outer.cut(face_cut_cylinder(FACE_RADIUS, SHELL_DEPTH))
    inner = build_inner_cavity()
    cavity_leak = sum(s.Volume() for s in inner.cut(outer).solids().vals())
    assert cavity_leak < 1e-6, f"La cavite traverse la coque: {cavity_leak:.2f} mm3"
    mouth_opening = ellipse_prism(*THROAT_OPENING, 40, SHELL_DEPTH - WALL - 0.5)
    shell = (
        outer.cut(inner)
        .cut(mouth_opening)
        .union(build_face_lip())
    )
    shell = shell.union(build_vertical_mount()).intersect(
        cq.Workplane("XY")
        .box(180, 160, FRONT_LOFT_Z + 10, centered=(True, True, False))
    )
    return shell.edges(cq.selectors.LengthNthSelector(-1)).fillet(
        CUSHION_EDGE_FILLET
    )


def build_references(shell):
    mount_front = MOUNT_Y + MOUNT_THICKNESS / 2
    mic_center_z = MIC_Z + MIC_SIZE[1] / 2
    mic_steel_disc_solid = cq.Solid.makeCylinder(
        MIC_STEEL_DISC_DIAMETER / 2,
        MIC_STEEL_DISC_THICKNESS,
        cq.Vector(MIC_X, mount_front, mic_center_z),
        cq.Vector(0, 1, 0),
    )
    mic_steel_disc = cq.Workplane("XY").newObject([mic_steel_disc_solid])
    mic_center_y = mount_front + MIC_STEEL_DISC_THICKNESS + MIC_SIZE[2] / 2
    mic = (
        cq.Workplane("XY", origin=(MIC_X, mic_center_y, MIC_Z))
        .box(
            MIC_SIZE[0],
            MIC_SIZE[2],
            MIC_SIZE[1],
            centered=(True, True, False),
        )
    )
    mount_back = MOUNT_Y - MOUNT_THICKNESS / 2
    dongle_center_z = DONGLE_Z + DONGLE_SIZE[1] / 2
    dongle_magnet = cq.Workplane("XY").newObject(
        [
            cq.Solid.makeCylinder(
                DONGLE_MAGNET_DIAMETER / 2,
                DONGLE_MAGNET_THICKNESS,
                cq.Vector(MIC_X, mount_back, dongle_center_z),
                cq.Vector(0, -1, 0),
            )
        ]
    )
    dongle_steel_disc = cq.Workplane("XY").newObject(
        [
            cq.Solid.makeCylinder(
                DONGLE_STEEL_DISC_DIAMETER / 2,
                DONGLE_STEEL_DISC_THICKNESS,
                cq.Vector(
                    MIC_X,
                    mount_back - DONGLE_MAGNET_THICKNESS,
                    dongle_center_z,
                ),
                cq.Vector(0, -1, 0),
            )
        ]
    )
    dongle = (
        cq.Workplane(
            "XY",
            origin=(
                MIC_X,
                mount_back
                - DONGLE_MAGNET_THICKNESS
                - DONGLE_STEEL_DISC_THICKNESS
                - DONGLE_SIZE[2] / 2,
                DONGLE_Z,
            ),
        )
        .box(
            DONGLE_SIZE[0],
            DONGLE_SIZE[2],
            DONGLE_SIZE[1],
            centered=(True, True, False),
        )
    )

    profile = ellipse_prism(*PAD_OUTER, 300, -150).cut(
        ellipse_prism(*PAD_OPENING, 300, -150)
    )
    cushion = (
        face_volume_below(FACE_RADIUS, SHELL_DEPTH + PAD_THICKNESS)
        .cut(face_volume_below(FACE_RADIUS, SHELL_DEPTH))
        .intersect(profile)
    )
    mesh = (
        face_volume_below(FACE_RADIUS, SHELL_DEPTH)
        .cut(face_volume_below(FACE_RADIUS, SHELL_DEPTH - 0.4))
        .intersect(ellipse_prism(*THROAT_OPENING, 300, -150))
    )

    foam_core = cq.Workplane("XY").newObject(
        [
            cq.Solid.makeLoft(
                [
                    ellipse_wire(
                        BACK_INNER[0] - 2 * FOAM_THICKNESS,
                        BACK_INNER[1] - 2 * FOAM_THICKNESS,
                        FLOOR_Z + 1,
                    ),
                    ellipse_wire(
                        FRONT_INNER[0] - 2 * FOAM_THICKNESS,
                        FRONT_INNER[1] - 2 * FOAM_THICKNESS,
                        FRONT_LOFT_Z,
                    ),
                ],
                ruled=False,
            )
        ]
    ).cut(face_cut_cylinder(FACE_RADIUS - WALL - FOAM_THICKNESS, SHELL_DEPTH - WALL))
    wall_foam = (
        build_inner_cavity()
        .cut(foam_core)
        .cut(shell)
        .cut(mic_steel_disc)
        .cut(mic)
    )
    floor_foam = (
        ellipse_prism(
            BACK_INNER[0] - 4,
            BACK_INNER[1] - 4,
            FOAM_THICKNESS,
            FLOOR_Z,
        )
        .intersect(build_inner_cavity())
        .cut(shell)
        .cut(mic_steel_disc)
        .cut(mic)
    )
    foam = wall_foam.union(floor_foam)
    return (
        mic_steel_disc,
        mic,
        dongle,
        dongle_magnet,
        dongle_steel_disc,
        cushion,
        mesh,
        foam,
    )


def check_layout(
    shell,
    mic_steel_disc,
    mic,
    dongle,
    dongle_magnet,
    dongle_steel_disc,
    foam,
):
    assert shell.val().isValid(), "La coque CadQuery n'est pas un solide valide"
    solid_count = shell.solids().size()
    volumes = [round(s.Volume(), 2) for s in shell.solids().vals()]
    assert solid_count == 1, f"La coque contient {solid_count} solides: {volumes} mm3"
    mic_front = mic.val().BoundingBox().zmax
    air_gap = face_depth_at_x(MIC_X) - mic_front
    assert air_gap >= AIR_GAP_TARGET, f"Air gap insuffisant: {air_gap:.2f} mm"
    mic_shell_overlap = mic.intersect(shell).val().Volume()
    assert mic_shell_overlap < 1e-6, f"Collision micro/coque: {mic_shell_overlap:.2f} mm3"
    mic_steel_disc_box = mic_steel_disc.val().BoundingBox()
    mic_box = mic.val().BoundingBox()
    mic_opening_clearance = THROAT_OPENING[1] / 2 - max(
        abs(mic_box.ymin), abs(mic_box.ymax)
    )
    assert mic_opening_clearance >= 5.0, "Micro trop proche du bord de l'ouverture"
    assert abs(mic_steel_disc_box.ymax - mic_box.ymin) < 1e-6, (
        "Plaque acier non plaquee au micro"
    )
    assert max(
        mic_box.zmin - mic_steel_disc_box.zmin,
        mic_steel_disc_box.zmax - mic_box.zmax,
    ) <= STEEL_DISC_MAX_OVERHANG
    assert FLOOR_Z + MOUNT_HEIGHT >= mic_box.zmax, "Support vertical trop court"
    foam_under_mic = mic_box.zmin - FLOOR_Z
    assert foam_under_mic >= FOAM_THICKNESS + FOAM_MIC_CLEARANCE - 1e-6, (
        "Marge mousse sous le micro insuffisante"
    )
    mount_box = build_vertical_mount().val().BoundingBox()
    assert mount_box.xlen >= MOUNT_WIDTH + 8.0, (
        f"Base support trop etroite: {mount_box.xlen:.2f} mm"
    )
    assert abs(mount_box.ylen - MOUNT_THICKNESS) < 1e-6, (
        "Le renfort du support ne doit pas grossir vers l'avant/arriere"
    )
    assert MOUNT_THICKNESS >= 4.0
    assembly_ymin = min(mount_box.ymin, mic_steel_disc_box.ymin, mic_box.ymin)
    assembly_ymax = max(mount_box.ymax, mic_steel_disc_box.ymax, mic_box.ymax)
    assembly_center_y = (assembly_ymin + assembly_ymax) / 2
    assert abs(assembly_center_y - MOUNT_SHIFT_Y) < 1e-6
    mount_clearance = FLOOR_INNER[1] / 2 - max(
        abs(mount_box.ymin), abs(mount_box.ymax)
    )
    mic_clearance = inner_half_size_at_z(MIC_Z, 1) - max(
        abs(mic_box.ymin), abs(mic_box.ymax)
    )
    foam_side_clearance = min(mount_clearance, mic_clearance)
    assert foam_side_clearance >= FOAM_THICKNESS, "Marge mousse laterale insuffisante"
    dongle_box = dongle.val().BoundingBox()
    dongle_magnet_box = dongle_magnet.val().BoundingBox()
    steel_disc_box = dongle_steel_disc.val().BoundingBox()
    assert abs(dongle_magnet_box.ymax - mount_box.ymin) < 1e-6
    assert abs(steel_disc_box.ymax - dongle_magnet_box.ymin) < 1e-6
    assert abs(dongle_box.ymax - steel_disc_box.ymin) < 1e-6
    assert dongle_magnet_box.zmin >= dongle_box.zmin
    assert dongle_magnet_box.zmax <= dongle_box.zmax
    assert max(
        dongle_box.zmin - steel_disc_box.zmin,
        steel_disc_box.zmax - dongle_box.zmax,
    ) <= STEEL_DISC_MAX_OVERHANG
    assert dongle_box.zmax <= SHELL_DEPTH - WALL - DONGLE_CLEARANCE
    dongle_foam_clearance = inner_half_size_at_z(DONGLE_Z, 1) + dongle_box.ymin
    required_foam_clearance = FOAM_THICKNESS + DONGLE_CLEARANCE + COMPONENT_TOLERANCE
    assert dongle_foam_clearance >= required_foam_clearance
    dongle_side_clearance = inner_half_size_at_z(DONGLE_Z, 0) - max(
        abs(dongle_box.xmin), abs(dongle_box.xmax)
    )
    assert dongle_side_clearance >= required_foam_clearance
    dongle_shell_overlap = dongle.intersect(shell).val().Volume()
    assert dongle_shell_overlap < 1e-6
    foam_dongle_overlap = foam.intersect(dongle).val().Volume()
    foam_magnet_overlap = foam.intersect(dongle_magnet).val().Volume()
    foam_disc_overlap = foam.intersect(dongle_steel_disc).val().Volume()
    assert foam_dongle_overlap < 1e-6, (
        f"Collision mousse/dongle: {foam_dongle_overlap:.2f} mm3"
    )
    assert foam_magnet_overlap < 1e-6, (
        f"Collision mousse/aimant dongle: {foam_magnet_overlap:.2f} mm3"
    )
    assert foam_disc_overlap < 1e-6, (
        f"Collision mousse/disque acier: {foam_disc_overlap:.2f} mm3"
    )
    dongle_net_margin = min(dongle_foam_clearance, dongle_side_clearance) - (
        FOAM_THICKNESS + COMPONENT_TOLERANCE
    )
    return (
        air_gap,
        foam_side_clearance,
        foam_under_mic,
        dongle_foam_clearance,
        dongle_side_clearance,
        dongle_net_margin,
        mic_opening_clearance,
    )


def export():
    shell = build_shell()
    (
        mic_steel_disc,
        mic,
        dongle,
        dongle_magnet,
        dongle_steel_disc,
        cushion,
        mesh,
        foam,
    ) = build_references(shell)
    (
        air_gap,
        foam_side_clearance,
        foam_under_mic,
        dongle_foam_clearance,
        dongle_side_clearance,
        dongle_net_margin,
        mic_opening_clearance,
    ) = check_layout(
        shell,
        mic_steel_disc,
        mic,
        dongle,
        dongle_magnet,
        dongle_steel_disc,
        foam,
    )

    output = Path(__file__).with_name("out")
    output.mkdir(exist_ok=True)
    cq.exporters.export(shell, str(output / "whisper-mask-v0.stl"))
    cq.exporters.export(shell, str(output / "whisper-mask-v0.step"))
    cq.exporters.export(
        shell,
        str(output / "whisper-mask-v0-print-plate.stl"),
    )

    fit_test = shell.cut(build_vertical_mount()).intersect(
        cq.Workplane("XY", origin=(0, 0, SHELL_DEPTH - 12))
        .box(140, 120, 20, centered=(True, True, False))
    )
    assert fit_test.solids().size() == 1
    cq.exporters.export(fit_test, str(output / "whisper-mask-v0-fit-test.stl"))
    cq.exporters.export(fit_test, str(output / "whisper-mask-v0-fit-test.step"))

    assembly = cq.Assembly(name="whisper-mask-v0-layout")
    assembly.add(shell, name="printed-shell", color=cq.Color(0.75, 0.75, 0.75))
    assembly.add(foam, name="foam-cut-template", color=cq.Color(0.15, 0.15, 0.15, 0.45))
    assembly.add(
        mic_steel_disc,
        name="mic-steel-disc-30mm",
        color=cq.Color(0.65, 0.65, 0.7),
    )
    assembly.add(mic, name="dji-mic-mini-2", color=cq.Color(0.03, 0.03, 0.03))
    assembly.add(dongle, name="dji-usb-c-dongle", color=cq.Color(0.9, 0.45, 0.05))
    assembly.add(dongle_magnet, name="dongle-magnet", color=cq.Color(0.65, 0.65, 0.7))
    assembly.add(
        dongle_steel_disc,
        name="dongle-steel-disc",
        color=cq.Color(0.25, 0.25, 0.28),
    )
    assembly.add(cushion, name="brainwavz-cushion", color=cq.Color(0.05, 0.08, 0.2, 0.35))
    assembly.add(mesh, name="existing-pop-mesh", color=cq.Color(0.1, 0.1, 0.1, 0.5))
    assembly.export(str(output / "whisper-mask-v0-layout.step"))

    print(f"OK: air gap micro/ouverture = {air_gap:.2f} mm")
    print(f"OK: DJI vertical, mousse modelisee = {FOAM_THICKNESS:.2f} mm")
    print(f"OK: mousse sous le micro = {foam_under_mic:.2f} mm")
    print(f"OK: marge mousse laterale minimale = {foam_side_clearance:.2f} mm")
    print(f"OK: mousse derriere le dongle = {dongle_foam_clearance:.2f} mm")
    print(f"OK: mousse laterale dongle = {dongle_side_clearance:.2f} mm")
    print(f"OK: marge nette dongle = {dongle_net_margin:.2f} mm")
    print(f"OK: marge micro/bord ouverture = {mic_opening_clearance:.2f} mm")
    print(f"Exports: {output}")
    return (
        shell,
        mic_steel_disc,
        mic,
        dongle,
        dongle_magnet,
        dongle_steel_disc,
        cushion,
        mesh,
        foam,
    )


if __name__ == "__main__" or "show_object" in globals():
    (
        shell,
        mic_steel_disc,
        mic,
        dongle,
        dongle_magnet,
        dongle_steel_disc,
        cushion,
        mesh,
        foam,
    ) = export()

if "show_object" in globals():
    show_object(
        shell,
        name="printed-shell",
        options={"color": "lightgray", "alpha": 0.25},
    )
    show_object(
        foam,
        name="foam-12.7mm-reference",
        options={"color": "darkslategray", "alpha": 0.65},
    )
    show_object(
        cushion,
        name="face-cushion",
        options={"color": "navy", "alpha": 0.35},
    )
    show_object(
        mic_steel_disc,
        name="mic-steel-disc-30mm",
        options={"color": "silver"},
    )
    show_object(mic, name="dji-mic-mini-2", options={"color": "black"})
    show_object(dongle, name="dji-usb-c-dongle", options={"color": "darkorange"})
    show_object(dongle_magnet, name="dongle-magnet", options={"color": "silver"})
    show_object(
        dongle_steel_disc,
        name="dongle-steel-disc",
        options={"color": "dimgray"},
    )
