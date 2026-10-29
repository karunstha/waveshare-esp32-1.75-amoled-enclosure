"""Parametric square enclosure for the Waveshare ESP32-S3-Touch-AMOLED-1.75.

Designed from the two mechanical drawings supplied with this project.  All
dimensions are millimetres.  Run from Blender's Scripting workspace, or with:

    blender --background --python blender_enclosure.py -- --export

The display/front face is -Y.  The connector/rear face is +Y.  Looking at the
rear of the finished enclosure, +X is right and +Z is up.
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import bpy


# ---------------------------------------------------------------------------
# USER PARAMETERS - revise these values after the first physical test print.
# ---------------------------------------------------------------------------

# Hardware envelope and fit allowances
MODULE_MAX_DEPTH = 12.70
DEVICE_REAR_CLEARANCE = 1.00
DEVICE_RADIAL_CLEARANCE = 1.00
MIN_CASE_DEPTH = 15.0

# Enclosure envelope
CASE_WIDTH = 60.0
CASE_HEIGHT = 60.0
ENCLOSURE_THICKNESS = 1.20
SIDE_WALL = ENCLOSURE_THICKNESS
FRONT_WALL = ENCLOSURE_THICKNESS
REAR_WALL = ENCLOSURE_THICKNESS
# Depth grows automatically if a future wall-thickness increase would consume
# the STEP-derived hardware envelope or the requested rear clearance.
CASE_DEPTH = max(
    MIN_CASE_DEPTH,
    MODULE_MAX_DEPTH + DEVICE_REAR_CLEARANCE + REAR_WALL,
)
# Match the display cup to the printable shell: three 0.40 mm extrusion lines.
DISPLAY_PLATFORM_THICKNESS = ENCLOSURE_THICKNESS
DISPLAY_SUPPORT_WALL_THICKNESS = ENCLOSURE_THICKNESS
# Temporarily disabled; restore a positive value when rounded corners return.
OUTER_CORNER_RADIUS = 0.0
# Keep cut edges sharp by default so the display support shoulder stays flat.
EDGE_BEVEL = 0.0

# Stepped display pocket. The touch-panel glass is wider than the PCB, so the
# larger shallow cut seats the glass while the smaller through-cut admits the
# PCB. The annulus between them is the display support platform.
DISPLAY_OUTER_DIAMETER = 48.96
BOARD_OUTER_DIAMETER = 46.00
DISPLAY_RECESS_DEPTH = 2.05
DISPLAY_DIAMETRAL_CLEARANCE = 0.40
BOARD_DIAMETRAL_CLEARANCE = 0.50
DISPLAY_POCKET_DIAMETER = DISPLAY_OUTER_DIAMETER + DISPLAY_DIAMETRAL_CLEARANCE
BOARD_OPENING_DIAMETER = BOARD_OUTER_DIAMETER + BOARD_DIAMETRAL_CLEARANCE

# Cable reliefs interrupt the circular display seat at all four cardinal sides.
# Each 10 mm notch runs radially across the full support band.
ENABLE_DISPLAY_CABLE_RELIEFS = True
DISPLAY_CABLE_RELIEF_WIDTH = 10.0

# Three M2 mounting/access holes in rear-view drawing coordinates.
# Correct drawing dimensions: left pair X=-14.70, Z=+/-13.75;
# right hole X=+20.50, Z=0.
SCREW_HOLE_DIAMETER = 2.40
SCREW_CENTRES = (
    (-14.70, +13.75),
    (-14.70, -13.75),
    (+20.50, 0.00),
)

# Recessed screw cups bridge the air gap from the rear wall to the three
# M2 x 3.5 mm threaded standoffs. The drawing places the standoff tips 10.40 mm
# behind the flush display surface.
ENABLE_RECESSED_SCREW_WELLS = True
SCREW_MOUNT_DEPTH_FROM_FRONT = 10.40
SCREW_WELL_INNER_DIAMETER = 5.00
SCREW_WELL_WALL_THICKNESS = ENCLOSURE_THICKNESS
SCREW_WELL_FLOOR_THICKNESS = ENCLOSURE_THICKNESS

# Rear connector openings. Tuple values are (centre_x, centre_z, width, height).
# Add tolerance here instead of editing boolean operations below.
PIN8_OPENING = (-18.30, 0.00, 5.20, 21.00)
SPEAKER_OPENING = (+17.50, +7.50, 6.50, 6.00)
BATTERY_OPENING = (+17.50, -7.50, 6.50, 6.00)

# Optional rear access hole for reaching/removing 3D-print support material.
# Ø28 mm stays centered and clear of the existing rear connector cutouts.
ENABLE_REAR_SUPPORT_ACCESS_HOLE = False
REAR_SUPPORT_ACCESS_HOLE_DIAMETER = 28.0

# Optional rear accessory chamber. The layout packs the battery on the left,
# GPS at upper-right, and the speaker (rotated 30 x 20) at lower-right.
ENABLE_BACK_ACCESSORY_LAYER = True
ACCESSORY_MAX_HEIGHT = 12.0
ACCESSORY_DEPTH_CLEARANCE = 0.80
ACCESSORY_INTERNAL_DEPTH = ACCESSORY_MAX_HEIGHT + ACCESSORY_DEPTH_CLEARANCE
ACCESSORY_WALL_THICKNESS = ENCLOSURE_THICKNESS
MODULE_HOLDER_CLEARANCE = 0.60
MODULE_HOLDER_HEIGHT = 3.0
MODULE_HOLDER_ARM_LENGTH = 5.0

# Top-loading sliding cover and guide rails.
ACCESSORY_COVER_THICKNESS = ENCLOSURE_THICKNESS
ACCESSORY_COVER_CLEARANCE = 0.35
ACCESSORY_RAIL_PROTRUSION = 2.0
ACCESSORY_COVER_STOP_HEIGHT = 2.0
ACCESSORY_COVER_PULL_TAB_WIDTH = 12.0
ACCESSORY_COVER_PULL_TAB_HEIGHT = 2.0

# Flexible snap-flap lock integrated into the top center of the sliding cover.
ENABLE_ACCESSORY_COVER_LOCK = True
ACCESSORY_LOCK_FLAP_WIDTH = 12.0
ACCESSORY_LOCK_FLAP_LENGTH = 12.0
ACCESSORY_LOCK_SLOT_WIDTH = 1.0
ACCESSORY_LOCK_HOOK_DEPTH = 1.20
ACCESSORY_LOCK_HOOK_HEIGHT = 1.50
# Embed the snap hook into the cover instead of merely touching its surface.
# A volumetric overlap is essential for a watertight union in slicers.
ACCESSORY_LOCK_HOOK_EMBED = 0.60
ACCESSORY_LOCK_CATCH_HEIGHT = 1.20
ACCESSORY_LOCK_VERTICAL_CLEARANCE = 0.20

# Speaker grille through the sliding rear cover.
ENABLE_SPEAKER_VENTS = True
SPEAKER_VENT_HOLE_DIAMETER = 2.00
SPEAKER_VENT_COLUMNS = 7
SPEAKER_VENT_ROWS = 5
SPEAKER_VENT_PITCH = 3.20

# Base enclosure airflow: circular holes on a staggered triangular lattice.
# The clean border around each perforated panel keeps the Mac-Pro-style pattern
# deliberate and leaves enough material at the wall edges.
ENABLE_BASE_AIR_VENTS = True
BASE_AIR_VENT_DIAMETER = 2.00
BASE_AIR_VENT_PITCH = 3.40
BASE_SIDE_VENT_COLUMNS = 4
BASE_SIDE_VENT_ROWS = 15
BASE_TOP_VENT_COLUMNS = 13
BASE_TOP_VENT_ROWS = 4

# One bottom acoustic opening for each microphone, flanking USB-C. These are
# drawing-view X coordinates; unlike rear-face openings, bottom openings do not
# need the rear-view X-axis mirror.
ENABLE_BASE_MIC_PORTS = True
BASE_MIC_PORT_DIAMETER = 2.0
BASE_MIC_CENTRES_X = (-11.5, +11.5)

# Matching seven-hole honeycomb rosettes in the bottom of the rear accessory
# layer near its front edge. The two actual base mic ports remain single holes.
ENABLE_ACCESSORY_BOTTOM_MIC_VENTS = True
ACCESSORY_BOTTOM_MIC_VENT_DIAMETER = 1.60
ACCESSORY_BOTTOM_MIC_VENT_PITCH = 2.70
# Positioned beyond the 3 mm holder depth so the vents do not weaken a clip.
ACCESSORY_BOTTOM_MIC_VENT_OFFSET_FROM_FRONT = 6.5

# USB-C receptacle envelope measured from H1_ASM in the supplied STEP model.
# Width is tangential along X; depth is front-to-rear along Y. A 0.50 mm total
# clearance is added around the connector for the plug and moulded head.
USB_C_RECEPTACLE_WIDTH = 9.58
USB_C_RECEPTACLE_DEPTH = 4.16
# 1.0 mm on every side means 2.0 mm added to each overall dimension.
USB_C_CUTOUT_CLEARANCE = 2.00
USB_C_OPENING_WIDTH = USB_C_RECEPTACLE_WIDTH + USB_C_CUTOUT_CLEARANCE
USB_C_OPENING_DEPTH = USB_C_RECEPTACLE_DEPTH + USB_C_CUTOUT_CLEARANCE
# Shifted 2.0 mm farther toward the rear/base from the STEP-derived 8.07 mm.
USB_C_CENTRE_FROM_FRONT = 10.07
ENABLE_USB_C_TUNNEL = True
USB_C_TUNNEL_LENGTH = 6.2
USB_C_TUNNEL_WALL = 0.80

# Mesh quality
CYLINDER_VERTICES = 128
# Tiny printed vents do not benefit from 128-sided cutters. At Ø2 mm, 32 sides
# are visually circular while dramatically reducing Boolean workload.
VENT_CYLINDER_VERTICES = 32
BOOLEAN_MARGIN = 1.0


@dataclass(frozen=True)
class RearRectangle:
    name: str
    x: float
    z: float
    width: float
    height: float


@dataclass(frozen=True)
class AccessoryModule:
    name: str
    x: float
    z: float
    width: float
    height: float


REAR_RECTANGLES = (
    RearRectangle("8_Pin_Interface", *PIN8_OPENING),
    RearRectangle("Speaker_Pins", *SPEAKER_OPENING),
    RearRectangle("Battery_Pins", *BATTERY_OPENING),
)


ACCESSORY_MODULES = (
    # World X is mirrored when viewed from outside the rear (+Y) face.
    AccessoryModule("Battery_22x53", +17.0, 0.0, 22.0, 53.0),
    AccessoryModule("GPS_30x30", -13.0, +13.0, 30.0, 30.0),
    AccessoryModule("Speaker_30x20", -13.0, -17.0, 30.0, 20.0),
)


def staggered_lattice_offsets(
    columns: int,
    rows: int,
    pitch: float,
) -> list[tuple[float, float]]:
    """Return a centered triangular lattice with alternating shorter rows."""
    offsets: list[tuple[float, float]] = []
    row_pitch = pitch * math.sqrt(3.0) / 2.0
    row_origin = (rows - 1) / 2.0
    for row in range(rows):
        row_columns = columns if row % 2 == 0 else max(1, columns - 1)
        column_origin = (row_columns - 1) / 2.0
        for column in range(row_columns):
            offsets.append(
                (
                    (column - column_origin) * pitch,
                    (row - row_origin) * row_pitch,
                )
            )
    return offsets


def honeycomb_rosette_offsets(pitch: float) -> list[tuple[float, float]]:
    """Return one center and six evenly spaced surrounding hole centres."""
    offsets = [(0.0, 0.0)]
    for index in range(6):
        angle = math.radians(index * 60.0)
        offsets.append((pitch * math.cos(angle), pitch * math.sin(angle)))
    return offsets


def parse_args() -> argparse.Namespace:
    """Parse only arguments after Blender's conventional `--` separator."""
    user_args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--export",
        action="store_true",
        help="Export STL and save a .blend file in ./output after generation.",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Output directory used with --export (default: ./output).",
    )
    return parser.parse_args(user_args)


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def set_units() -> None:
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "MILLIMETERS"
    scene.unit_settings.scale_length = 0.001


