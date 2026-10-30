"""Main shell construction.

Each ``_cut_*`` helper performs a group of Boolean operations on the shell. The
order in which they run matters (later cuts and unions see earlier results), so
``build_enclosure`` keeps the original sequence.
"""

from __future__ import annotations

import bpy

from . import config as cfg
from .accessory import build_back_accessory_layer
from .display import cut_display_cable_reliefs
from .fit_check import build_dummy_esp32
from .mesh import clean_mesh, make_material
from .patterns import staggered_lattice_offsets
from .primitives import (
    add_box,
    add_x_cylinder,
    add_y_cylinder,
    add_y_ellipse,
    add_z_cylinder,
    apply_bevel,
    clear_scene,
    set_units,
    subtract,
    subtract_many,
    subtract_z_capsule,
    unite,
)
from .validation import validate_parameters


def _cut_display_seat(enclosure, front_y: float) -> None:
    """Add the stepped display cup and open the pocket and PCB passage."""


    # Form a concentric recessed cup directly from the front opening. A thin
    # circular sleeve runs inward from the surface and terminates in an annular
    # support ring. The display OD follows the sleeve; the smaller PCB passes
    # through the ring, leaving a flat circular shoulder at exactly 2.05 mm.
    support_outer_diameter = (
        cfg.DISPLAY_POCKET_DIAMETER + 2 * cfg.DISPLAY_SUPPORT_WALL_THICKNESS
    )
    support_outer_vertical_diameter = (
        support_outer_diameter + 2 * cfg.DISPLAY_VERTICAL_RADIUS_COMPENSATION
    )
    # The sleeve starts inside the front wall, not on its outer face: a
    # coplanar front face makes the union non-manifold. The final pocket cut
    # below opens the front surface.
    sleeve_start_y = front_y + cfg.FRONT_WALL / 2.0
    sleeve_end_y = front_y + cfg.DISPLAY_RECESS_DEPTH + cfg.DISPLAY_PLATFORM_THICKNESS
    sleeve_depth = sleeve_end_y - sleeve_start_y
    sleeve_y = (sleeve_start_y + sleeve_end_y) / 2.0
    sleeve = add_y_ellipse(
        "Display_Recess_Sleeve",
        support_outer_diameter,
        support_outer_vertical_diameter,
        sleeve_depth,
        location=(0.0, sleeve_y, 0.0),
    )
    sleeve_void = add_y_ellipse(
        "Display_Recess_Interior",
        cfg.DISPLAY_POCKET_DIAMETER,
        cfg.DISPLAY_POCKET_VERTICAL_DIAMETER,
        sleeve_depth + 2 * cfg.BOOLEAN_MARGIN,
        location=(0.0, sleeve_y, 0.0),
    )
    subtract(sleeve, sleeve_void)
    cut_display_cable_reliefs(
        sleeve,
        "Sleeve",
        sleeve_y,
        sleeve_depth + 2 * cfg.BOOLEAN_MARGIN,
        support_outer_diameter,
        cfg.BOARD_OPENING_DIAMETER,
        cfg.DISPLAY_VERTICAL_RADIUS_COMPENSATION,
    )

    platform_front_y = front_y + cfg.DISPLAY_RECESS_DEPTH
    platform_y = platform_front_y + cfg.DISPLAY_PLATFORM_THICKNESS / 2.0
    platform = add_y_ellipse(
        "Display_Annular_Support",
        support_outer_diameter,
        support_outer_vertical_diameter,
        cfg.DISPLAY_PLATFORM_THICKNESS,
        location=(0.0, platform_y, 0.0),
    )
    board_cutter = add_y_ellipse(
        "PCB_Opening_In_Platform",
        cfg.BOARD_OPENING_DIAMETER,
        cfg.BOARD_OPENING_VERTICAL_DIAMETER,
        cfg.DISPLAY_PLATFORM_THICKNESS + 2 * cfg.BOOLEAN_MARGIN,
        location=(0.0, platform_y, 0.0),
    )
    subtract(platform, board_cutter)
    cut_display_cable_reliefs(
        platform,
        "Support",
        platform_y,
        cfg.DISPLAY_PLATFORM_THICKNESS + 2 * cfg.BOOLEAN_MARGIN,
        support_outer_diameter,
        cfg.BOARD_OPENING_DIAMETER,
        cfg.DISPLAY_VERTICAL_RADIUS_COMPENSATION,
    )
    # Build one watertight display cup before touching the complex enclosure
    # mesh. This prevents slicers from dropping the ring as a separate shell.
    unite(sleeve, platform)
    unite(enclosure, sleeve)

    # Re-cut the two concentric passages after every display-support union.
    # Boolean unions can otherwise leave an internal cap that mesh-repairing
    # slicers interpret as a solid top skin.
    pocket_cut_start = front_y - cfg.BOOLEAN_MARGIN
    pocket_cut_end = platform_front_y
    final_pocket_cutter = add_y_ellipse(
        "Final_Display_Pocket_Opening",
        cfg.DISPLAY_POCKET_DIAMETER,
        cfg.DISPLAY_POCKET_VERTICAL_DIAMETER,
        pocket_cut_end - pocket_cut_start,
        location=(0.0, (pocket_cut_start + pocket_cut_end) / 2.0, 0.0),
    )
    subtract(enclosure, final_pocket_cutter)

    final_board_cutter = add_y_ellipse(
        "Final_PCB_Through_Opening",
        cfg.BOARD_OPENING_DIAMETER,
        cfg.BOARD_OPENING_VERTICAL_DIAMETER,
        cfg.DISPLAY_PLATFORM_THICKNESS + 2 * cfg.BOOLEAN_MARGIN,
        location=(0.0, platform_y, 0.0),
    )
    subtract(enclosure, final_board_cutter)


