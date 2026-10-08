"""Save a color-coded technical view without opening a FreeCAD window."""

from pathlib import Path
import copy
import os
import struct
import sys
import tempfile
import uuid
import xml.etree.ElementTree as ET
import zipfile

SOURCE = Path(sys.argv[-2]).resolve()
TARGET = Path(sys.argv[-1]).resolve()

# label: (shape color, transparency, line color)
STYLE = {
    "Printed upper": ((0.56, 0.68, 0.82), 75, (0.08, 0.12, 0.18)),
    "Printed lower": ((0.43, 0.57, 0.74), 75, (0.08, 0.12, 0.18)),
    "Vertical baffle": ((0.92, 0.30, 0.12), 0, (0.30, 0.06, 0.02)),
    "Continuous air path": ((0.10, 0.78, 0.96), 68, (0.02, 0.35, 0.52)),
    "Handle foam left": ((0.22, 0.67, 0.30), 22, (0.04, 0.25, 0.08)),
    "Handle foam right": ((0.22, 0.67, 0.30), 22, (0.04, 0.25, 0.08)),
    "Joint gasket": ((0.96, 0.78, 0.10), 10, (0.38, 0.25, 0.02)),
    "Hidden M3 screws": ((0.64, 0.68, 0.73), 0, (0.18, 0.20, 0.23)),
    "Captive M3 nuts": ((0.48, 0.52, 0.58), 0, (0.16, 0.18, 0.21)),
    "Mic steel disc": ((0.76, 0.78, 0.82), 0, (0.22, 0.24, 0.28)),
    "DJI Mic Mini 2": ((0.05, 0.06, 0.08), 0, (0.75, 0.78, 0.82)),
    "DJI USB-C dongle": ((0.94, 0.48, 0.08), 0, (0.35, 0.12, 0.02)),
    "Dongle magnet": ((0.86, 0.12, 0.16), 0, (0.30, 0.02, 0.04)),
    "Dongle steel disc": ((0.58, 0.61, 0.66), 0, (0.18, 0.20, 0.24)),
    "Brainwavz cushion": ((0.42, 0.25, 0.70), 38, (0.15, 0.06, 0.28)),
    "Pop mesh": ((0.12, 0.14, 0.18), 52, (0.70, 0.72, 0.76)),
    "Main foam": ((0.18, 0.55, 0.24), 28, (0.04, 0.22, 0.07)),
}
HIDDEN_BY_DEFAULT = {"Hidden M3 screws", "Captive M3 nuts"}


def color_bytes(rgb):
    return bytes([255, *(round(channel * 255) for channel in rgb)])


def property_color(rgb):
    red, green, blue = (round(channel * 255) for channel in rgb)
    return str((red << 24) | (green << 16) | (blue << 8))


def material_blob(rgb, transparency):
    ambient = tuple(channel * 0.45 for channel in rgb)
    material_uuid = str(uuid.uuid4()).encode("ascii")
    return b"".join(
        (
            struct.pack("<I", 1),
            color_bytes(ambient),
            color_bytes(rgb),
            color_bytes((0.50, 0.50, 0.50)),
            color_bytes((0.0, 0.0, 0.0)),
            struct.pack("<ff", 0.90, transparency / 100.0),
            struct.pack("<I", 0),
            struct.pack("<I", 0),
            struct.pack("<I", len(material_uuid)),
            material_uuid,
        )
    )


def set_property(view_provider, name, child_tag, attribute, value):
    prop = view_provider.find(f"./Properties/Property[@name='{name}']")
    if prop is None:
        raise RuntimeError(f"Missing view property {name}")
    child = prop.find(child_tag)
    if child is None:
        raise RuntimeError(f"Missing {child_tag} for {name}")
    child.set(attribute, str(value))


