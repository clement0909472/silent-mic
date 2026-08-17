# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright 2026 Clement Barberousse

from pathlib import Path
import math
import sys

import cadquery as cq


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import whisper_mask_v0 as v1


# Variante demontable: la coupelle et le manche sont imprimes separement.
# Quatre vis M3 fraisees accessibles par-dessous serrent des ecrous captifs
# inseres depuis la chambre avant assemblage.
JOIN_Z = v1.SHOULDER_Z
M3_CLEARANCE_DIAMETER = 3.6
M3_HEAD_DIAMETER = 6.2
M3_HEAD_DEPTH = 1.8
M3_NUT_POCKET_DIAMETER = 6.7
M3_NUT_POCKET_DEPTH = 2.6
SCREW_POSITIONS = ((-32.0, -19.0), (-32.0, 19.0), (32.0, -19.0), (32.0, 19.0))
FLANGE_OUTER = (88.0, 70.0)
FLANGE_INNER = (66.0, 48.0)
GASKET_OUTER = (84.0, 66.0)
GASKET_INNER = (70.0, 52.0)
GASKET_THICKNESS = 1.0

HANDLE_OUTER_SECTIONS = (
    (42.0, 32.0, -105.0, -26.0),
    (46.0, 35.0, -98.0, -24.0),
    (50.0, 38.0, -75.0, -18.0),
    (58.0, 43.0, -45.0, -11.0),
    (66.0, 49.0, -15.0, -4.0),
    (68.0, 51.0, 0.0, -1.5),
    (72.0, 54.0, JOIN_Z, 0.0),
)
HANDLE_INNER_SECTIONS = (
    (34.0, 24.0, -97.0, -24.5),
    (38.0, 27.0, -90.0, -22.5),
    (42.0, 30.0, -72.0, -17.2),
    (50.0, 35.0, -42.0, -10.2),
    (58.0, 42.0, -12.0, -3.5),
    (60.0, 44.0, JOIN_Z, 0.0),
)
INLET_CENTER = (-18.0, -8.0, 10.5)
INLET_SIZE = (16.0, 10.0, 12.0)
EXHAUST_DIAMETER = 12.0
EXHAUST_X = 9.0
EXHAUST_Y = 7.0
HANDLE_BOTTOM_Y = HANDLE_OUTER_SECTIONS[0][3]
HANDLE_BOTTOM_Z = HANDLE_OUTER_SECTIONS[0][2]
EXHAUST_ORIGIN_Z = HANDLE_BOTTOM_Z - 3.0
SOLE_CLEARANCE = 4.0
SOLE_OVERLAP = 0.8
SOLE_HEIGHT = SOLE_CLEARANCE + SOLE_OVERLAP
SOLE_BASE_Z = HANDLE_BOTTOM_Z - SOLE_CLEARANCE
SOLE_OUTER_MARGIN = 4.0
SOLE_RING_WIDTH = 8.0
SOLE_VENT_WIDTH = 20.0
LOWER_PRINT_LIFT = -SOLE_BASE_Z
PRINT_UPPER_XY = (0.0, -40.0)
PRINT_LOWER_XY = (0.0, 45.0)
PRINT_LOWER_ROTATION = 0.0
HANDLE_FOAM_THICKNESS = 12.7
HANDLE_FOAM_DEPTH = 18.0
HANDLE_FOAM_CENTER_Y = -14.0
HANDLE_FOAM_BOTTOM_Z = -88.0
HANDLE_FOAM_HEIGHT = 68.0

# Paroi droite fixee au fond. L'air descend a gauche, passe au-dessus, puis
# redescend a droite vers les sorties.
DIVIDER_X = 0.0
DIVIDER_BOTTOM_Z = -103.0
DIVIDER_TOP_Z = -12.0
DIVIDER_THICKNESS = 3.0


def ellipse_ring(outer, inner, z, height):
    return v1.ellipse_prism(*outer, height, z).cut(
        v1.ellipse_prism(*inner, height, z)
    )


