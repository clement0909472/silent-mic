# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright 2026 Clement Barberousse

import math

import whisper_mask_v2_screwed as model


# Variante ergonomique: manche plus court, un peu plus large et davantage coude.
HANDLE_OUTER_SECTIONS = (
    (46.0, 35.0, -84.0, -42.0),
    (50.0, 38.0, -78.0, -39.0),
    (54.0, 41.0, -60.0, -31.0),
    (61.0, 46.0, -36.0, -19.0),
    (67.0, 50.0, -12.0, -6.0),
    (69.0, 52.0, 0.0, -2.0),
    (72.0, 54.0, model.JOIN_Z, 0.0),
)
HANDLE_INNER_SECTIONS = (
    (38.0, 27.0, -76.0, -39.5),
    (42.0, 30.0, -70.0, -36.5),
    (46.0, 33.0, -56.0, -29.5),
    (53.0, 38.0, -33.0, -18.0),
    (59.0, 43.0, -10.0, -5.0),
    (60.0, 44.0, model.JOIN_Z, 0.0),
)


def configure():
    model.HANDLE_OUTER_SECTIONS = HANDLE_OUTER_SECTIONS
    model.HANDLE_INNER_SECTIONS = HANDLE_INNER_SECTIONS
    model.INLET_CENTER = (-18.0, -8.0, 3.25)
    model.INLET_SIZE = (16.0, 10.0, 26.5)
    model.HANDLE_BOTTOM_Y = HANDLE_OUTER_SECTIONS[0][3]
    model.HANDLE_BOTTOM_Z = HANDLE_OUTER_SECTIONS[0][2]
    model.EXHAUST_ORIGIN_Z = model.HANDLE_BOTTOM_Z - 3.0
    model.SOLE_BASE_Z = model.HANDLE_BOTTOM_Z - model.SOLE_CLEARANCE
    model.LOWER_PRINT_LIFT = -model.SOLE_BASE_Z
    # Disposition diagonale sans collision sur le plateau 180 x 180 mm.
    model.PRINT_UPPER_XY = (-22.6, 30.9)
    model.PRINT_LOWER_XY = (37.4, -43.1)
    model.PRINT_LOWER_ROTATION = 155.0
    model.HANDLE_FOAM_CENTER_Y = -24.0
    model.HANDLE_FOAM_DEPTH = 36.0
    model.HANDLE_FOAM_BOTTOM_Z = -69.0
    model.HANDLE_FOAM_HEIGHT = 51.0
    model.DIVIDER_BOTTOM_Z = -82.0
    model.DIVIDER_TOP_Z = -10.0


def main():
    configure()
    height = model.JOIN_Z - model.HANDLE_BOTTOM_Z
    angle = math.degrees(math.atan2(abs(model.HANDLE_BOTTOM_Y), height))
    assert 85.0 <= height <= 95.0
    assert 23.0 <= angle <= 27.0
    assert model.INLET_CENTER[2] - model.INLET_SIZE[2] / 2 == model.DIVIDER_TOP_Z
    result = model.export(
        output_subdir="v2-compact",
        filename_stem="whisper-mask-v2-compact",
    )
    viewer = globals().get("show_object")
    if viewer:
        upper, lower, air_path, divider, handle_foam, gasket, _, _, refs = result
        viewer(upper, name="Coque haute", options={"alpha": 0.25, "color": (142, 173, 209)})
        viewer(lower, name="Manche + semelle", options={"alpha": 0.25, "color": (110, 145, 189)})
        viewer(divider, name="Paroi verticale", options={"color": (235, 76, 31)})
        viewer(air_path, name="Passage d'air", options={"alpha": 0.35, "color": (25, 199, 245)})
        viewer(handle_foam, name="Mousse du manche", options={"alpha": 0.65, "color": (56, 171, 77)})
        viewer(gasket, name="Joint", options={"alpha": 0.75, "color": (245, 199, 26)})
        for name, ref in zip(
            ("Disque micro", "DJI Mic Mini 2", "Dongle USB-C", "Aimant dongle", "Disque dongle", "Coussinet", "Membrane", "Mousse principale"),
            refs,
        ):
            viewer(ref, name=name, options={"alpha": 0.65})
    print(f"OK: manche compact {height:.1f} mm, inclinaison {angle:.1f} degres")


if __name__ == "__main__" or "show_object" in globals():
    main()