def add_gui_data(entries, object_names):
    if "GuiDocument.xml" in entries:
        return

    template = SOURCE.with_name("silent-mic-v2-technical-ready.FCStd")
    if not template.exists():
        template = SOURCE.parent.parent / "v2-screwed" / template.name
    with zipfile.ZipFile(template, "r") as archive:
        for info in archive.infolist():
            if info.filename == "GuiDocument.xml" or info.filename.startswith(
                ("LineColorArray", "PointColorArray", "ShapeAppearance", "thumbnails/")
            ):
                entries[info.filename] = (info, archive.read(info.filename))

    root = ET.fromstring(entries["GuiDocument.xml"][1])
    provider_data = root.find("./ViewProviderData")
    providers = {provider.get("name"): provider for provider in provider_data}
    prototype = next(iter(providers.values()))
    for name in object_names:
        if name in providers:
            continue
        provider = copy.deepcopy(prototype)
        provider.set("name", name)
        suffix = str(len(providers))
        for child in provider.findall(".//*[@file]"):
            old_name = child.get("file")
            prefix = old_name.rstrip("0123456789")
            new_name = f"{prefix}{suffix}"
            old_info, data = entries[old_name]
            new_info = copy.copy(old_info)
            new_info.filename = new_name
            entries[new_name] = (new_info, data)
            child.set("file", new_name)
        provider_data.append(provider)
        providers[name] = provider
    provider_data.set("Count", str(len(object_names)))
    ET.indent(root, space="    ")
    info, _ = entries["GuiDocument.xml"]
    entries["GuiDocument.xml"] = (
        info,
        ET.tostring(root, encoding="utf-8", xml_declaration=True),
    )


def main():
    with zipfile.ZipFile(SOURCE, "r") as archive:
        entries = {info.filename: (info, archive.read(info.filename)) for info in archive.infolist()}

    document_root = ET.fromstring(entries["Document.xml"][1])
    labels = {}
    for obj in document_root.findall("./ObjectData/Object"):
        label = obj.find("./Properties/Property[@name='Label']/String")
        if label is not None:
            labels[obj.get("name")] = label.get("value")

    add_gui_data(entries, labels)
    gui_root = ET.fromstring(entries["GuiDocument.xml"][1])
    styled = set()
    for view_provider in gui_root.findall("./ViewProviderData/ViewProvider"):
        label = labels.get(view_provider.get("name"))
        if label not in STYLE:
            continue
        shape_color, transparency, line_color = STYLE[label]
        set_property(view_provider, "Transparency", "Integer", "value", transparency)
        set_property(view_provider, "LineColor", "PropertyColor", "value", property_color(line_color))
        set_property(view_provider, "PointColor", "PropertyColor", "value", property_color(line_color))
        set_property(view_provider, "LineWidth", "Float", "value", "1.5")
        if label in HIDDEN_BY_DEFAULT:
            set_property(view_provider, "Visibility", "Bool", "value", "false")

        material = view_provider.find("./Properties/Property[@name='ShapeAppearance']/MaterialList")
        if material is None:
            raise RuntimeError(f"Missing ShapeAppearance for {label}")
        material_file = material.get("file")
        info, _ = entries[material_file]
        entries[material_file] = (info, material_blob(shape_color, transparency))
        styled.add(label)

    missing = set(STYLE) - styled
    if missing:
        raise RuntimeError(f"Missing objects: {', '.join(sorted(missing))}")

    ET.indent(gui_root, space="    ")
    gui_xml = ET.tostring(gui_root, encoding="utf-8", xml_declaration=True)
    gui_info, _ = entries["GuiDocument.xml"]
    entries["GuiDocument.xml"] = (gui_info, gui_xml)

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=TARGET.parent, suffix=".FCStd", delete=False) as temp:
        temp_path = Path(temp.name)
    try:
        with zipfile.ZipFile(temp_path, "w") as archive:
            for info, data in entries.values():
                archive.writestr(info, data)
        os.replace(temp_path, TARGET)
    finally:
        temp_path.unlink(missing_ok=True)

    print(f"Saved {TARGET}")


if __name__ == "__main__":
    main()