def loft_ellipses(sections):
    return cq.Workplane("XY").newObject(
        [
            cq.Solid.makeLoft(
                [
                    cq.Workplane("XY", origin=(0, center_y, z))
                    .ellipse(width / 2, height / 2)
                    .wire()
                    .val()
                    for width, height, z, center_y in sections
                ],
                ruled=False,
            )
        ]
    )


def build_handle_outer():
    return loft_ellipses(HANDLE_OUTER_SECTIONS)


def build_handle_inner():
    return loft_ellipses(HANDLE_INNER_SECTIONS)


def build_inlet():
    return (
        cq.Workplane("XY", origin=INLET_CENTER)
        .box(*INLET_SIZE, centered=(True, True, True))
        .edges("|Z")
        .fillet(2.0)
    )


def build_exhaust_ports():
    ports = None
    for y in (-EXHAUST_Y, EXHAUST_Y):
        port = (
            cq.Workplane(
                "XY", origin=(EXHAUST_X, HANDLE_BOTTOM_Y + y, EXHAUST_ORIGIN_Z)
            )
            .circle(EXHAUST_DIAMETER / 2)
            .extrude(15.0)
        )
        ports = port if ports is None else ports.union(port)
    return ports


def build_divider():
    height = DIVIDER_TOP_Z - DIVIDER_BOTTOM_Z
    return (
        cq.Workplane("XY", origin=(DIVIDER_X, 0.0, DIVIDER_BOTTOM_Z))
        .box(DIVIDER_THICKNESS, 100.0, height, centered=(True, True, False))
        .intersect(build_handle_outer())
    )


def sole_dimensions():
    bottom_width, bottom_height = HANDLE_OUTER_SECTIONS[0][:2]
    outer = (
        bottom_width + SOLE_OUTER_MARGIN,
        bottom_height + SOLE_OUTER_MARGIN,
    )
    inner = tuple(size - 2 * SOLE_RING_WIDTH for size in outer)
    return outer, inner


def build_sole():
    outer, inner = sole_dimensions()
    envelope = (
        cq.Workplane("XY", origin=(0.0, HANDLE_BOTTOM_Y, SOLE_BASE_Z))
        .ellipse(outer[0] / 2, outer[1] / 2)
        .extrude(SOLE_HEIGHT)
    )
    opening = (
        cq.Workplane("XY", origin=(0.0, HANDLE_BOTTOM_Y, SOLE_BASE_Z - 0.1))
        .ellipse(inner[0] / 2, inner[1] / 2)
        .extrude(SOLE_HEIGHT + 0.2)
    )
    side_vents = (
        cq.Workplane("XY", origin=(0.0, HANDLE_BOTTOM_Y, SOLE_BASE_Z - 0.1))
        .box(
            outer[0] + 2.0,
            SOLE_VENT_WIDTH,
            SOLE_HEIGHT + 0.2,
            centered=(True, True, False),
        )
    )
    return envelope.cut(opening).cut(side_vents).clean()


def build_sole_air_path():
    outer, inner = sole_dimensions()
    envelope = (
        cq.Workplane("XY", origin=(0.0, HANDLE_BOTTOM_Y, SOLE_BASE_Z))
        .ellipse(outer[0] / 2, outer[1] / 2)
        .extrude(SOLE_CLEARANCE + 0.1)
    )
    opening = (
        cq.Workplane("XY", origin=(0.0, HANDLE_BOTTOM_Y, SOLE_BASE_Z))
        .ellipse(inner[0] / 2, inner[1] / 2)
        .extrude(SOLE_CLEARANCE + 0.1)
    )
    side_vents = (
        cq.Workplane("XY", origin=(0.0, HANDLE_BOTTOM_Y, SOLE_BASE_Z))
        .box(
            outer[0] + 2.0,
            SOLE_VENT_WIDTH,
            SOLE_CLEARANCE + 0.1,
            centered=(True, True, False),
        )
        .intersect(envelope)
    )
    return opening.union(side_vents).clean()