def add_box(name: str, size: tuple[float, float, float], location=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj


def add_y_cylinder(
    name: str,
    diameter: float,
    depth: float,
    location=(0, 0, 0),
    vertices: int = CYLINDER_VERTICES,
):
    """Add a cylinder whose axis follows Y (front-to-rear)."""
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=diameter / 2.0,
        depth=depth,
        location=location,
        rotation=(math.radians(90.0), 0.0, 0.0),
    )
    obj = bpy.context.object
    obj.name = name
    return obj


def add_x_cylinder(
    name: str,
    diameter: float,
    depth: float,
    location=(0, 0, 0),
    vertices: int = CYLINDER_VERTICES,
):
    """Add a cylinder whose axis follows X."""
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=diameter / 2.0,
        depth=depth,
        location=location,
        rotation=(0.0, math.radians(90.0), 0.0),
    )
    obj = bpy.context.object
    obj.name = name
    return obj


def add_z_cylinder(
    name: str,
    diameter: float,
    depth: float,
    location=(0, 0, 0),
    vertices: int = CYLINDER_VERTICES,
):
    """Add a cylinder whose axis follows Z."""
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=diameter / 2.0,
        depth=depth,
        location=location,
    )
    obj = bpy.context.object
    obj.name = name
    return obj


def apply_bevel(obj, width: float, segments: int = 3) -> None:
    modifier = obj.modifiers.new(name="Edge_Softening", type="BEVEL")
    modifier.width = width
    modifier.segments = segments
    modifier.limit_method = "ANGLE"
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)


