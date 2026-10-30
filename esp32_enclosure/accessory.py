"""Rear accessory tray and its separate flush snap cover."""

from __future__ import annotations

from . import config as cfg
from .patterns import honeycomb_rosette_offsets, staggered_lattice_offsets
from .primitives import (
    add_box,
    add_x_cylinder,
    add_y_cylinder,
    add_z_cylinder,
    apply_bevel,
    subtract,
    subtract_many,
    unite,
)


def add_module_corner_holders(
    enclosure,
    module: cfg.AccessoryModule,
    rear_y: float,
) -> None:
    """Add four open L-shaped corner retainers around one accessory module."""
    wall = cfg.ACCESSORY_WALL_THICKNESS
    overlap = min(0.20, wall / 2.0)
    holder_depth = cfg.MODULE_HOLDER_HEIGHT + overlap
    holder_y = rear_y - overlap + holder_depth / 2.0
    half_w = (module.width + cfg.MODULE_HOLDER_CLEARANCE) / 2.0
    half_h = (module.height + cfg.MODULE_HOLDER_CLEARANCE) / 2.0
    arm = min(cfg.MODULE_HOLDER_ARM_LENGTH, module.width / 2.0, module.height / 2.0)

    for x_sign in (-1.0, 1.0):
        for z_sign in (-1.0, 1.0):
            x_wall = add_box(
                f"{module.name}_Corner_X_{int(x_sign)}_{int(z_sign)}",
                # Extended over the corner so it overlaps the Z arm in volume;
                # face-only contact leaves a coincident internal seam.
                (wall, holder_depth, arm + wall),
                location=(
                    module.x + x_sign * (half_w + wall / 2.0),
                    holder_y,
                    module.z + z_sign * (half_h - arm / 2.0 + wall / 2.0),
                ),
            )
            unite(enclosure, x_wall)

            z_wall = add_box(
                f"{module.name}_Corner_Z_{int(x_sign)}_{int(z_sign)}",
                # Extended over the corner so the two arms share a face;
                # edge-only contact leaves non-manifold edges after the union.
                (arm + wall, holder_depth, wall),
                location=(
                    module.x + x_sign * (half_w - arm / 2.0 + wall / 2.0),
                    holder_y,
                    module.z + z_sign * (half_h + wall / 2.0),
                ),
            )
            unite(enclosure, z_wall)