def build_screw_holes():
    holes = None
    for x, y in SCREW_POSITIONS:
        hole = (
            cq.Workplane("XY", origin=(x, y, JOIN_Z - 4.0))
            .circle(M3_CLEARANCE_DIAMETER / 2)
            .extrude(8.0)
        )
        holes = hole if holes is None else holes.union(hole)
    return holes


def build_countersinks():
    sinks = None
    for x, y in SCREW_POSITIONS:
        sink = cq.Workplane("XY").newObject(
            [
                cq.Solid.makeCone(
                    M3_HEAD_DIAMETER / 2,
                    M3_CLEARANCE_DIAMETER / 2,
                    M3_HEAD_DEPTH,
                    cq.Vector(x, y, JOIN_Z - 3.0),
                    cq.Vector(0, 0, 1),
                )
            ]
        )
        sinks = sink if sinks is None else sinks.union(sink)
    return sinks


def build_nut_pockets():
    pockets = None
    for x, y in SCREW_POSITIONS:
        pocket = (
            cq.Workplane(
                "XY", origin=(x, y, JOIN_Z + 3.0 - M3_NUT_POCKET_DEPTH)
            )
            .polygon(6, M3_NUT_POCKET_DIAMETER)
            .extrude(M3_NUT_POCKET_DEPTH)
        )
        pockets = pocket if pockets is None else pockets.union(pocket)
    return pockets


def build_upper():
    upper_half_space = (
        cq.Workplane("XY", origin=(0, 0, JOIN_Z))
        .box(180.0, 160.0, 100.0, centered=(True, True, False))
    )
    flange = ellipse_ring(FLANGE_OUTER, FLANGE_INNER, JOIN_Z, 3.0)
    return (
        v1.build_shell()
        .intersect(upper_half_space)
        .union(flange)
        .cut(build_inlet())
        .cut(build_screw_holes())
        .cut(build_nut_pockets())
        .clean()
    )


def build_lower():
    flange = ellipse_ring(FLANGE_OUTER, FLANGE_INNER, JOIN_Z - 3.0, 3.0)
    return (
        build_handle_outer()
        .cut(build_handle_inner())
        .union(flange)
        .union(build_sole())
        .cut(build_exhaust_ports())
        .union(build_divider())
        .cut(build_screw_holes())
        .cut(build_countersinks())
        .clean()
    )


def build_gasket():
    return ellipse_ring(
        GASKET_OUTER,
        GASKET_INNER,
        JOIN_Z - GASKET_THICKNESS / 2,
        GASKET_THICKNESS,
    ).cut(build_screw_holes())


def build_handle_foam_parts():
    # Deux bandes distinctes, introduites de chaque cote avant vissage.
    inner = build_handle_inner().cut(build_divider())
    left = (
        cq.Workplane(
            "XY", origin=(-16.0, HANDLE_FOAM_CENTER_Y, HANDLE_FOAM_BOTTOM_Z)
        )
        .box(
            HANDLE_FOAM_THICKNESS,
            HANDLE_FOAM_DEPTH,
            HANDLE_FOAM_HEIGHT,
            centered=(True, True, False),
        )
        .intersect(inner)
        .clean()
    )
    right = (
        cq.Workplane(
            "XY", origin=(16.0, HANDLE_FOAM_CENTER_Y, HANDLE_FOAM_BOTTOM_Z)
        )
        .box(
            HANDLE_FOAM_THICKNESS,
            HANDLE_FOAM_DEPTH,
            HANDLE_FOAM_HEIGHT,
            centered=(True, True, False),
        )
        .intersect(inner)
        .clean()
    )
    return left, right


def build_handle_foam():
    left, right = build_handle_foam_parts()
    return left.union(right).clean()


def build_air_path():
    return (
        v1.build_inner_cavity()
        .union(build_inlet())
        .union(build_handle_inner())
        .union(build_exhaust_ports())
        .union(build_sole_air_path())
        .cut(build_divider())
        .clean()
    )