def _cut_rear_features(enclosure, front_y: float, rear_y: float) -> None:
    """Cut the rear screw wells and the three connector openings."""
    # Rear screw holes.
    rear_cut_depth = cfg.REAR_WALL + 2 * cfg.BOOLEAN_MARGIN

    # Independent centered rear hole for accessing sacrificial print supports.
    # This is a separate boolean and does not alter any existing rear cutout.
    if cfg.ENABLE_REAR_SUPPORT_ACCESS_HOLE:
        support_access_cutter = add_y_cylinder(
            "Rear_Support_Access_Hole",
            cfg.REAR_SUPPORT_ACCESS_HOLE_DIAMETER,
            rear_cut_depth,
            location=(0.0, rear_y, 0.0),
        )
        subtract(enclosure, support_access_cutter)

    if cfg.ENABLE_RECESSED_SCREW_WELLS:
        screw_mount_y = front_y + cfg.SCREW_MOUNT_DEPTH_FROM_FRONT
        screw_cup_front_y = screw_mount_y + cfg.SCREW_WELL_DEPTH_REDUCTION
        screw_cup_depth = rear_y - screw_cup_front_y
        screw_cup_y = (rear_y + screw_cup_front_y) / 2.0
        screw_cup_outer_diameter = (
            cfg.SCREW_WELL_INNER_DIAMETER + 2 * cfg.SCREW_WELL_WALL_THICKNESS
        )
        well_floor_rear_y = (
            screw_cup_front_y + cfg.SCREW_WELL_FLOOR_THICKNESS
        )
        well_cut_end_y = rear_y + cfg.BOOLEAN_MARGIN
        well_cut_depth = well_cut_end_y - well_floor_rear_y
        screw_cut_start_y = screw_mount_y - cfg.BOOLEAN_MARGIN
        screw_cut_end_y = rear_y + cfg.BOOLEAN_MARGIN

        for index, (drawing_x, z) in enumerate(cfg.SCREW_CENTRES, start=1):
            world_x = -drawing_x
            cup = add_y_cylinder(
                f"M2_Recessed_Cup_{index}",
                screw_cup_outer_diameter,
                screw_cup_depth,
                location=(world_x, screw_cup_y, z),
            )
            unite(enclosure, cup)

            well = add_y_cylinder(
                f"M2_Head_Recess_{index}",
                cfg.SCREW_WELL_INNER_DIAMETER,
                well_cut_depth,
                location=(
                    world_x,
                    (well_floor_rear_y + well_cut_end_y) / 2.0,
                    z,
                ),
            )
            subtract(enclosure, well)

            through_hole = add_y_cylinder(
                f"M2_Screw_Hole_{index}",
                cfg.SCREW_HOLE_DIAMETER,
                screw_cut_end_y - screw_cut_start_y,
                location=(
                    world_x,
                    (screw_cut_start_y + screw_cut_end_y) / 2.0,
                    z,
                ),
            )
            subtract(enclosure, through_hole)
    else:
        for index, (drawing_x, z) in enumerate(cfg.SCREW_CENTRES, start=1):
            cutter = add_y_cylinder(
                f"M2_Screw_Hole_{index}",
                cfg.SCREW_HOLE_DIAMETER,
                rear_cut_depth,
                # A rear view looks along -Y, so drawing-right is Blender -X.
                location=(-drawing_x, rear_y, z),
            )
            subtract(enclosure, cutter)

    # Rear rectangular access openings.
    for opening in cfg.REAR_RECTANGLES:
        cutter = add_box(
            opening.name,
            (opening.width, rear_cut_depth, opening.height),
            location=(-opening.x, rear_y, opening.z),
        )
        subtract(enclosure, cutter)