def subtract(target, cutter, solver: str = "EXACT") -> None:
    modifier = target.modifiers.new(name=f"Cut_{cutter.name}", type="BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.solver = solver
    modifier.object = cutter
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


def subtract_many(target, cutters: list, name: str) -> None:
    """Join simple vent cutters and apply one fast Boolean operation."""
    if not cutters:
        return
    bpy.ops.object.select_all(action="DESELECT")
    for cutter in cutters:
        cutter.select_set(True)
    combined = cutters[0]
    bpy.context.view_layer.objects.active = combined
    bpy.ops.object.join()
    combined.name = name
    subtract(target, combined, solver="FAST")


def unite(target, addition) -> None:
    modifier = target.modifiers.new(name=f"Join_{addition.name}", type="BOOLEAN")
    modifier.operation = "UNION"
    modifier.solver = "EXACT"
    modifier.object = addition
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(addition, do_unlink=True)


def subtract_z_capsule(
    target,
    name: str,
    width: float,
    depth: float,
    cut_height: float,
    location: tuple[float, float, float],
) -> None:
    """Cut a rounded USB-style slot extruded along Z."""
    if width <= depth:
        raise ValueError("Capsule width must be greater than its depth.")
    x, y, z = location
    straight_length = width - depth
    center = add_box(
        f"{name}_Centre",
        (straight_length, depth, cut_height),
        location=(x, y, z),
    )
    subtract(target, center)
    for suffix, x_offset in (("Left", -straight_length / 2.0),
                             ("Right", straight_length / 2.0)):
        end = add_z_cylinder(
            f"{name}_{suffix}",
            depth,
            cut_height,
            location=(x + x_offset, y, z),
        )
        subtract(target, end)


def cut_display_cable_reliefs(
    target,
    name_prefix: str,
    y: float,
    cut_depth: float,
    outer_diameter: float,
    inner_diameter: float,
) -> None:
    """Remove top, bottom, left, and right windows across the support band."""
    if not ENABLE_DISPLAY_CABLE_RELIEFS:
        return
    radial_band = (outer_diameter - inner_diameter) / 2.0
    relief_height = radial_band + 2 * BOOLEAN_MARGIN
    relief_center_z = (outer_diameter + inner_diameter) / 4.0
    for label, direction in (("Top", 1.0), ("Bottom", -1.0)):
        cutter = add_box(
            f"{name_prefix}_{label}_Cable_Relief",
            (DISPLAY_CABLE_RELIEF_WIDTH, cut_depth, relief_height),
            location=(0.0, y, direction * relief_center_z),
        )
        subtract(target, cutter)

    for label, direction in (("Left", -1.0), ("Right", 1.0)):
        cutter = add_box(
            f"{name_prefix}_{label}_Cable_Relief",
            (relief_height, cut_depth, DISPLAY_CABLE_RELIEF_WIDTH),
            location=(direction * relief_center_z, y, 0.0),
        )
        subtract(target, cutter)


def add_module_corner_holders(
    enclosure,
    module: AccessoryModule,
    rear_y: float,
) -> None:
    """Add four open L-shaped corner retainers around one accessory module."""
    wall = ACCESSORY_WALL_THICKNESS
    overlap = min(0.20, wall / 2.0)
    holder_depth = MODULE_HOLDER_HEIGHT + overlap
    holder_y = rear_y - overlap + holder_depth / 2.0
    half_w = (module.width + MODULE_HOLDER_CLEARANCE) / 2.0
    half_h = (module.height + MODULE_HOLDER_CLEARANCE) / 2.0
    arm = min(MODULE_HOLDER_ARM_LENGTH, module.width / 2.0, module.height / 2.0)

    for x_sign in (-1.0, 1.0):
        for z_sign in (-1.0, 1.0):
            x_wall = add_box(
                f"{module.name}_Corner_X_{int(x_sign)}_{int(z_sign)}",
                (wall, holder_depth, arm),
                location=(
                    module.x + x_sign * (half_w + wall / 2.0),
                    holder_y,
                    module.z + z_sign * (half_h - arm / 2.0),
                ),
            )
            unite(enclosure, x_wall)

            z_wall = add_box(
                f"{module.name}_Corner_Z_{int(x_sign)}_{int(z_sign)}",
                (arm, holder_depth, wall),
                location=(
                    module.x + x_sign * (half_w - arm / 2.0),
                    holder_y,
                    module.z + z_sign * (half_h + wall / 2.0),
                ),
            )
            unite(enclosure, z_wall)


def build_back_accessory_layer(enclosure, rear_y: float):
    """Add the rear component tray and return its separate sliding cover."""
    if not ENABLE_BACK_ACCESSORY_LAYER:
        return None

    wall = ACCESSORY_WALL_THICKNESS
    overlap = min(0.20, wall / 2.0)
    cover_front_y = rear_y + ACCESSORY_INTERNAL_DEPTH
    cover_y = cover_front_y + ACCESSORY_COVER_THICKNESS / 2.0
    groove_half_depth = (
        ACCESSORY_COVER_THICKNESS / 2.0 + ACCESSORY_COVER_CLEARANCE
    )
    inner_rail_y = cover_y - groove_half_depth - wall / 2.0
    outer_rail_y = cover_y + groove_half_depth + wall / 2.0
    outer_end_y = outer_rail_y + wall / 2.0
    wall_start_y = rear_y - overlap
    extension_depth = outer_end_y - wall_start_y
    extension_y = (wall_start_y + outer_end_y) / 2.0

    # Left, right, and bottom walls extend the existing enclosure rearward.
    for label, x in (("Left", -CASE_WIDTH / 2.0 + wall / 2.0),
                     ("Right", CASE_WIDTH / 2.0 - wall / 2.0)):
        side = add_box(
            f"Accessory_{label}_Wall",
            (wall, extension_depth, CASE_HEIGHT),
            location=(x, extension_y, 0.0),
        )
        unite(enclosure, side)

    bottom = add_box(
        "Accessory_Bottom_Wall",
        (CASE_WIDTH - 2 * wall, extension_depth, wall),
        location=(0.0, extension_y, -CASE_HEIGHT / 2.0 + wall / 2.0),
    )
    unite(enclosure, bottom)

    if ENABLE_ACCESSORY_BOTTOM_MIC_VENTS:
        vent_y = rear_y + ACCESSORY_BOTTOM_MIC_VENT_OFFSET_FROM_FRONT
        mic_vent_cutters = []
        for cluster_index, cluster_x in enumerate(BASE_MIC_CENTRES_X):
            for index, (x_offset, y_offset) in enumerate(
                honeycomb_rosette_offsets(ACCESSORY_BOTTOM_MIC_VENT_PITCH)
            ):
                mic_vent_cutters.append(
                    add_z_cylinder(
                        f"Accessory_Bottom_Mic_Vent_{cluster_index}_{index}",
                        ACCESSORY_BOTTOM_MIC_VENT_DIAMETER,
                        wall + 2 * BOOLEAN_MARGIN,
                        location=(
                            cluster_x + x_offset,
                            vent_y + y_offset,
                            -CASE_HEIGHT / 2.0,
                        ),
                        vertices=VENT_CYLINDER_VERTICES,
                    )
                )
        subtract_many(
            enclosure,
            mic_vent_cutters,
            "Accessory_Bottom_Mic_Vent_Pattern",
        )

    # Stop the top wall before the cover groove, leaving a top insertion slot.
    top_wall_end_y = cover_front_y - ACCESSORY_COVER_CLEARANCE
    top_depth = top_wall_end_y - wall_start_y
    top = add_box(
        "Accessory_Top_Wall_With_Cover_Slot",
        (CASE_WIDTH - 2 * wall, top_depth, wall),
        location=(
            0.0,
            wall_start_y + top_depth / 2.0,
            CASE_HEIGHT / 2.0 - wall / 2.0,
        ),
    )
    unite(enclosure, top)

    # Paired inner/outer rails capture the cover while allowing top insertion.
    rail_height = CASE_HEIGHT - 2 * wall
    rail_x = CASE_WIDTH / 2.0 - wall + overlap - ACCESSORY_RAIL_PROTRUSION / 2.0
    for side_label, x in (("Left", -rail_x), ("Right", rail_x)):
        for rail_label, y in (("Inner", inner_rail_y), ("Outer", outer_rail_y)):
            rail = add_box(
                f"Accessory_{side_label}_{rail_label}_Cover_Rail",
                (ACCESSORY_RAIL_PROTRUSION, wall, rail_height),
                location=(x, y, 0.0),
            )
            unite(enclosure, rail)

    cover_width = CASE_WIDTH - 2 * wall - 2 * ACCESSORY_COVER_CLEARANCE
    groove_depth = ACCESSORY_COVER_THICKNESS + 2 * ACCESSORY_COVER_CLEARANCE
    stop_z = -CASE_HEIGHT / 2.0 + wall + ACCESSORY_COVER_STOP_HEIGHT / 2.0
    stop = add_box(
        "Accessory_Cover_Bottom_Stop",
        (cover_width, groove_depth, ACCESSORY_COVER_STOP_HEIGHT),
        location=(0.0, cover_y, stop_z),
    )
    unite(enclosure, stop)

    for module in ACCESSORY_MODULES:
        add_module_corner_holders(enclosure, module, rear_y)

    # Separate printable cover, shown in its installed position.
    cover_bottom_z = stop_z + ACCESSORY_COVER_STOP_HEIGHT / 2.0
    cover_height = (
        CASE_HEIGHT
        - 2 * wall
        - ACCESSORY_COVER_STOP_HEIGHT
        - ACCESSORY_COVER_CLEARANCE
    )
    cover_z = cover_bottom_z + cover_height / 2.0
    cover = add_box(
        "Accessory_Sliding_Cover",
        (cover_width, ACCESSORY_COVER_THICKNESS, cover_height),
        location=(0.0, cover_y, cover_z),
    )
    pull_tab = add_box(
        "Accessory_Cover_Pull_Tab",
        (
            ACCESSORY_COVER_PULL_TAB_WIDTH,
            ACCESSORY_COVER_THICKNESS,
            ACCESSORY_COVER_PULL_TAB_HEIGHT,
        ),
        location=(
            0.0,
            cover_y,
            cover_bottom_z + cover_height + ACCESSORY_COVER_PULL_TAB_HEIGHT / 2.0,
        ),
    )
    unite(cover, pull_tab)

    # Vent the cover over the speaker with a centered staggered circular grille.
    if ENABLE_SPEAKER_VENTS:
        speaker = next(
            module for module in ACCESSORY_MODULES
            if module.name.startswith("Speaker")
        )
        speaker_vent_cutters = []
        for index, (x_offset, z_offset) in enumerate(
            staggered_lattice_offsets(
                SPEAKER_VENT_COLUMNS,
                SPEAKER_VENT_ROWS,
                SPEAKER_VENT_PITCH,
            )
        ):
            speaker_vent_cutters.append(
                add_y_cylinder(
                    f"Speaker_Vent_{index}",
                    SPEAKER_VENT_HOLE_DIAMETER,
                    ACCESSORY_COVER_THICKNESS + 2 * BOOLEAN_MARGIN,
                    location=(
                        speaker.x + x_offset,
                        cover_y,
                        speaker.z + z_offset,
                    ),
                    vertices=VENT_CYLINDER_VERTICES,
                )
            )
        subtract_many(cover, speaker_vent_cutters, "Speaker_Vent_Pattern")

    if ENABLE_ACCESSORY_COVER_LOCK:
        cover_top_z = cover_bottom_z + cover_height

        # Two slots isolate a flexible center tongue while retaining it at the
        # bottom. Pressing this flap inward releases its rear-facing snap hook.
        slot_start_z = cover_top_z - ACCESSORY_LOCK_FLAP_LENGTH
        slot_end_z = cover_top_z + BOOLEAN_MARGIN
        slot_height = slot_end_z - slot_start_z
        slot_x = (
            ACCESSORY_LOCK_FLAP_WIDTH / 2.0
            + ACCESSORY_LOCK_SLOT_WIDTH / 2.0
        )
        for label, x in (("Left", -slot_x), ("Right", slot_x)):
            slot = add_box(
                f"Accessory_Lock_Flap_{label}_Relief",
                (
                    ACCESSORY_LOCK_SLOT_WIDTH,
                    ACCESSORY_COVER_THICKNESS + 2 * BOOLEAN_MARGIN,
                    slot_height,
                ),
                location=(0.0 + x, cover_y, (slot_start_z + slot_end_z) / 2.0),
            )
            subtract(cover, slot)

        catch_bottom_z = cover_top_z - ACCESSORY_LOCK_CATCH_HEIGHT
        hook_top_z = catch_bottom_z - ACCESSORY_LOCK_VERTICAL_CLEARANCE
        hook = add_box(
            "Accessory_Cover_Snap_Hook",
            (
                ACCESSORY_LOCK_FLAP_WIDTH,
                ACCESSORY_LOCK_HOOK_DEPTH,
                ACCESSORY_LOCK_HOOK_HEIGHT,
            ),
            location=(
                0.0,
                cover_y
                + ACCESSORY_COVER_THICKNESS / 2.0
                + ACCESSORY_LOCK_HOOK_DEPTH / 2.0
                - ACCESSORY_LOCK_HOOK_EMBED,
                hook_top_z - ACCESSORY_LOCK_HOOK_HEIGHT / 2.0,
            ),
        )
        apply_bevel(
            hook,
            min(0.30, ACCESSORY_LOCK_HOOK_DEPTH / 3.0),
            segments=2,
        )
        unite(cover, hook)

        # A full-width header joins both outer rails and catches the hook when
        # the installed cover is pulled upward.
        catch = add_box(
            "Accessory_Cover_Lock_Catch_Bar",
            (
                CASE_WIDTH - 2 * wall,
                wall,
                ACCESSORY_LOCK_CATCH_HEIGHT,
            ),
            location=(
                0.0,
                outer_rail_y,
                cover_top_z - ACCESSORY_LOCK_CATCH_HEIGHT / 2.0,
            ),
        )
        unite(enclosure, catch)

    cover["print_separately"] = True
    cover["slide_direction"] = "Insert from +Z (top), slide toward -Z"
    cover["clearance_mm"] = ACCESSORY_COVER_CLEARANCE
    cover["snap_flap_lock_enabled"] = ENABLE_ACCESSORY_COVER_LOCK
    cover["speaker_vent_pattern"] = (
        f"{SPEAKER_VENT_COLUMNS} x {SPEAKER_VENT_ROWS}, "
        f"diameter {SPEAKER_VENT_HOLE_DIAMETER} mm"
    )
    return cover


def make_material():
    material = bpy.data.materials.new(name="Enclosure_Material")
    material.diffuse_color = (0.055, 0.075, 0.105, 1.0)
    material.metallic = 0.0
    material.roughness = 0.34
    return material


def validate_parameters() -> None:
    cavity_width = CASE_WIDTH - 2 * SIDE_WALL
    cavity_height = CASE_HEIGHT - 2 * SIDE_WALL
    cavity_depth = CASE_DEPTH - FRONT_WALL - REAR_WALL
    usable_depth_from_front = CASE_DEPTH - REAR_WALL
    required_depth_from_front = MODULE_MAX_DEPTH + DEVICE_REAR_CLEARANCE

    if min(cavity_width, cavity_height, cavity_depth) <= 0:
        raise ValueError("Wall values leave no internal cavity.")
    if DISPLAY_POCKET_DIAMETER >= min(CASE_WIDTH, CASE_HEIGHT):
        raise ValueError("Display pocket is larger than the enclosure face.")
    if DISPLAY_POCKET_DIAMETER <= BOARD_OPENING_DIAMETER:
        raise ValueError("Display pocket must be wider than the board opening.")
    required_radial_space = BOARD_OUTER_DIAMETER + 2 * DEVICE_RADIAL_CLEARANCE
    if min(cavity_width, cavity_height) < required_radial_space:
        raise ValueError(
            "Side-wall thickness leaves insufficient radial device clearance."
        )
    if DISPLAY_POCKET_DIAMETER + 2 * DISPLAY_SUPPORT_WALL_THICKNESS >= min(
        CASE_WIDTH, CASE_HEIGHT
    ):
        raise ValueError("Circular display support is larger than the enclosure.")
    if ENABLE_DISPLAY_CABLE_RELIEFS and not (
        0 < DISPLAY_CABLE_RELIEF_WIDTH < DISPLAY_POCKET_DIAMETER
    ):
        raise ValueError("Display cable-relief width is invalid.")
    if DISPLAY_RECESS_DEPTH <= FRONT_WALL:
        raise ValueError("Display platform must sit behind the front shell.")
    if DISPLAY_RECESS_DEPTH + DISPLAY_PLATFORM_THICKNESS >= CASE_DEPTH - REAR_WALL:
        raise ValueError("Display platform leaves no usable rear cavity.")
    if ENABLE_RECESSED_SCREW_WELLS:
        screw_gap = CASE_DEPTH - REAR_WALL - SCREW_MOUNT_DEPTH_FROM_FRONT
        if screw_gap <= 0:
            raise ValueError("Rear wall reaches or crosses the screw mounts.")
        if SCREW_WELL_INNER_DIAMETER <= SCREW_HOLE_DIAMETER:
            raise ValueError("Screw well must be wider than its through-hole.")
        if SCREW_WELL_FLOOR_THICKNESS >= (
            CASE_DEPTH - SCREW_MOUNT_DEPTH_FROM_FRONT
        ):
            raise ValueError("Screw-well floor consumes the complete recess.")
    if USB_C_OPENING_WIDTH + 2 * USB_C_TUNNEL_WALL >= CASE_WIDTH:
        raise ValueError("USB-C guide tunnel is wider than the enclosure.")
    if USB_C_OPENING_DEPTH + 2 * USB_C_TUNNEL_WALL >= CASE_DEPTH:
        raise ValueError("USB-C guide tunnel is deeper than the enclosure.")
    if USB_C_CENTRE_FROM_FRONT - USB_C_OPENING_DEPTH / 2.0 < 0:
        raise ValueError("USB-C opening extends beyond the front surface.")
    if (
        USB_C_CENTRE_FROM_FRONT
        + USB_C_OPENING_DEPTH / 2.0
        + USB_C_TUNNEL_WALL
        > CASE_DEPTH
    ):
        raise ValueError("USB-C guide tunnel extends beyond the rear surface.")
    if USB_C_TUNNEL_LENGTH <= SIDE_WALL:
        raise ValueError("USB-C guide tunnel must extend beyond the side wall.")
    if ENABLE_BASE_AIR_VENTS and (
        BASE_AIR_VENT_DIAMETER <= 0
        or BASE_AIR_VENT_PITCH <= BASE_AIR_VENT_DIAMETER
        or BASE_SIDE_VENT_COLUMNS < 2
        or BASE_SIDE_VENT_ROWS < 1
        or BASE_TOP_VENT_COLUMNS < 2
        or BASE_TOP_VENT_ROWS < 1
    ):
        raise ValueError("Base airflow vent pattern is invalid.")
    if ENABLE_BASE_MIC_PORTS and (
        BASE_MIC_PORT_DIAMETER <= 0 or len(BASE_MIC_CENTRES_X) != 2
    ):
        raise ValueError("Exactly two valid USB-C microphone ports are required.")
    if ENABLE_REAR_SUPPORT_ACCESS_HOLE and not (
        0 < REAR_SUPPORT_ACCESS_HOLE_DIAMETER < min(CASE_WIDTH, CASE_HEIGHT)
    ):
        raise ValueError("Rear support-access hole diameter is invalid.")
    if ENABLE_BACK_ACCESSORY_LAYER:
        if ACCESSORY_INTERNAL_DEPTH < ACCESSORY_MAX_HEIGHT:
            raise ValueError("Accessory chamber is shallower than its modules.")
        if ACCESSORY_COVER_THICKNESS + 2 * ACCESSORY_COVER_CLEARANCE <= 0:
            raise ValueError("Accessory cover groove is invalid.")
        if ENABLE_ACCESSORY_COVER_LOCK and (
            ACCESSORY_LOCK_FLAP_WIDTH <= 0
            or ACCESSORY_LOCK_FLAP_LENGTH <= ACCESSORY_LOCK_HOOK_HEIGHT
            or ACCESSORY_LOCK_SLOT_WIDTH <= 0
            or ACCESSORY_LOCK_HOOK_EMBED <= 0
            or ACCESSORY_LOCK_HOOK_EMBED >= ACCESSORY_LOCK_HOOK_DEPTH
            or ACCESSORY_LOCK_HOOK_EMBED > ACCESSORY_COVER_THICKNESS
        ):
            raise ValueError("Accessory cover-lock dimensions are invalid.")
        if ENABLE_SPEAKER_VENTS and (
            SPEAKER_VENT_HOLE_DIAMETER <= 0
            or SPEAKER_VENT_PITCH <= SPEAKER_VENT_HOLE_DIAMETER
            or SPEAKER_VENT_COLUMNS < 1
            or SPEAKER_VENT_ROWS < 1
        ):
            raise ValueError("Speaker vent pattern is invalid.")
        if ENABLE_ACCESSORY_BOTTOM_MIC_VENTS and (
            ACCESSORY_BOTTOM_MIC_VENT_DIAMETER <= 0
            or ACCESSORY_BOTTOM_MIC_VENT_PITCH
            <= ACCESSORY_BOTTOM_MIC_VENT_DIAMETER
        ):
            raise ValueError("Accessory microphone rosette pattern is invalid.")
        for module in ACCESSORY_MODULES:
            holder_half_w = (
                module.width + MODULE_HOLDER_CLEARANCE
            ) / 2.0 + ACCESSORY_WALL_THICKNESS
            holder_half_h = (
                module.height + MODULE_HOLDER_CLEARANCE
            ) / 2.0 + ACCESSORY_WALL_THICKNESS
            if abs(module.x) + holder_half_w > CASE_WIDTH / 2.0:
                raise ValueError(f"{module.name} holder exceeds enclosure width.")
            if abs(module.z) + holder_half_h > CASE_HEIGHT / 2.0:
                raise ValueError(f"{module.name} holder exceeds enclosure height.")
    if usable_depth_from_front < required_depth_from_front:
        raise ValueError(
            f"Usable depth from the flush display face is "
            f"{usable_depth_from_front:.2f} mm; at least "
            f"{required_depth_from_front:.2f} mm is required."
        )


def build_enclosure():
    # Always start from a completely empty Blender scene.
    clear_scene()
    validate_parameters()
    set_units()

    # Begin with a rounded solid envelope.
    enclosure = add_box(
        "ESP32_Display_Enclosure",
        (CASE_WIDTH, CASE_DEPTH, CASE_HEIGHT),
    )
    if OUTER_CORNER_RADIUS > 0:
        apply_bevel(enclosure, OUTER_CORNER_RADIUS, segments=6)

    # Hollow the envelope. Matching the inner corner radius to the outer one
    # keeps the selected wall thickness continuous around rounded corners.
    cavity_depth = CASE_DEPTH - FRONT_WALL - REAR_WALL
    cavity_y = (FRONT_WALL - REAR_WALL) / 2.0
    cavity = add_box(
        "Internal_Cavity",
        (
            CASE_WIDTH - 2 * SIDE_WALL,
            cavity_depth,
            CASE_HEIGHT - 2 * SIDE_WALL,
        ),
        location=(0.0, cavity_y, 0.0),
    )
    inner_corner_radius = max(OUTER_CORNER_RADIUS - SIDE_WALL, 0.0)
    if inner_corner_radius > 0:
        apply_bevel(cavity, inner_corner_radius, segments=6)
    subtract(enclosure, cavity)

    # Front display entry opening through only the thin outer shell.
    front_y = -CASE_DEPTH / 2.0
    display_entry_cutter = add_y_cylinder(
        "Display_Entry_Opening",
        DISPLAY_POCKET_DIAMETER,
        FRONT_WALL + 2 * BOOLEAN_MARGIN,
        location=(0.0, front_y, 0.0),
    )
    subtract(enclosure, display_entry_cutter)

    # Form a concentric recessed cup directly from the front opening. A thin
    # circular sleeve runs inward from the surface and terminates in an annular
    # support ring. The display OD follows the sleeve; the smaller PCB passes
    # through the ring, leaving a flat circular shoulder at exactly 2.05 mm.
    support_outer_diameter = (
        DISPLAY_POCKET_DIAMETER + 2 * DISPLAY_SUPPORT_WALL_THICKNESS
    )
    sleeve_depth = DISPLAY_RECESS_DEPTH + DISPLAY_PLATFORM_THICKNESS
    sleeve_y = front_y + sleeve_depth / 2.0
    sleeve = add_y_cylinder(
        "Display_Recess_Sleeve",
        support_outer_diameter,
        sleeve_depth,
        location=(0.0, sleeve_y, 0.0),
    )
    sleeve_void = add_y_cylinder(
        "Display_Recess_Interior",
        DISPLAY_POCKET_DIAMETER,
        sleeve_depth + 2 * BOOLEAN_MARGIN,
        location=(0.0, sleeve_y, 0.0),
    )
    subtract(sleeve, sleeve_void)
    cut_display_cable_reliefs(
        sleeve,
        "Sleeve",
        sleeve_y,
        sleeve_depth + 2 * BOOLEAN_MARGIN,
        support_outer_diameter,
        BOARD_OPENING_DIAMETER,
    )

    platform_front_y = front_y + DISPLAY_RECESS_DEPTH
    platform_y = platform_front_y + DISPLAY_PLATFORM_THICKNESS / 2.0
    platform = add_y_cylinder(
        "Display_Annular_Support",
        support_outer_diameter,
        DISPLAY_PLATFORM_THICKNESS,
        location=(0.0, platform_y, 0.0),
    )
    board_cutter = add_y_cylinder(
        "PCB_Opening_In_Platform",
        BOARD_OPENING_DIAMETER,
        DISPLAY_PLATFORM_THICKNESS + 2 * BOOLEAN_MARGIN,
        location=(0.0, platform_y, 0.0),
    )
    subtract(platform, board_cutter)
    cut_display_cable_reliefs(
        platform,
        "Support",
        platform_y,
        DISPLAY_PLATFORM_THICKNESS + 2 * BOOLEAN_MARGIN,
        support_outer_diameter,
        BOARD_OPENING_DIAMETER,
    )
    # Build one watertight display cup before touching the complex enclosure
    # mesh. This prevents slicers from dropping the ring as a separate shell.
    unite(sleeve, platform)
    unite(enclosure, sleeve)

    # Re-cut the two concentric passages after every display-support union.
    # Boolean unions can otherwise leave an internal cap that mesh-repairing
    # slicers interpret as a solid top skin.
    pocket_cut_start = front_y - BOOLEAN_MARGIN
    pocket_cut_end = platform_front_y
    final_pocket_cutter = add_y_cylinder(
        "Final_Display_Pocket_Opening",
        DISPLAY_POCKET_DIAMETER,
        pocket_cut_end - pocket_cut_start,
        location=(0.0, (pocket_cut_start + pocket_cut_end) / 2.0, 0.0),
    )
    subtract(enclosure, final_pocket_cutter)

    final_board_cutter = add_y_cylinder(
        "Final_PCB_Through_Opening",
        BOARD_OPENING_DIAMETER,
        DISPLAY_PLATFORM_THICKNESS + 2 * BOOLEAN_MARGIN,
        location=(0.0, platform_y, 0.0),
    )
    subtract(enclosure, final_board_cutter)

    # Rear screw holes.
    rear_y = CASE_DEPTH / 2.0
    rear_cut_depth = REAR_WALL + 2 * BOOLEAN_MARGIN

    # Independent centered rear hole for accessing sacrificial print supports.
    # This is a separate boolean and does not alter any existing rear cutout.
    if ENABLE_REAR_SUPPORT_ACCESS_HOLE:
        support_access_cutter = add_y_cylinder(
            "Rear_Support_Access_Hole",
            REAR_SUPPORT_ACCESS_HOLE_DIAMETER,
            rear_cut_depth,
            location=(0.0, rear_y, 0.0),
        )
        subtract(enclosure, support_access_cutter)

    if ENABLE_RECESSED_SCREW_WELLS:
        screw_mount_y = front_y + SCREW_MOUNT_DEPTH_FROM_FRONT
        screw_cup_depth = rear_y - screw_mount_y
        screw_cup_y = (rear_y + screw_mount_y) / 2.0
        screw_cup_outer_diameter = (
            SCREW_WELL_INNER_DIAMETER + 2 * SCREW_WELL_WALL_THICKNESS
        )
        well_floor_rear_y = screw_mount_y + SCREW_WELL_FLOOR_THICKNESS
        well_cut_end_y = rear_y + BOOLEAN_MARGIN
        well_cut_depth = well_cut_end_y - well_floor_rear_y
        screw_cut_start_y = screw_mount_y - BOOLEAN_MARGIN
        screw_cut_end_y = rear_y + BOOLEAN_MARGIN

        for index, (drawing_x, z) in enumerate(SCREW_CENTRES, start=1):
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
                SCREW_WELL_INNER_DIAMETER,
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
                SCREW_HOLE_DIAMETER,
                screw_cut_end_y - screw_cut_start_y,
                location=(
                    world_x,
                    (screw_cut_start_y + screw_cut_end_y) / 2.0,
                    z,
                ),
            )
            subtract(enclosure, through_hole)
    else:
        for index, (drawing_x, z) in enumerate(SCREW_CENTRES, start=1):
            cutter = add_y_cylinder(
                f"M2_Screw_Hole_{index}",
                SCREW_HOLE_DIAMETER,
                rear_cut_depth,
                # A rear view looks along -Y, so drawing-right is Blender -X.
                location=(-drawing_x, rear_y, z),
            )
            subtract(enclosure, cutter)

    # Rear rectangular access openings.
    for opening in REAR_RECTANGLES:
        cutter = add_box(
            opening.name,
            (opening.width, rear_cut_depth, opening.height),
            location=(-opening.x, rear_y, opening.z),
        )
        subtract(enclosure, cutter)

    # USB-C access through the bottom (-Z) side wall. The rounded guide tunnel
    # now reaches from the shell exterior to the edge-mounted receptacle.
    usb_y = front_y + USB_C_CENTRE_FROM_FRONT
    bottom_z = -CASE_HEIGHT / 2.0
    if ENABLE_USB_C_TUNNEL:
        tunnel_z = bottom_z + USB_C_TUNNEL_LENGTH / 2.0
        usb_inner_front_y = usb_y - USB_C_OPENING_DEPTH / 2.0
        usb_inner_rear_y = usb_y + USB_C_OPENING_DEPTH / 2.0
        tunnel_front_y = max(
            usb_inner_front_y - USB_C_TUNNEL_WALL,
            front_y,
        )
        tunnel_rear_y = usb_inner_rear_y + USB_C_TUNNEL_WALL
        tunnel_outer_depth = tunnel_rear_y - tunnel_front_y
        tunnel_outer_y = (tunnel_front_y + tunnel_rear_y) / 2.0
        tunnel = add_box(
            "USB_C_Guide_Tunnel",
            (
                USB_C_OPENING_WIDTH + 2 * USB_C_TUNNEL_WALL,
                tunnel_outer_depth,
                USB_C_TUNNEL_LENGTH,
            ),
            location=(0.0, tunnel_outer_y, tunnel_z),
        )
        subtract_z_capsule(
            tunnel,
            "USB_C_Tunnel_Interior",
            USB_C_OPENING_WIDTH,
            USB_C_OPENING_DEPTH,
            USB_C_TUNNEL_LENGTH + 2 * BOOLEAN_MARGIN,
            location=(0.0, usb_y, tunnel_z),
        )
        unite(enclosure, tunnel)
        usb_cut_height = USB_C_TUNNEL_LENGTH + 2 * BOOLEAN_MARGIN
        usb_cut_z = tunnel_z
        subtract_z_capsule(
            enclosure,
            "USB_C_Tunnel_Clearance",
            USB_C_OPENING_WIDTH,
            USB_C_OPENING_DEPTH,
            usb_cut_height,
            location=(0.0, usb_y, usb_cut_z),
        )
    else:
        usb_cut_height = SIDE_WALL + 2 * BOOLEAN_MARGIN
        usb_cut_z = bottom_z
        subtract_z_capsule(
            enclosure,
            "USB_C_Accurate_Cutout",
            USB_C_OPENING_WIDTH,
            USB_C_OPENING_DEPTH,
            usb_cut_height,
            location=(0.0, usb_y, usb_cut_z),
        )

    # Mac-Pro-inspired staggered circular lattices through the two side walls
    # and top wall. Each panel is centered and retains a clean solid border.
    if ENABLE_BASE_AIR_VENTS:
        airflow_cutters = []
        for side_label, x in (("Left", -CASE_WIDTH / 2.0),
                              ("Right", CASE_WIDTH / 2.0)):
            for index, (y_offset, z_offset) in enumerate(
                staggered_lattice_offsets(
                    BASE_SIDE_VENT_COLUMNS,
                    BASE_SIDE_VENT_ROWS,
                    BASE_AIR_VENT_PITCH,
                )
            ):
                airflow_cutters.append(
                    add_x_cylinder(
                        f"Base_{side_label}_Air_Vent_{index}",
                        BASE_AIR_VENT_DIAMETER,
                        SIDE_WALL + 2 * BOOLEAN_MARGIN,
                        location=(x, y_offset, z_offset),
                        vertices=VENT_CYLINDER_VERTICES,
                    )
                )

        for index, (x_offset, y_offset) in enumerate(
            staggered_lattice_offsets(
                BASE_TOP_VENT_COLUMNS,
                BASE_TOP_VENT_ROWS,
                BASE_AIR_VENT_PITCH,
            )
        ):
            airflow_cutters.append(
                add_z_cylinder(
                    f"Base_Top_Air_Vent_{index}",
                    BASE_AIR_VENT_DIAMETER,
                    SIDE_WALL + 2 * BOOLEAN_MARGIN,
                    location=(x_offset, y_offset, CASE_HEIGHT / 2.0),
                    vertices=VENT_CYLINDER_VERTICES,
                )
            )
        subtract_many(enclosure, airflow_cutters, "Base_Airflow_Vent_Pattern")

    # The two actual microphone ports through the base bottom, one immediately
    # on each side of USB-C at the same front-to-rear position.
    if ENABLE_BASE_MIC_PORTS:
        for index, mic_x in enumerate(BASE_MIC_CENTRES_X, start=1):
            mic_port = add_z_cylinder(
                f"Base_Microphone_Hole_{index}",
                BASE_MIC_PORT_DIAMETER,
                SIDE_WALL + 2 * BOOLEAN_MARGIN,
                location=(mic_x, usb_y, bottom_z),
            )
            subtract(enclosure, mic_port)

    cover = build_back_accessory_layer(enclosure, rear_y)

    # Optional cut-edge softening. Leave this at zero for a full-width, flat
    # display seating shoulder; external case corners were already rounded.
    if EDGE_BEVEL > 0:
        apply_bevel(enclosure, EDGE_BEVEL, segments=2)
    material = make_material()
    enclosure.data.materials.append(material)
    if cover is not None:
        cover.data.materials.append(material)

    # Improve viewport presentation without affecting exported geometry.
    enclosure.select_set(True)
    bpy.context.view_layer.objects.active = enclosure
    if hasattr(bpy.ops.object, "shade_smooth_by_angle"):
        bpy.ops.object.shade_smooth_by_angle()
    else:
        # Compatibility with Blender 3.x.
        bpy.ops.object.shade_smooth()
    enclosure["dimensions_mm"] = f"{CASE_WIDTH} x {CASE_HEIGHT} x {CASE_DEPTH}"
    enclosure["display_pocket_diameter_mm"] = DISPLAY_POCKET_DIAMETER
    enclosure["board_opening_diameter_mm"] = BOARD_OPENING_DIAMETER
    enclosure["display_recess_depth_mm"] = DISPLAY_RECESS_DEPTH
    enclosure["display_platform_thickness_mm"] = DISPLAY_PLATFORM_THICKNESS
    enclosure["display_support_wall_thickness_mm"] = (
        DISPLAY_SUPPORT_WALL_THICKNESS
    )
    enclosure["display_cable_reliefs_enabled"] = ENABLE_DISPLAY_CABLE_RELIEFS
    if ENABLE_DISPLAY_CABLE_RELIEFS:
        enclosure["display_cable_relief_width_mm"] = DISPLAY_CABLE_RELIEF_WIDTH
    enclosure["shell_thickness_mm"] = ENCLOSURE_THICKNESS
    enclosure["usb_c_opening_mm"] = (
        f"{USB_C_OPENING_WIDTH} x {USB_C_OPENING_DEPTH}"
    )
    enclosure["usb_c_tunnel_enabled"] = ENABLE_USB_C_TUNNEL
    enclosure["rear_support_access_hole_enabled"] = (
        ENABLE_REAR_SUPPORT_ACCESS_HOLE
    )
    if ENABLE_REAR_SUPPORT_ACCESS_HOLE:
        enclosure["rear_support_access_hole_diameter_mm"] = (
            REAR_SUPPORT_ACCESS_HOLE_DIAMETER
        )
    enclosure["recessed_screw_wells_enabled"] = ENABLE_RECESSED_SCREW_WELLS
    if ENABLE_RECESSED_SCREW_WELLS:
        enclosure["screw_mount_gap_mm"] = (
            CASE_DEPTH - REAR_WALL - SCREW_MOUNT_DEPTH_FROM_FRONT
        )
        enclosure["screw_head_recess_depth_mm"] = (
            CASE_DEPTH
            - SCREW_MOUNT_DEPTH_FROM_FRONT
            - SCREW_WELL_FLOOR_THICKNESS
        )
    if ENABLE_USB_C_TUNNEL:
        enclosure["usb_c_tunnel_mm"] = (
            f"length {USB_C_TUNNEL_LENGTH}, wall {USB_C_TUNNEL_WALL}"
        )
    enclosure["back_accessory_layer_enabled"] = ENABLE_BACK_ACCESSORY_LAYER
    enclosure["base_air_vents_enabled"] = ENABLE_BASE_AIR_VENTS
    enclosure["base_mic_ports_enabled"] = ENABLE_BASE_MIC_PORTS
    enclosure["accessory_bottom_mic_vents_enabled"] = (
        ENABLE_ACCESSORY_BOTTOM_MIC_VENTS
    )
    if ENABLE_BACK_ACCESSORY_LAYER:
        enclosure["accessory_internal_depth_mm"] = ACCESSORY_INTERNAL_DEPTH
        enclosure["accessory_layout"] = "Battery left; GPS upper-right; speaker lower-right"
    enclosure["notes"] = "Mic centres are drawing-scaled estimates; test fit."
    return enclosure, cover