def build_fastener_references():
    bolts = None
    nuts = None
    for x, y in SCREW_POSITIONS:
        bolt = (
            cq.Workplane("XY", origin=(x, y, JOIN_Z - 3.0))
            .circle(1.5)
            .extrude(6.0)
            .union(
                cq.Workplane("XY").newObject(
                    [
                        cq.Solid.makeCone(
                            M3_HEAD_DIAMETER / 2,
                            M3_CLEARANCE_DIAMETER / 2,
                            M3_HEAD_DEPTH,
                            cq.Vector(x, y, JOIN_Z - 3.0),
                            cq.Vector(0, 0, 1),
                        )
                    ]
                )
            )
        )
        nut = (
            cq.Workplane(
                "XY", origin=(x, y, JOIN_Z + 3.0 - M3_NUT_POCKET_DEPTH)
            )
            .polygon(6, 6.4)
            .extrude(2.4)
        )
        bolts = bolt if bolts is None else bolts.union(bolt)
        nuts = nut if nuts is None else nuts.union(nut)
    return bolts, nuts


def check(upper, lower, air_path, handle_foam):
    assert upper.val().isValid() and upper.solids().size() == 1
    assert lower.val().isValid() and lower.solids().size() == 1
    assert air_path.val().isValid() and air_path.solids().size() == 1
    assert upper.intersect(lower).val().Volume() < 1e-6
    assert handle_foam.intersect(upper.union(lower)).val().Volume() < 1e-6
    assert air_path.cut(handle_foam).clean().solids().size() == 1
    assert DIVIDER_TOP_Z <= -10.0, "Le passage au-dessus de la paroi est trop petit"
    assert abs(build_divider().val().Center().x - DIVIDER_X) < 1e-6
    assert build_divider().intersect(build_exhaust_ports()).val().Volume() < 1e-6
    assert 2 * EXHAUST_Y > EXHAUST_DIAMETER
    floor = (
        cq.Workplane("XY", origin=(0.0, 0.0, HANDLE_BOTTOM_Z))
        .box(100.0, 100.0, 3.0, centered=(True, True, False))
    )
    assert build_divider().intersect(floor).val().Volume() > 0
    assert upper.intersect(build_nut_pockets()).val().Volume() < 1e-6
    assert lower.intersect(build_countersinks()).val().Volume() < 1e-6
    assert 2 * SOLE_VENT_WIDTH * SOLE_CLEARANCE >= INLET_SIZE[0] * INLET_SIZE[1]