def _cut_usb_c(enclosure, front_y: float) -> float:
    """Cut the USB-C opening and tunnel; return its centre along Y."""
    # USB-C access through the bottom (-Z) side wall. The rounded guide tunnel
    # now reaches from the shell exterior to the edge-mounted receptacle.
    usb_y = front_y + cfg.USB_C_CENTRE_FROM_FRONT
    bottom_z = -cfg.CASE_HEIGHT / 2.0
    if cfg.ENABLE_USB_C_TUNNEL:
        tunnel_z = bottom_z + cfg.USB_C_TUNNEL_LENGTH / 2.0
        usb_inner_front_y = usb_y - cfg.USB_C_OPENING_DEPTH / 2.0
        usb_inner_rear_y = usb_y + cfg.USB_C_OPENING_DEPTH / 2.0
        tunnel_front_y = max(
            usb_inner_front_y - cfg.USB_C_TUNNEL_WALL,
            front_y,
        )
        tunnel_rear_y = usb_inner_rear_y + cfg.USB_C_TUNNEL_WALL
        tunnel_outer_depth = tunnel_rear_y - tunnel_front_y
        tunnel_outer_y = (tunnel_front_y + tunnel_rear_y) / 2.0
        tunnel = add_box(
            "USB_C_Guide_Tunnel",
            (
                cfg.USB_C_OPENING_WIDTH + 2 * cfg.USB_C_TUNNEL_WALL,
                tunnel_outer_depth,
                cfg.USB_C_TUNNEL_LENGTH,
            ),
            location=(0.0, tunnel_outer_y, tunnel_z),
        )
        subtract_z_capsule(
            tunnel,
            "USB_C_Tunnel_Interior",
            cfg.USB_C_OPENING_WIDTH,
            cfg.USB_C_OPENING_DEPTH,
            cfg.USB_C_TUNNEL_LENGTH + 2 * cfg.BOOLEAN_MARGIN,
            location=(0.0, usb_y, tunnel_z),
        )
        unite(enclosure, tunnel)
        usb_cut_height = cfg.USB_C_TUNNEL_LENGTH + 2 * cfg.BOOLEAN_MARGIN
        usb_cut_z = tunnel_z
        subtract_z_capsule(
            enclosure,
            "USB_C_Tunnel_Clearance",
            cfg.USB_C_OPENING_WIDTH,
            cfg.USB_C_OPENING_DEPTH,
            usb_cut_height,
            location=(0.0, usb_y, usb_cut_z),
        )
    else:
        usb_cut_height = cfg.SIDE_WALL + 2 * cfg.BOOLEAN_MARGIN
        usb_cut_z = bottom_z
        subtract_z_capsule(
            enclosure,
            "USB_C_Accurate_Cutout",
            cfg.USB_C_OPENING_WIDTH,
            cfg.USB_C_OPENING_DEPTH,
            usb_cut_height,
            location=(0.0, usb_y, usb_cut_z),
        )

    return usb_y