def export_outputs(enclosure, cover, output_dir: str):
    base_dir = Path(bpy.path.abspath("//")).resolve()
    destination = (base_dir / output_dir).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    blend_path = destination / "esp32_s3_touch_amoled_1_75_enclosure.blend"
    stl_path = destination / "esp32_s3_touch_amoled_1_75_enclosure.stl"
    cover_stl_path = destination / "esp32_s3_touch_amoled_1_75_sliding_cover.stl"

    bpy.ops.object.select_all(action="DESELECT")
    enclosure.select_set(True)
    bpy.context.view_layer.objects.active = enclosure
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

    # Blender 4.x and Blender 3.x use different STL operators.
    if hasattr(bpy.ops.wm, "stl_export"):
        bpy.ops.wm.stl_export(
            filepath=str(stl_path),
            export_selected_objects=True,
        )
    else:
        bpy.ops.export_mesh.stl(filepath=str(stl_path), use_selection=True)

    if cover is not None:
        bpy.ops.object.select_all(action="DESELECT")
        cover.select_set(True)
        bpy.context.view_layer.objects.active = cover
        if hasattr(bpy.ops.wm, "stl_export"):
            bpy.ops.wm.stl_export(
                filepath=str(cover_stl_path),
                export_selected_objects=True,
            )
        else:
            bpy.ops.export_mesh.stl(filepath=str(cover_stl_path), use_selection=True)
    else:
        cover_stl_path = None
    return blend_path, stl_path, cover_stl_path