def export(output_subdir="v2-screwed", filename_stem="whisper-mask-v2-screwed"):
    upper = build_upper()
    lower = build_lower()
    air_path = build_air_path()
    divider = build_divider()
    left_foam, right_foam = build_handle_foam_parts()
    handle_foam = left_foam.union(right_foam).clean()
    gasket = build_gasket()
    bolts, nuts = build_fastener_references()
    refs = list(v1.build_references(upper))
    refs[-1] = refs[-1].cut(build_inlet())
    check(upper, lower, air_path, handle_foam)

    output = HERE / "out" / output_subdir
    output.mkdir(parents=True, exist_ok=True)
    exports = {
        "upper": upper,
        "lower": lower,
        "air-path": air_path,
        "divider": divider,
        "handle-foam": handle_foam,
        "handle-foam-left": left_foam,
        "handle-foam-right": right_foam,
        "gasket": gasket,
    }
    for name, solid in exports.items():
        cq.exporters.export(solid, str(output / f"{filename_stem}-{name}.step"))
    cq.exporters.export(bolts, str(output / "07-m3-bolts-reference.step"))
    cq.exporters.export(nuts, str(output / "08-m3-nuts-reference.step"))
    cq.exporters.export(upper, str(output / f"{filename_stem}-upper.stl"))
    cq.exporters.export(lower, str(output / f"{filename_stem}-lower.stl"))

    placed_upper = upper.translate((*PRINT_UPPER_XY, -JOIN_Z))
    placed_lower = lower.rotate(
        (0, 0, 0), (0, 0, 1), PRINT_LOWER_ROTATION
    ).translate((*PRINT_LOWER_XY, LOWER_PRINT_LIFT))
    assert placed_upper.intersect(placed_lower).val().Volume() < 1e-6
    print_plate = cq.Compound.makeCompound([placed_upper.val(), placed_lower.val()])
    plate_box = print_plate.BoundingBox()
    assert plate_box.xlen <= 180.0 and plate_box.ylen <= 180.0
    assert plate_box.zlen <= 180.0
    cq.exporters.export(
        cq.Workplane("XY").newObject([print_plate]),
        str(output / f"{filename_stem}-print-plate.stl"),
    )

    assembly = cq.Assembly(name=f"{filename_stem}-technical")
    assembly.add(upper, name="01-printed-upper", color=cq.Color(0.78, 0.78, 0.80, 0.35))
    assembly.add(lower, name="02-printed-lower", color=cq.Color(0.72, 0.75, 0.80, 0.35))
    assembly.add(divider, name="03-vertical-bottom-baffle", color=cq.Color(0.85, 0.20, 0.12))
    assembly.add(air_path, name="04-continuous-air-path", color=cq.Color(0.10, 0.70, 0.95, 0.28))
    assembly.add(left_foam, name="05a-left-handle-foam", color=cq.Color(0.20, 0.60, 0.25, 0.60))
    assembly.add(right_foam, name="05b-right-handle-foam", color=cq.Color(0.20, 0.60, 0.25, 0.60))
    assembly.add(gasket, name="06-1mm-gasket", color=cq.Color(0.95, 0.80, 0.10, 0.75))
    assembly.add(bolts, name="07-external-m3-screws-reference", color=cq.Color(0.55, 0.58, 0.62))
    assembly.add(nuts, name="08-captive-m3-nuts-reference", color=cq.Color(0.45, 0.48, 0.52))
    ref_names = (
        "09-mic-steel-disc-30mm",
        "10-dji-mic-mini-2",
        "11-dji-usb-c-dongle",
        "12-dongle-magnet",
        "13-dongle-steel-disc",
        "14-brainwavz-cushion",
        "15-existing-pop-mesh",
        "16-main-foam",
    )
    ref_colors = (
        cq.Color(0.65, 0.65, 0.70),
        cq.Color(0.03, 0.03, 0.03),
        cq.Color(0.90, 0.45, 0.05),
        cq.Color(0.65, 0.65, 0.70),
        cq.Color(0.25, 0.25, 0.28),
        cq.Color(0.25, 0.15, 0.55, 0.42),
        cq.Color(0.10, 0.10, 0.10, 0.50),
        cq.Color(0.15, 0.15, 0.15, 0.50),
    )
    for name, color, solid in zip(ref_names, ref_colors, refs):
        assembly.add(solid, name=name, color=color)
        cq.exporters.export(solid, str(output / f"{name}.step"))
    assembly.export(str(output / f"{filename_stem}-technical.step"))

    inlet_area = INLET_SIZE[0] * INLET_SIZE[1]
    exhaust_area = 2 * math.pi * (EXHAUST_DIAMETER / 2) ** 2
    print(f"OK: deux pieces valides, entree {inlet_area:.0f} mm2, sorties {exhaust_area:.0f} mm2")
    print(f"OK: paroi verticale fixee au fond, passage superieur {JOIN_Z - DIVIDER_TOP_Z:.1f} mm")
    print(f"OK: vis M3 par-dessous, ecrous captifs par-dessus, semelle laterale {2 * SOLE_VENT_WIDTH * SOLE_CLEARANCE:.0f} mm2")
    print(f"OK: plateau A1 mini {plate_box.xlen:.1f} x {plate_box.ylen:.1f} x {plate_box.zlen:.1f} mm")
    print(f"Exports: {output}")
    return upper, lower, air_path, divider, handle_foam, gasket, bolts, nuts, refs


if __name__ == "__main__":
    export()