def _cut_base_vents(enclosure, front_y: float) -> None:
    """Cut staggered airflow lattices through the side and top walls."""
    # Mac-Pro-inspired staggered circular lattices through the two side walls
    # and top wall. Each panel is centered and retains a clean solid border.
    if cfg.ENABLE_BASE_AIR_VENTS:
        airflow_cutters = []
        main_side_vent_y = (
            front_y + cfg.CASE_DEPTH * cfg.BASE_SIDE_VENT_MAIN_DEPTH_FRACTION
        )
        for side_label, x in (("Left", -cfg.CASE_WIDTH / 2.0),
                              ("Right", cfg.CASE_WIDTH / 2.0)):
            for index, (y_offset, z_offset) in enumerate(
                staggered_lattice_offsets(
                    cfg.BASE_SIDE_VENT_COLUMNS,
                    cfg.BASE_SIDE_VENT_ROWS,
                    cfg.BASE_AIR_VENT_PITCH,
                )
            ):
                airflow_cutters.append(
                    add_x_cylinder(
                        f"Base_{side_label}_Air_Vent_{index}",
                        cfg.BASE_AIR_VENT_DIAMETER,
                        cfg.SIDE_WALL + 2 * cfg.BOOLEAN_MARGIN,
                        location=(x, main_side_vent_y + y_offset, z_offset),
                        vertices=cfg.VENT_CYLINDER_VERTICES,
                    )
                )

        for index, (x_offset, y_offset) in enumerate(
            staggered_lattice_offsets(
                cfg.BASE_TOP_VENT_COLUMNS,
                cfg.BASE_TOP_VENT_ROWS,
                cfg.BASE_AIR_VENT_PITCH,
            )
        ):
            airflow_cutters.append(
                add_z_cylinder(
                    f"Base_Top_Air_Vent_{index}",
                    cfg.BASE_AIR_VENT_DIAMETER,
                    cfg.SIDE_WALL + 2 * cfg.BOOLEAN_MARGIN,
                    location=(x_offset, y_offset, cfg.CASE_HEIGHT / 2.0),
                    vertices=cfg.VENT_CYLINDER_VERTICES,
                )
            )
        subtract_many(enclosure, airflow_cutters, "Base_Airflow_Vent_Pattern")


def _cut_base_mic_ports(enclosure, usb_y: float) -> None:
    """Cut the two microphone ports flanking USB-C."""
    bottom_z = -cfg.CASE_HEIGHT / 2.0
    # The two actual microphone ports through the base bottom, one immediately
    # on each side of USB-C at the same front-to-rear position.
    if cfg.ENABLE_BASE_MIC_PORTS:
        for index, mic_x in enumerate(cfg.BASE_MIC_CENTRES_X, start=1):
            mic_port = add_z_cylinder(
                f"Base_Microphone_Hole_{index}",
                cfg.BASE_MIC_PORT_DIAMETER,
                cfg.SIDE_WALL + 2 * cfg.BOOLEAN_MARGIN,
                location=(mic_x, usb_y, bottom_z),
            )
            subtract(enclosure, mic_port)


