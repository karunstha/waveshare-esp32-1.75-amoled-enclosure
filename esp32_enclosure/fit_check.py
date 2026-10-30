"""Simplified, viewport-only ESP32 hardware for visual fit checks."""

from __future__ import annotations

import bpy

from . import config as cfg
from .mesh import make_dummy_material
from .primitives import add_box, add_y_cylinder


def build_dummy_esp32(front_y: float) -> list:
    """Create a simplified, viewport-only ESP32 fit-check assembly."""
    if not cfg.ENABLE_DUMMY_ESP32:
        return []

    collection_name = "FIT_CHECK_DUMMY_ESP32"
    collection = bpy.data.collections.get(collection_name)
    if collection is None:
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)

    glass_material = make_dummy_material(
        "Dummy_Display_Glass_Material", (0.04, 0.20, 0.28, 1.0)
    )
    pcb_material = make_dummy_material(
        "Dummy_PCB_Material", (0.02, 0.38, 0.12, 1.0)
    )
    keepout_material = make_dummy_material(
        "Dummy_Component_Keepout_Material", (0.95, 0.30, 0.05, 1.0)
    )
    connector_material = make_dummy_material(
        "Dummy_Connector_Material", (0.45, 0.48, 0.52, 1.0)
    )

    objects = []

    def register(obj, material, wire: bool = False):
        for source_collection in list(obj.users_collection):
            source_collection.objects.unlink(obj)
        collection.objects.link(obj)
        obj.data.materials.append(material)
        obj.hide_render = True
        obj.show_in_front = True
        obj.display_type = "WIRE" if wire else "SOLID"
        obj["fit_check_only"] = True
        obj["exclude_from_stl"] = True
        objects.append(obj)
        return obj

    glass = add_y_cylinder(
        "Dummy_Display_Glass_48_96mm",
        cfg.DISPLAY_OUTER_DIAMETER,
        cfg.DISPLAY_RECESS_DEPTH,
        location=(0.0, front_y + cfg.DISPLAY_RECESS_DEPTH / 2.0, 0.0),
    )
    register(glass, glass_material)

    carrier = add_box(
        "Dummy_Display_Carrier_STEP_Envelope",
        (cfg.DUMMY_CARRIER_WIDTH, cfg.DUMMY_CARRIER_DEPTH, cfg.DUMMY_CARRIER_HEIGHT),
        location=(
            cfg.DUMMY_CARRIER_CENTRE_X,
            front_y
            + cfg.DUMMY_CARRIER_FRONT_FROM_DISPLAY
            + cfg.DUMMY_CARRIER_DEPTH / 2.0,
            0.0,
        ),
    )
    register(carrier, keepout_material, wire=True)

    pcb_y = (
        front_y
        + cfg.DUMMY_PCB_FRONT_FROM_DISPLAY
        + cfg.DUMMY_PCB_THICKNESS / 2.0
    )
    pcb = add_y_cylinder(
        "Dummy_Circular_PCB_46mm",
        cfg.BOARD_OUTER_DIAMETER,
        cfg.DUMMY_PCB_THICKNESS,
        location=(0.0, pcb_y, 0.0),
    )
    register(pcb, pcb_material)

    usb = add_box(
        "Dummy_USB_C_Receptacle",
        (cfg.USB_C_RECEPTACLE_WIDTH, cfg.USB_C_RECEPTACLE_DEPTH, cfg.DUMMY_USB_C_HEIGHT),
        location=(
            cfg.DUMMY_USB_C_CENTRE_X,
            front_y + cfg.DUMMY_USB_C_CENTRE_FROM_FRONT,
            cfg.DUMMY_USB_C_CENTRE_Z,
        ),
    )
    register(usb, connector_material)

    for name, x, depth_from_front, z, width, depth, height in (
        cfg.DUMMY_MAJOR_COMPONENT_BOXES
    ):
        component = add_box(
            f"Dummy_{name}_STEP_Envelope",
            (width, depth, height),
            location=(
                x,
                front_y + depth_from_front,
                z,
            ),
        )
        register(component, connector_material)

    boss_y = (
        front_y
        + cfg.DUMMY_SCREW_BOSS_FRONT_FROM_DISPLAY
        + cfg.DUMMY_SCREW_BOSS_DEPTH / 2.0
    )
    for index, (drawing_x, z) in enumerate(cfg.SCREW_CENTRES, 1):
        boss = add_y_cylinder(
            f"Dummy_M2_Boss_{index}",
            cfg.DUMMY_SCREW_BOSS_DIAMETER,
            cfg.DUMMY_SCREW_BOSS_DEPTH,
            location=(-drawing_x, boss_y, z),
            vertices=cfg.VENT_CYLINDER_VERTICES,
        )
        register(boss, connector_material)

    return objects
