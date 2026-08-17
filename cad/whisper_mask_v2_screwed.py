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
# Quatre vis M3 traversent des trous lisses et serrent des ecrous captifs.
JOIN_Z = v1.SHOULDER_Z
M3_CLEARANCE_DIAMETER = 3.6
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
EXHAUST_X = 6.0
EXHAUST_Y = 3.8
HANDLE_BOTTOM_Y = HANDLE_OUTER_SECTIONS[0][3]
FOOT_DIAMETER = 5.0
FOOT_HEIGHT = 4.2
HANDLE_FOAM_THICKNESS = 12.7

# Paroi inclinee fixee au fond, sans coude. L'air passe au-dessus.
DIVIDER_BOTTOM = (-10.0, -103.0)
DIVIDER_TOP = (10.0, -12.0)
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
            cq.Workplane("XY", origin=(EXHAUST_X, HANDLE_BOTTOM_Y + y, -108.0))
            .circle(EXHAUST_DIAMETER / 2)
            .extrude(15.0)
        )
        ports = port if ports is None else ports.union(port)
    return ports


def build_divider():
    x0, z0 = DIVIDER_BOTTOM
    x1, z1 = DIVIDER_TOP
    dx, dz = x1 - x0, z1 - z0
    length = math.hypot(dx, dz)
    nx, nz = -dz / length, dx / length
    h = DIVIDER_THICKNESS / 2
    profile = (
        (x0 + nx * h, z0 + nz * h),
        (x1 + nx * h, z1 + nz * h),
        (x1 - nx * h, z1 - nz * h),
        (x0 - nx * h, z0 - nz * h),
    )
    return (
        cq.Workplane("XZ")
        .polyline(profile)
        .close()
        .extrude(45.0, both=True)
        .intersect(build_handle_outer())
    )


def build_feet():
    feet = None
    for x in (-16.0, 16.0):
        for y in (-9.0, 9.0):
            foot = (
                cq.Workplane("XY", origin=(x, HANDLE_BOTTOM_Y + y, -108.4))
                .circle(FOOT_DIAMETER / 2)
                .extrude(FOOT_HEIGHT)
            )
            feet = foot if feet is None else feet.union(foot)
    return feet


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


def build_nut_pockets():
    pockets = None
    for x, y in SCREW_POSITIONS:
        pocket = (
            cq.Workplane("XY", origin=(x, y, JOIN_Z - 3.0))
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
        .clean()
    )


def build_lower():
    flange = ellipse_ring(FLANGE_OUTER, FLANGE_INNER, JOIN_Z - 3.0, 3.0)
    return (
        build_handle_outer()
        .cut(build_handle_inner())
        .union(flange)
        .cut(build_exhaust_ports())
        .union(build_divider())
        .union(build_feet())
        .cut(build_screw_holes())
        .cut(build_nut_pockets())
        .clean()
    )


def build_gasket():
    return ellipse_ring(
        GASKET_OUTER,
        GASKET_INNER,
        JOIN_Z - GASKET_THICKNESS / 2,
        GASKET_THICKNESS,
    ).cut(build_screw_holes())


def build_handle_foam():
    # Deux bandes souples introduites par le dessus avant vissage.
    inner = build_handle_inner().cut(build_divider())
    left = (
        cq.Workplane("XY", origin=(-17.0, -14.0, -76.0))
        .box(HANDLE_FOAM_THICKNESS, 18.0, 54.0, centered=(True, True, False))
        .intersect(inner)
    )
    right = (
        cq.Workplane("XY", origin=(17.0, -14.0, -76.0))
        .box(HANDLE_FOAM_THICKNESS, 18.0, 54.0, centered=(True, True, False))
        .intersect(inner)
    )
    return left.union(right).clean()