def main() -> None:
    args = parse_args()
    enclosure, cover = build_enclosure()
    internal_depth = CASE_DEPTH - FRONT_WALL - REAR_WALL
    print(
        "Created ESP32 enclosure: "
        f"{CASE_WIDTH:.1f} x {CASE_HEIGHT:.1f} x {CASE_DEPTH:.1f} mm, "
        f"hollow {ENCLOSURE_THICKNESS:.2f} mm shell, "
        f"internal depth {internal_depth:.1f} mm, "
        f"display pocket Ø{DISPLAY_POCKET_DIAMETER:.2f} x "
        f"{DISPLAY_RECESS_DEPTH:.2f} mm, "
        f"board opening Ø{BOARD_OPENING_DIAMETER:.2f} mm."
    )
    if args.export:
        blend_path, stl_path, cover_stl_path = export_outputs(
            enclosure, cover, args.output_dir
        )
        print(f"Saved Blender file: {blend_path}")
        print(f"Exported STL: {stl_path}")
        if cover_stl_path is not None:
            print(f"Exported sliding cover STL: {cover_stl_path}")


# Blender's VS Code extension executes scripts with runpy.run_path(), which
# assigns the special module name "<run_path>" instead of "__main__".
if __name__ in {"__main__", "<run_path>"}:
    main()