def build_back_accessory_layer(enclosure, rear_y: float):
    """Add the rear component tray and its flush, internally clipped cover."""
    if not cfg.ENABLE_BACK_ACCESSORY_LAYER:
        return None

    wall = cfg.ACCESSORY_WALL_THICKNESS
    overlap = min(0.20, wall / 2.0)
    cover_front_y = rear_y + cfg.ACCESSORY_INTERNAL_DEPTH
    cover_y = cover_front_y + cfg.ACCESSORY_COVER_THICKNESS / 2.0
    wall_start_y = rear_y - overlap
    extension_depth = cover_front_y - wall_start_y
    extension_y = (wall_start_y + cover_front_y) / 2.0

    if cfg.ENABLE_GPS_MIDDLE_PANEL_OPENING:
        gps = next(
            module for module in cfg.ACCESSORY_MODULES
            if module.name.startswith("GPS")
        )
        gps_opening = add_box(
            "GPS_24mm_Middle_Panel_Window",
            (
                cfg.GPS_MIDDLE_PANEL_OPENING_SIZE,
                cfg.REAR_WALL + 2 * cfg.BOOLEAN_MARGIN,
                cfg.GPS_MIDDLE_PANEL_OPENING_SIZE,
            ),
            location=(gps.x, rear_y, gps.z),
        )
        nearest_screw = min(
            cfg.SCREW_CENTRES,
            key=lambda centre: (
                (-centre[0] - gps.x) ** 2 + (centre[1] - gps.z) ** 2
            ),
        )
        screw_keep_out = add_y_cylinder(
            "GPS_Opening_Screw_Keep_Out",
            (
                cfg.SCREW_WELL_INNER_DIAMETER
                + 2 * cfg.SCREW_WELL_WALL_THICKNESS
                + 2 * cfg.GPS_SCREW_KEEP_OUT_MARGIN
            ),
            cfg.REAR_WALL + 4 * cfg.BOOLEAN_MARGIN,
            location=(-nearest_screw[0], rear_y, nearest_screw[1]),
        )
        # Removing this cylinder from the cutter leaves a connected solid patch
        # around the screw cup when the GPS window is cut from the middle panel.
        subtract(gps_opening, screw_keep_out)
        subtract(enclosure, gps_opening)

    # Four full-depth perimeter walls terminate against the flush cover.
    for label, x in (("Left", -cfg.CASE_WIDTH / 2.0 + wall / 2.0),
                     ("Right", cfg.CASE_WIDTH / 2.0 - wall / 2.0)):
        side = add_box(
            f"Accessory_{label}_Wall",
            (wall, extension_depth, cfg.CASE_HEIGHT),
            location=(x, extension_y, 0.0),
        )
        unite(enclosure, side)

    bottom = add_box(
        "Accessory_Bottom_Wall",
        (cfg.CASE_WIDTH - 2 * wall, extension_depth, wall),
        location=(0.0, extension_y, -cfg.CASE_HEIGHT / 2.0 + wall / 2.0),
    )
    unite(enclosure, bottom)

    top = add_box(
        "Accessory_Top_Wall",
        (cfg.CASE_WIDTH - 2 * wall, extension_depth, wall),
        location=(0.0, extension_y, cfg.CASE_HEIGHT / 2.0 - wall / 2.0),
    )
    unite(enclosure, top)

    if cfg.ENABLE_ACCESSORY_BOTTOM_MIC_VENTS:
        vent_y = rear_y + cfg.ACCESSORY_BOTTOM_MIC_VENT_OFFSET_FROM_FRONT
        mic_vent_cutters = []
        for cluster_index, cluster_x in enumerate(cfg.BASE_MIC_CENTRES_X):
            for index, (x_offset, y_offset) in enumerate(
                honeycomb_rosette_offsets(cfg.ACCESSORY_BOTTOM_MIC_VENT_PITCH)
            ):
                mic_vent_cutters.append(
                    add_z_cylinder(
                        f"Accessory_Bottom_Mic_Vent_{cluster_index}_{index}",
                        cfg.ACCESSORY_BOTTOM_MIC_VENT_DIAMETER,
                        wall + 2 * cfg.BOOLEAN_MARGIN,
                        location=(
                            cluster_x + x_offset,
                            vent_y + y_offset,
                            -cfg.CASE_HEIGHT / 2.0,
                        ),
                        vertices=cfg.VENT_CYLINDER_VERTICES,
                    )
                )
        subtract_many(
            enclosure,
            mic_vent_cutters,
            "Accessory_Bottom_Mic_Vent_Pattern",
        )

    for module in cfg.ACCESSORY_MODULES:
        add_module_corner_holders(enclosure, module, rear_y)

    # The second half of the side-vent pattern is centered on the accessory
    # chamber, behind the module-holder depth and clear of the flush cover.
    if cfg.ENABLE_BASE_AIR_VENTS and cfg.ENABLE_ACCESSORY_SIDE_AIR_VENTS:
        accessory_side_vent_y = (
            rear_y
            + cfg.ACCESSORY_INTERNAL_DEPTH * cfg.ACCESSORY_SIDE_VENT_DEPTH_FRACTION
        )
        accessory_vent_cutters = []
        for side_label, x in (("Left", -cfg.CASE_WIDTH / 2.0),
                              ("Right", cfg.CASE_WIDTH / 2.0)):
            for index, (y_offset, z_offset) in enumerate(
                staggered_lattice_offsets(
                    cfg.ACCESSORY_SIDE_VENT_COLUMNS,
                    cfg.BASE_SIDE_VENT_ROWS,
                    cfg.BASE_AIR_VENT_PITCH,
                )
            ):
                accessory_vent_cutters.append(
                    add_x_cylinder(
                        f"Accessory_{side_label}_Air_Vent_{index}",
                        cfg.BASE_AIR_VENT_DIAMETER,
                        wall + 2 * cfg.BOOLEAN_MARGIN,
                        location=(
                            x,
                            accessory_side_vent_y + y_offset,
                            z_offset,
                        ),
                        vertices=cfg.VENT_CYLINDER_VERTICES,
                    )
                )
        subtract_many(
            enclosure,
            accessory_vent_cutters,
            "Accessory_Side_Air_Vent_Pattern",
        )

    # The panel matches the 60 x 60 mm outline exactly. Its rear face is one
    # uninterrupted plane, while all retention geometry stays inside.
    cover = add_box(
        "Accessory_Flush_Snap_Cover",
        (cfg.CASE_WIDTH, cfg.ACCESSORY_COVER_THICKNESS, cfg.CASE_HEIGHT),
        location=(0.0, cover_y, 0.0),
    )

    if cfg.ENABLE_COVER_ALIGNMENT_SKIRT:
        skirt_overlap = 0.20
        skirt_depth = cfg.ACCESSORY_ALIGNMENT_SKIRT_DEPTH + skirt_overlap
        skirt_y = cover_front_y - (
            cfg.ACCESSORY_ALIGNMENT_SKIRT_DEPTH - skirt_overlap
        ) / 2.0
        skirt_inset = (
            wall
            + cfg.ACCESSORY_ALIGNMENT_SKIRT_CLEARANCE
            + cfg.ACCESSORY_ALIGNMENT_SKIRT_THICKNESS / 2.0
        )
        skirt_x = cfg.CASE_WIDTH / 2.0 - skirt_inset
        skirt_z = cfg.CASE_HEIGHT / 2.0 - skirt_inset
        vertical_length = (
            cfg.CASE_HEIGHT
            - 2 * (wall + cfg.ACCESSORY_ALIGNMENT_SKIRT_CLEARANCE)
        )
        horizontal_length = (
            cfg.CASE_WIDTH
            - 2 * (wall + cfg.ACCESSORY_ALIGNMENT_SKIRT_CLEARANCE)
        )

        for label, x in (("Left", -skirt_x), ("Right", skirt_x)):
            rib = add_box(
                f"Cover_{label}_Internal_Alignment_Rail",
                (
                    cfg.ACCESSORY_ALIGNMENT_SKIRT_THICKNESS,
                    skirt_depth,
                    vertical_length,
                ),
                location=(x, skirt_y, 0.0),
            )
            unite(cover, rib)

        for label, z in (("Bottom", -skirt_z), ("Top", skirt_z)):
            rib = add_box(
                f"Cover_{label}_Internal_Alignment_Rail",
                (
                    horizontal_length,
                    skirt_depth,
                    cfg.ACCESSORY_ALIGNMENT_SKIRT_THICKNESS,
                ),
                location=(0.0, skirt_y, z),
            )
            unite(cover, rib)

    if cfg.ENABLE_FLUSH_SNAP_COVER:
        clip_overlap = 0.25
        hook_overlap = 0.35
        top_inner_z = cfg.CASE_HEIGHT / 2.0 - wall
        clip_y = cover_front_y - (
            cfg.ACCESSORY_SNAP_CLIP_LENGTH - clip_overlap
        ) / 2.0
        hook_y = (
            cover_front_y
            - cfg.ACCESSORY_SNAP_CLIP_LENGTH
            + cfg.ACCESSORY_SNAP_HOOK_LENGTH / 2.0
        )
        for side_label, side_sign in (("Bottom", -1.0), ("Top", 1.0)):
            clip_z = side_sign * (
                top_inner_z
                - cfg.ACCESSORY_SNAP_WALL_CLEARANCE
                - cfg.ACCESSORY_SNAP_CLIP_THICKNESS / 2.0
            )
            hook_z = side_sign * (
                top_inner_z
                + (cfg.ACCESSORY_SNAP_HOOK_PROJECTION - hook_overlap) / 2.0
            )
            beam = add_box(
                f"Cover_{side_label}_Hidden_Clip",
                (
                    cfg.ACCESSORY_SNAP_CLIP_WIDTH,
                    cfg.ACCESSORY_SNAP_CLIP_LENGTH + clip_overlap,
                    cfg.ACCESSORY_SNAP_CLIP_THICKNESS,
                ),
                location=(cfg.ACCESSORY_SNAP_CLIP_X_CENTRE, clip_y, clip_z),
            )
            unite(cover, beam)

            # Put all of the extra root thickness on the chamber side of the
            # beam. Centering it on the beam would protrude into the tray wall
            # and prevent the cover from seating fully.
            root_thickness = (
                cfg.ACCESSORY_SNAP_CLIP_THICKNESS
                + cfg.ACCESSORY_SNAP_ROOT_EXTRA_THICKNESS
            )
            root_z = side_sign * (
                top_inner_z
                - cfg.ACCESSORY_SNAP_WALL_CLEARANCE
                - root_thickness / 2.0
            )
            root = add_box(
                f"Cover_{side_label}_Clip_Root_Reinforcement",
                (
                    cfg.ACCESSORY_SNAP_CLIP_WIDTH
                    + cfg.ACCESSORY_SNAP_ROOT_EXTRA_WIDTH,
                    cfg.ACCESSORY_SNAP_ROOT_DEPTH + clip_overlap,
                    root_thickness,
                ),
                location=(
                    cfg.ACCESSORY_SNAP_CLIP_X_CENTRE,
                    cover_front_y
                    - (cfg.ACCESSORY_SNAP_ROOT_DEPTH - clip_overlap) / 2.0,
                    root_z,
                ),
            )
            unite(cover, root)

            hook = add_box(
                f"Cover_{side_label}_Snap_Hook",
                (
                    cfg.ACCESSORY_SNAP_CLIP_WIDTH,
                    cfg.ACCESSORY_SNAP_HOOK_LENGTH,
                    cfg.ACCESSORY_SNAP_HOOK_PROJECTION + hook_overlap,
                ),
                location=(cfg.ACCESSORY_SNAP_CLIP_X_CENTRE, hook_y, hook_z),
            )
            apply_bevel(
                hook,
                min(0.20, cfg.ACCESSORY_SNAP_HOOK_PROJECTION / 3.0),
                segments=2,
            )
            unite(cover, hook)

            slot = add_box(
                f"Accessory_{side_label}_Snap_Slot",
                (
                    cfg.ACCESSORY_SNAP_CLIP_WIDTH
                    + 2 * cfg.ACCESSORY_SNAP_SLOT_CLEARANCE,
                    cfg.ACCESSORY_SNAP_HOOK_LENGTH
                    + 2 * cfg.ACCESSORY_SNAP_SLOT_CLEARANCE,
                    wall + 2 * cfg.BOOLEAN_MARGIN,
                ),
                location=(
                    cfg.ACCESSORY_SNAP_CLIP_X_CENTRE,
                    hook_y,
                    side_sign * (cfg.CASE_HEIGHT / 2.0 - wall / 2.0),
                ),
            )
            subtract(enclosure, slot)

    # Vent the cover over the speaker with a centered staggered circular grille.
    if cfg.ENABLE_SPEAKER_VENTS:
        speaker = next(
            module for module in cfg.ACCESSORY_MODULES
            if module.name.startswith("Speaker")
        )
        speaker_vent_cutters = []
        for index, (x_offset, z_offset) in enumerate(
            staggered_lattice_offsets(
                cfg.SPEAKER_VENT_COLUMNS,
                cfg.SPEAKER_VENT_ROWS,
                cfg.SPEAKER_VENT_PITCH,
            )
        ):
            speaker_vent_cutters.append(
                add_y_cylinder(
                    f"Speaker_Vent_{index}",
                    cfg.SPEAKER_VENT_HOLE_DIAMETER,
                    cfg.ACCESSORY_COVER_THICKNESS + 2 * cfg.BOOLEAN_MARGIN,
                    location=(
                        speaker.x + x_offset,
                        cover_y,
                        speaker.z + z_offset,
                    ),
                    vertices=cfg.VENT_CYLINDER_VERTICES,
                )
            )
        subtract_many(cover, speaker_vent_cutters, "Speaker_Vent_Pattern")

    cover["print_separately"] = True
    cover["installation"] = "Press straight toward -Y until both clips snap"
    cover["release"] = "Press clips inward through the top and bottom slots"
    cover["flush_snap_clip_count"] = 2 if cfg.ENABLE_FLUSH_SNAP_COVER else 0
    cover["alignment_skirt_enabled"] = cfg.ENABLE_COVER_ALIGNMENT_SKIRT
    cover["alignment_rail_depth_mm"] = cfg.ACCESSORY_ALIGNMENT_SKIRT_DEPTH
    cover["clip_beam_thickness_mm"] = cfg.ACCESSORY_SNAP_CLIP_THICKNESS
    cover["reinforced_clip_root_thickness_mm"] = (
        cfg.ACCESSORY_SNAP_CLIP_THICKNESS
        + cfg.ACCESSORY_SNAP_ROOT_EXTRA_THICKNESS
    )
    cover["gps_opening"] = "None; rear panel remains intact"
    cover["speaker_vent_pattern"] = (
        f"{cfg.SPEAKER_VENT_COLUMNS} x {cfg.SPEAKER_VENT_ROWS}, "
        f"diameter {cfg.SPEAKER_VENT_HOLE_DIAMETER} mm"
    )
    return cover