def _annotate_enclosure(enclosure, dummy_objects) -> None:
    """Record the key dimensions and switches as custom properties."""
    enclosure["dimensions_mm"] = f"{cfg.CASE_WIDTH} x {cfg.CASE_HEIGHT} x {cfg.CASE_DEPTH}"
    enclosure["display_pocket_diameter_mm"] = cfg.DISPLAY_POCKET_DIAMETER
    enclosure["display_pocket_vertical_diameter_mm"] = (
        cfg.DISPLAY_POCKET_VERTICAL_DIAMETER
    )
    enclosure["board_opening_diameter_mm"] = cfg.BOARD_OPENING_DIAMETER
    enclosure["board_opening_vertical_diameter_mm"] = (
        cfg.BOARD_OPENING_VERTICAL_DIAMETER
    )
    enclosure["display_vertical_radius_compensation_mm"] = (
        cfg.DISPLAY_VERTICAL_RADIUS_COMPENSATION
    )
    enclosure["display_recess_depth_mm"] = cfg.DISPLAY_RECESS_DEPTH
    enclosure["display_platform_thickness_mm"] = cfg.DISPLAY_PLATFORM_THICKNESS
    enclosure["display_support_wall_thickness_mm"] = (
        cfg.DISPLAY_SUPPORT_WALL_THICKNESS
    )
    enclosure["display_cable_reliefs_enabled"] = cfg.ENABLE_DISPLAY_CABLE_RELIEFS
    if cfg.ENABLE_DISPLAY_CABLE_RELIEFS:
        enclosure["display_cable_relief_width_mm"] = cfg.DISPLAY_CABLE_RELIEF_WIDTH
    enclosure["shell_thickness_mm"] = cfg.ENCLOSURE_THICKNESS
    enclosure["usb_c_opening_mm"] = (
        f"{cfg.USB_C_OPENING_WIDTH} x {cfg.USB_C_OPENING_DEPTH}"
    )
    enclosure["usb_c_tunnel_enabled"] = cfg.ENABLE_USB_C_TUNNEL
    enclosure["rear_support_access_hole_enabled"] = (
        cfg.ENABLE_REAR_SUPPORT_ACCESS_HOLE
    )
    if cfg.ENABLE_REAR_SUPPORT_ACCESS_HOLE:
        enclosure["rear_support_access_hole_diameter_mm"] = (
            cfg.REAR_SUPPORT_ACCESS_HOLE_DIAMETER
        )
    enclosure["recessed_screw_wells_enabled"] = cfg.ENABLE_RECESSED_SCREW_WELLS
    if cfg.ENABLE_RECESSED_SCREW_WELLS:
        enclosure["screw_bump_depth_reduction_mm"] = (
            cfg.SCREW_WELL_DEPTH_REDUCTION
        )
        enclosure["screw_bump_inward_projection_mm"] = (
            cfg.CASE_DEPTH
            - cfg.REAR_WALL
            - cfg.SCREW_MOUNT_DEPTH_FROM_FRONT
            - cfg.SCREW_WELL_DEPTH_REDUCTION
        )
        enclosure["screw_mount_gap_mm"] = (
            cfg.CASE_DEPTH - cfg.REAR_WALL - cfg.SCREW_MOUNT_DEPTH_FROM_FRONT
        )
        enclosure["screw_head_recess_depth_mm"] = (
            cfg.CASE_DEPTH
            - cfg.SCREW_MOUNT_DEPTH_FROM_FRONT
            - cfg.SCREW_WELL_DEPTH_REDUCTION
            - cfg.SCREW_WELL_FLOOR_THICKNESS
        )
    if cfg.ENABLE_USB_C_TUNNEL:
        enclosure["usb_c_tunnel_mm"] = (
            f"length {cfg.USB_C_TUNNEL_LENGTH}, wall {cfg.USB_C_TUNNEL_WALL}"
        )
    enclosure["back_accessory_layer_enabled"] = cfg.ENABLE_BACK_ACCESSORY_LAYER
    enclosure["dummy_esp32_enabled"] = cfg.ENABLE_DUMMY_ESP32
    enclosure["dummy_esp32_object_count"] = len(dummy_objects)
    enclosure["rear_cover_mechanism"] = (
        "Flush internal top-and-bottom two-clip snap fit"
    )
    enclosure["outer_faces_planar"] = True
    enclosure["gps_middle_panel_opening_enabled"] = (
        cfg.ENABLE_GPS_MIDDLE_PANEL_OPENING
    )
    enclosure["base_air_vents_enabled"] = cfg.ENABLE_BASE_AIR_VENTS
    enclosure["accessory_side_air_vents_enabled"] = (
        cfg.ENABLE_ACCESSORY_SIDE_AIR_VENTS
    )
    enclosure["base_mic_ports_enabled"] = cfg.ENABLE_BASE_MIC_PORTS
    enclosure["accessory_bottom_mic_vents_enabled"] = (
        cfg.ENABLE_ACCESSORY_BOTTOM_MIC_VENTS
    )
    if cfg.ENABLE_BACK_ACCESSORY_LAYER:
        enclosure["accessory_internal_depth_mm"] = cfg.ACCESSORY_INTERNAL_DEPTH
        enclosure["accessory_depth_reduction_mm"] = cfg.ACCESSORY_DEPTH_REDUCTION
        enclosure["accessory_layout"] = "Battery left; GPS upper-right; speaker lower-right"
    enclosure["notes"] = "Mic centres are drawing-scaled estimates; test fit."