def build_air_path():
    return (
        v1.build_inner_cavity()
        .union(build_inlet())
        .union(build_handle_inner())
        .union(build_exhaust_ports())
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
            .extrude(9.0)
            .union(
                cq.Workplane("XY", origin=(x, y, JOIN_Z + 3.0))
                .circle(2.8)
                .extrude(3.0)
            )
        )
        nut = (
            cq.Workplane("XY", origin=(x, y, JOIN_Z - 3.0))
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
    assert DIVIDER_TOP[1] <= -10.0, "Le passage au-dessus de la paroi est trop petit"
    assert build_exhaust_ports().intersect(build_feet()).val().Volume() < 1e-6


def export():
    upper = build_upper()
    lower = build_lower()
    air_path = build_air_path()
    divider = build_divider()
    handle_foam = build_handle_foam()
    gasket = build_gasket()
    bolts, nuts = build_fastener_references()
    refs = list(v1.build_references(upper))
    refs[-1] = refs[-1].cut(build_inlet())
    check(upper, lower, air_path, handle_foam)

    output = HERE / "out" / "v2-screwed"
    output.mkdir(parents=True, exist_ok=True)
    exports = {
        "upper": upper,
        "lower": lower,
        "air-path": air_path,
        "divider": divider,
        "handle-foam": handle_foam,
        "gasket": gasket,
    }
    for name, solid in exports.items():
        cq.exporters.export(solid, str(output / f"whisper-mask-v2-screwed-{name}.step"))
    cq.exporters.export(bolts, str(output / "07-m3-bolts-reference.step"))
    cq.exporters.export(nuts, str(output / "08-m3-nuts-reference.step"))
    cq.exporters.export(upper, str(output / "whisper-mask-v2-screwed-upper.stl"))
    cq.exporters.export(lower, str(output / "whisper-mask-v2-screwed-lower.stl"))

    print_plate = cq.Compound.makeCompound(
        [
            upper.translate((0, -40.0, -JOIN_Z)).val(),
            lower.translate((0, 45.0, 108.4)).val(),
        ]
    )
    plate_box = print_plate.BoundingBox()
    assert plate_box.xlen <= 180.0 and plate_box.ylen <= 180.0
    assert plate_box.zlen <= 180.0
    cq.exporters.export(
        cq.Workplane("XY").newObject([print_plate]),
        str(output / "whisper-mask-v2-screwed-print-plate.stl"),
    )

    assembly = cq.Assembly(name="whisper-mask-v2-screwed-technical")
    assembly.add(upper, name="01-printed-upper", color=cq.Color(0.78, 0.78, 0.80, 0.35))
    assembly.add(lower, name="02-printed-lower", color=cq.Color(0.72, 0.75, 0.80, 0.35))
    assembly.add(divider, name="03-inclined-bottom-baffle", color=cq.Color(0.85, 0.20, 0.12))
    assembly.add(air_path, name="04-continuous-air-path", color=cq.Color(0.10, 0.70, 0.95, 0.28))
    assembly.add(handle_foam, name="05-removable-handle-foam", color=cq.Color(0.20, 0.60, 0.25, 0.60))
    assembly.add(gasket, name="06-1mm-gasket", color=cq.Color(0.95, 0.80, 0.10, 0.75))
    assembly.add(bolts, name="07-m3-bolts-reference", color=cq.Color(0.55, 0.58, 0.62))
    assembly.add(nuts, name="08-m3-nuts-reference", color=cq.Color(0.45, 0.48, 0.52))
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
    assembly.export(str(output / "whisper-mask-v2-screwed-technical.step"))

    inlet_area = INLET_SIZE[0] * INLET_SIZE[1]
    exhaust_area = 2 * math.pi * (EXHAUST_DIAMETER / 2) ** 2
    print(f"OK: deux pieces valides, entree {inlet_area:.0f} mm2, sorties {exhaust_area:.0f} mm2")
    print(f"OK: paroi fixee au fond, passage superieur {JOIN_Z - DIVIDER_TOP[1]:.1f} mm")
    print(f"OK: plateau A1 mini {plate_box.xlen:.1f} x {plate_box.ylen:.1f} x {plate_box.zlen:.1f} mm")
    print(f"Exports: {output}")
    return upper, lower, air_path, divider, handle_foam, gasket, bolts, nuts, refs


if __name__ == "__main__":
    export()