def build_enclosure():
    """Build the main shell and separate cover; return both Blender objects.

    The fit-check collection is created for viewport inspection and never
    passed to the STL exporter.
    """
    # Always start from a completely empty Blender scene.
    clear_scene()
    validate_parameters()
    set_units()

    # Begin with a square envelope; the optional bevel is currently disabled.
    enclosure = add_box(
        "ESP32_Display_Enclosure",
        (cfg.CASE_WIDTH, cfg.CASE_DEPTH, cfg.CASE_HEIGHT),
    )
    if cfg.OUTER_CORNER_RADIUS > 0:
        apply_bevel(enclosure, cfg.OUTER_CORNER_RADIUS, segments=6)

    # Hollow the envelope. Matching the inner corner radius to the outer one
    # keeps the selected wall thickness continuous around rounded corners.
    cavity_depth = cfg.CASE_DEPTH - cfg.FRONT_WALL - cfg.REAR_WALL
    cavity_y = (cfg.FRONT_WALL - cfg.REAR_WALL) / 2.0
    cavity = add_box(
        "Internal_Cavity",
        (
            cfg.CASE_WIDTH - 2 * cfg.SIDE_WALL,
            cavity_depth,
            cfg.CASE_HEIGHT - 2 * cfg.SIDE_WALL,
        ),
        location=(0.0, cavity_y, 0.0),
    )
    inner_corner_radius = max(cfg.OUTER_CORNER_RADIUS - cfg.SIDE_WALL, 0.0)
    if inner_corner_radius > 0:
        apply_bevel(cavity, inner_corner_radius, segments=6)
    subtract(enclosure, cavity)

    front_y = -cfg.CASE_DEPTH / 2.0
    _cut_display_seat(enclosure, front_y)

    rear_y = cfg.CASE_DEPTH / 2.0
    _cut_rear_features(enclosure, front_y, rear_y)
    usb_y = _cut_usb_c(enclosure, front_y)
    _cut_base_vents(enclosure, front_y)
    _cut_base_mic_ports(enclosure, usb_y)

    cover = build_back_accessory_layer(enclosure, rear_y)
    dummy_objects = build_dummy_esp32(front_y)

    # Optional cut-edge softening. Leave this at zero for a full-width, flat
    # display seating shoulder; external case corners were already rounded.
    if cfg.EDGE_BEVEL > 0:
        apply_bevel(enclosure, cfg.EDGE_BEVEL, segments=2)
    clean_mesh(enclosure)
    if cover is not None:
        clean_mesh(cover)
    material = make_material()
    enclosure.data.materials.append(material)
    if cover is not None:
        cover.data.materials.append(material)

    # Improve viewport presentation without affecting exported geometry.
    bpy.ops.object.select_all(action="DESELECT")
    enclosure.select_set(True)
    bpy.context.view_layer.objects.active = enclosure
    if hasattr(bpy.ops.object, "shade_smooth_by_angle"):
        bpy.ops.object.shade_smooth_by_angle()
    else:
        # Compatibility with Blender 3.x.
        bpy.ops.object.shade_smooth()
    _annotate_enclosure(enclosure, dummy_objects)
    return enclosure, cover
