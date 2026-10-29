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

import bmesh
import bpy


# ---------------------------------------------------------------------------
# USER PARAMETERS - revise these values after the first physical test print.
# ---------------------------------------------------------------------------

# Hardware envelope and fit allowances
MODULE_MAX_DEPTH = 12.70
# The core stack ends at 10.40 mm. Deeper connectors intentionally pass through
# their rear openings into the accessory chamber in the compact 13.5 mm case.
NON_CONNECTOR_HARDWARE_DEPTH = 10.40
DEVICE_REAR_CLEARANCE = 0.10
DEVICE_RADIAL_CLEARANCE = 1.00
MIN_CASE_DEPTH = 13.5
ALLOW_REAR_CONNECTOR_PROTRUSION = True

# Enclosure envelope
CASE_WIDTH = 60.0
CASE_HEIGHT = 60.0
ENCLOSURE_THICKNESS = 1.20
SIDE_WALL = ENCLOSURE_THICKNESS
FRONT_WALL = ENCLOSURE_THICKNESS
REAR_WALL = ENCLOSURE_THICKNESS
# In compact mode, connector bodies use the existing rear cutouts rather than
# forcing the complete case to match the STEP assembly's 12.70 mm maximum.
CASE_DEPTH = (
    MIN_CASE_DEPTH
    if ALLOW_REAR_CONNECTOR_PROTRUSION
    else max(
        MIN_CASE_DEPTH,
        MODULE_MAX_DEPTH + DEVICE_REAR_CLEARANCE + REAR_WALL,
    )
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
# Increased by 0.20 mm diametrically from the original 46.50 mm opening,
# i.e. 0.10 mm added to the inner radius.
BOARD_DIAMETRAL_CLEARANCE = 0.70
DISPLAY_POCKET_DIAMETER = DISPLAY_OUTER_DIAMETER + DISPLAY_DIAMETRAL_CLEARANCE
BOARD_OPENING_DIAMETER = BOARD_OUTER_DIAMETER + BOARD_DIAMETRAL_CLEARANCE
# Upright-print compensation: add 0.20 mm only to the vertical radius. The
# horizontal radius remains nominal, producing a subtle ellipse in the model.
DISPLAY_VERTICAL_RADIUS_COMPENSATION = 0.20
DISPLAY_POCKET_VERTICAL_DIAMETER = (
    DISPLAY_POCKET_DIAMETER + 2 * DISPLAY_VERTICAL_RADIUS_COMPENSATION
)
BOARD_OPENING_VERTICAL_DIAMETER = (
    BOARD_OPENING_DIAMETER + 2 * DISPLAY_VERTICAL_RADIUS_COMPENSATION
)

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

# Recessed screw cups project inward from the rear wall toward the three
# M2 x 3.5 mm threaded standoffs. The drawing places the standoff tips 10.40 mm
# behind the flush display surface.
ENABLE_RECESSED_SCREW_WELLS = True
SCREW_MOUNT_DEPTH_FROM_FRONT = 10.40
# Shorten the available 1.90 mm gap by 1.00 mm for a 0.90 mm projection.
SCREW_WELL_DEPTH_REDUCTION = 1.00
SCREW_WELL_INNER_DIAMETER = 5.00
SCREW_WELL_WALL_THICKNESS = ENCLOSURE_THICKNESS
SCREW_WELL_FLOOR_THICKNESS = ENCLOSURE_THICKNESS

# Rear connector openings. Tuple values are (centre_x, centre_z, width, height).
# Add tolerance here instead of editing boolean operations below.
PIN8_OPENING = (-18.30, 0.00, 5.20, 21.00)
# These two openings use the STEP connector centers and 1.0 mm total vertical
# clearance around their 7.65 mm envelopes.
SPEAKER_OPENING = (+17.50, +6.49, 6.50, 8.65)
BATTERY_OPENING = (+17.50, -6.81, 6.50, 8.65)

# Optional rear access hole for reaching/removing 3D-print support material.
# Ø28 mm stays centered and clear of the existing rear connector cutouts.
ENABLE_REAR_SUPPORT_ACCESS_HOLE = False
REAR_SUPPORT_ACCESS_HOLE_DIAMETER = 28.0

# Optional rear accessory chamber. The layout packs the battery on the left,
# GPS at upper-right, and the speaker (rotated 30 x 20) at lower-right.
ENABLE_BACK_ACCESSORY_LAYER = True
ACCESSORY_MAX_HEIGHT = 12.0
ACCESSORY_DEPTH_CLEARANCE = 0.80
# Reduce the rear protrusion by 2 mm. This gives 10.8 mm usable depth, so any
# nominal 12 mm component must compress or have a locally relieved cover.
ACCESSORY_DEPTH_REDUCTION = 2.0
ACCESSORY_INTERNAL_DEPTH = (
    ACCESSORY_MAX_HEIGHT
    + ACCESSORY_DEPTH_CLEARANCE
    - ACCESSORY_DEPTH_REDUCTION
)
ACCESSORY_WALL_THICKNESS = ENCLOSURE_THICKNESS
MODULE_HOLDER_CLEARANCE = 0.60
MODULE_HOLDER_HEIGHT = 3.0
MODULE_HOLDER_ARM_LENGTH = 5.0

# Add a GPS antenna window through the fixed middle mounting panel.
ENABLE_GPS_MIDDLE_PANEL_OPENING = True
GPS_MIDDLE_PANEL_OPENING_SIZE = 24.0
# Preserve a solid circular patch around the nearby lower GPS-area screw cup.
GPS_SCREW_KEEP_OUT_MARGIN = 1.0

# Flush press-on cover. One top and one bottom cantilever clip sit in the
# narrow X gap between the left modules and battery, avoiding all components.
ACCESSORY_COVER_THICKNESS = ENCLOSURE_THICKNESS
ENABLE_FLUSH_SNAP_COVER = True
ENABLE_COVER_ALIGNMENT_SKIRT = True
ACCESSORY_ALIGNMENT_SKIRT_DEPTH = 1.00
ACCESSORY_ALIGNMENT_SKIRT_THICKNESS = 0.40
ACCESSORY_ALIGNMENT_SKIRT_CLEARANCE = 0.20
ACCESSORY_SNAP_CLIP_LENGTH = 6.0
ACCESSORY_SNAP_CLIP_THICKNESS = 0.80
ACCESSORY_SNAP_CLIP_WIDTH = 3.0
ACCESSORY_SNAP_HOOK_PROJECTION = 0.80
ACCESSORY_SNAP_HOOK_LENGTH = 1.50
ACCESSORY_SNAP_SLOT_CLEARANCE = 0.35
ACCESSORY_SNAP_CLIP_X_CENTRE = 4.0

# Speaker grille through the flush rear cover.
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
BASE_AIR_VENT_PITCH = 3.20
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
# Start from 10.07 mm, move toward the display by half the finished opening
# depth, move 2.40 mm toward the base/rear, then move the tunnel 1.40 mm back
# up toward the display.
USB_C_CENTRE_FROM_FRONT = (
    10.07 - USB_C_OPENING_DEPTH / 2.0 + 2.40 - 1.40
)
ENABLE_USB_C_TUNNEL = True
USB_C_TUNNEL_LENGTH = 6.2
USB_C_TUNNEL_WALL = 0.80

# Optional simplified viewport-only hardware for checking enclosure fit. These
# measurements are taken from the supplied drawing and STEP bounding boxes.
# Objects are stored in their own collection and are never selected for STL.
ENABLE_DUMMY_ESP32 = True
DUMMY_PCB_FRONT_FROM_DISPLAY = 5.70
DUMMY_PCB_THICKNESS = 1.20
DUMMY_CARRIER_FRONT_FROM_DISPLAY = 2.05
DUMMY_CARRIER_DEPTH = 3.65
DUMMY_CARRIER_WIDTH = 40.80
DUMMY_CARRIER_HEIGHT = 46.00
DUMMY_CARRIER_CENTRE_X = -2.60
DUMMY_USB_C_CENTRE_FROM_FRONT = 8.07
DUMMY_USB_C_CENTRE_X = 0.02
DUMMY_USB_C_CENTRE_Z = -20.03
DUMMY_USB_C_HEIGHT = 7.53
DUMMY_SCREW_BOSS_DIAMETER = 3.50
DUMMY_SCREW_BOSS_FRONT_FROM_DISPLAY = 5.90
DUMMY_SCREW_BOSS_DEPTH = 4.50

# Boxes use (name, centre_x, centre_from_front, centre_z, width, depth, height).
DUMMY_MAJOR_COMPONENT_BOXES = (
    ("8_Pin_Header", 18.68, 8.30, 0.00, 2.40, 8.80, 20.85),
    ("Speaker_Connector", -17.50, 9.30, 6.49, 4.20, 4.80, 7.65),
    ("Battery_Connector", -17.50, 9.30, -6.81, 4.20, 4.80, 7.65),
    ("Microphone_Left", -10.96, 7.50, -17.54, 4.24, 1.00, 3.95),
    ("Microphone_Right", 11.74, 7.50, -17.35, 4.28, 1.00, 4.08),
)

# Mesh quality
CYLINDER_VERTICES = 128
# Tiny printed vents do not benefit from 128-sided cutters. At Ø2 mm, 32 sides
# are visually circular while dramatically reducing Boolean workload.
VENT_CYLINDER_VERTICES = 32
BOOLEAN_MARGIN = 1.0
DIMENSION_EPSILON = 1e-6


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


def add_y_ellipse(
    name: str,
    horizontal_diameter: float,
    vertical_diameter: float,
    depth: float,
    location=(0, 0, 0),
    vertices: int = CYLINDER_VERTICES,
):
    """Add a transform-normalized elliptical cylinder along global Y."""
    if horizontal_diameter <= 0 or vertical_diameter <= 0 or depth <= 0:
        raise ValueError("Ellipse dimensions must be positive.")
    obj = add_y_cylinder(
        name,
        horizontal_diameter,
        depth,
        location=location,
        vertices=vertices,
    )
    bpy.context.view_layer.objects.active = obj
    # Bake the 90-degree cylinder rotation first. Scaling Z before doing this
    # can elongate a local axis that Blender later maps into the cut depth,
    # producing malformed or unstable Boolean results.
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    obj.scale.z = vertical_diameter / horizontal_diameter
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
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


def configure_exact_boolean(modifier) -> None:
    """Make EXACT Booleans tolerate coplanar faces and touching shells.

    Without these options the many unions/cuts that land on the rear-wall plane
    leave edges shared by three faces, which slicers report as non-manifold.
    """
    if modifier.solver != "EXACT":
        return
    modifier.use_self = True
    modifier.use_hole_tolerant = True


def subtract(target, cutter, solver: str = "EXACT") -> None:
    modifier = target.modifiers.new(name=f"Cut_{cutter.name}", type="BOOLEAN")
    modifier.operation = "DIFFERENCE"
    try:
        modifier.solver = solver
    except TypeError:
        # Blender 5.x renamed the FAST solver to FLOAT.
        modifier.solver = "FLOAT" if solver == "FAST" else solver
    modifier.object = cutter
    configure_exact_boolean(modifier)
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
    configure_exact_boolean(modifier)
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
    vertical_radius_compensation: float = 0.0,
) -> None:
    """Remove top, bottom, left, and right windows across the support band."""
    if not ENABLE_DISPLAY_CABLE_RELIEFS:
        return
    radial_band = (outer_diameter - inner_diameter) / 2.0
    relief_height = radial_band + 2 * BOOLEAN_MARGIN
    horizontal_relief_center = (outer_diameter + inner_diameter) / 4.0
    vertical_relief_center = (
        horizontal_relief_center + vertical_radius_compensation
    )
    for label, direction in (("Top", 1.0), ("Bottom", -1.0)):
        cutter = add_box(
            f"{name_prefix}_{label}_Cable_Relief",
            (DISPLAY_CABLE_RELIEF_WIDTH, cut_depth, relief_height),
            location=(0.0, y, direction * vertical_relief_center),
        )
        subtract(target, cutter)

    for label, direction in (("Left", -1.0), ("Right", 1.0)):
        cutter = add_box(
            f"{name_prefix}_{label}_Cable_Relief",
            (relief_height, cut_depth, DISPLAY_CABLE_RELIEF_WIDTH),
            location=(direction * horizontal_relief_center, y, 0.0),
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
    if not ENABLE_BACK_ACCESSORY_LAYER:
        return None

    wall = ACCESSORY_WALL_THICKNESS
    overlap = min(0.20, wall / 2.0)
    cover_front_y = rear_y + ACCESSORY_INTERNAL_DEPTH
    cover_y = cover_front_y + ACCESSORY_COVER_THICKNESS / 2.0
    wall_start_y = rear_y - overlap
    extension_depth = cover_front_y - wall_start_y
    extension_y = (wall_start_y + cover_front_y) / 2.0

    if ENABLE_GPS_MIDDLE_PANEL_OPENING:
        gps = next(
            module for module in ACCESSORY_MODULES
            if module.name.startswith("GPS")
        )
        gps_opening = add_box(
            "GPS_24mm_Middle_Panel_Window",
            (
                GPS_MIDDLE_PANEL_OPENING_SIZE,
                REAR_WALL + 2 * BOOLEAN_MARGIN,
                GPS_MIDDLE_PANEL_OPENING_SIZE,
            ),
            location=(gps.x, rear_y, gps.z),
        )
        nearest_screw = min(
            SCREW_CENTRES,
            key=lambda centre: (
                (-centre[0] - gps.x) ** 2 + (centre[1] - gps.z) ** 2
            ),
        )
        screw_keep_out = add_y_cylinder(
            "GPS_Opening_Screw_Keep_Out",
            (
                SCREW_WELL_INNER_DIAMETER
                + 2 * SCREW_WELL_WALL_THICKNESS
                + 2 * GPS_SCREW_KEEP_OUT_MARGIN
            ),
            REAR_WALL + 4 * BOOLEAN_MARGIN,
            location=(-nearest_screw[0], rear_y, nearest_screw[1]),
        )
        # Removing this cylinder from the cutter leaves a connected solid patch
        # around the screw cup when the GPS window is cut from the middle panel.
        subtract(gps_opening, screw_keep_out)
        subtract(enclosure, gps_opening)

    # Four full-depth perimeter walls terminate against the flush cover.
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

    top = add_box(
        "Accessory_Top_Wall",
        (CASE_WIDTH - 2 * wall, extension_depth, wall),
        location=(0.0, extension_y, CASE_HEIGHT / 2.0 - wall / 2.0),
    )
    unite(enclosure, top)

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

    for module in ACCESSORY_MODULES:
        add_module_corner_holders(enclosure, module, rear_y)

    # The panel matches the 60 x 60 mm outline exactly. Its rear face is one
    # uninterrupted plane, while all retention geometry stays inside.
    cover = add_box(
        "Accessory_Flush_Snap_Cover",
        (CASE_WIDTH, ACCESSORY_COVER_THICKNESS, CASE_HEIGHT),
        location=(0.0, cover_y, 0.0),
    )

    if ENABLE_COVER_ALIGNMENT_SKIRT:
        skirt_overlap = 0.20
        skirt_depth = ACCESSORY_ALIGNMENT_SKIRT_DEPTH + skirt_overlap
        skirt_y = cover_front_y - (
            ACCESSORY_ALIGNMENT_SKIRT_DEPTH - skirt_overlap
        ) / 2.0
        skirt_inset = (
            wall
            + ACCESSORY_ALIGNMENT_SKIRT_CLEARANCE
            + ACCESSORY_ALIGNMENT_SKIRT_THICKNESS / 2.0
        )
        skirt_x = CASE_WIDTH / 2.0 - skirt_inset
        skirt_z = CASE_HEIGHT / 2.0 - skirt_inset
        vertical_length = (
            CASE_HEIGHT
            - 2 * (wall + ACCESSORY_ALIGNMENT_SKIRT_CLEARANCE)
        )
        horizontal_length = (
            CASE_WIDTH
            - 2 * (wall + ACCESSORY_ALIGNMENT_SKIRT_CLEARANCE)
        )

        for label, x in (("Left", -skirt_x), ("Right", skirt_x)):
            rib = add_box(
                f"Cover_{label}_Alignment_Skirt",
                (
                    ACCESSORY_ALIGNMENT_SKIRT_THICKNESS,
                    skirt_depth,
                    vertical_length,
                ),
                location=(x, skirt_y, 0.0),
            )
            unite(cover, rib)

        for label, z in (("Bottom", -skirt_z), ("Top", skirt_z)):
            rib = add_box(
                f"Cover_{label}_Alignment_Skirt",
                (
                    horizontal_length,
                    skirt_depth,
                    ACCESSORY_ALIGNMENT_SKIRT_THICKNESS,
                ),
                location=(0.0, skirt_y, z),
            )
            unite(cover, rib)

    if ENABLE_FLUSH_SNAP_COVER:
        clip_overlap = 0.25
        hook_overlap = 0.20
        top_inner_z = CASE_HEIGHT / 2.0 - wall
        clip_y = cover_front_y - (
            ACCESSORY_SNAP_CLIP_LENGTH - clip_overlap
        ) / 2.0
        hook_y = (
            cover_front_y
            - ACCESSORY_SNAP_CLIP_LENGTH
            + ACCESSORY_SNAP_HOOK_LENGTH / 2.0
        )
        for side_label, side_sign in (("Bottom", -1.0), ("Top", 1.0)):
            clip_z = side_sign * (
                top_inner_z - ACCESSORY_SNAP_CLIP_THICKNESS / 2.0
            )
            hook_z = side_sign * (
                top_inner_z
                + (ACCESSORY_SNAP_HOOK_PROJECTION - hook_overlap) / 2.0
            )
            beam = add_box(
                f"Cover_{side_label}_Hidden_Clip",
                (
                    ACCESSORY_SNAP_CLIP_WIDTH,
                    ACCESSORY_SNAP_CLIP_LENGTH + clip_overlap,
                    ACCESSORY_SNAP_CLIP_THICKNESS,
                ),
                location=(ACCESSORY_SNAP_CLIP_X_CENTRE, clip_y, clip_z),
            )
            unite(cover, beam)

            hook = add_box(
                f"Cover_{side_label}_Snap_Hook",
                (
                    ACCESSORY_SNAP_CLIP_WIDTH,
                    ACCESSORY_SNAP_HOOK_LENGTH,
                    ACCESSORY_SNAP_HOOK_PROJECTION + hook_overlap,
                ),
                location=(ACCESSORY_SNAP_CLIP_X_CENTRE, hook_y, hook_z),
            )
            apply_bevel(
                hook,
                min(0.20, ACCESSORY_SNAP_HOOK_PROJECTION / 3.0),
                segments=2,
            )
            unite(cover, hook)

            slot = add_box(
                f"Accessory_{side_label}_Snap_Slot",
                (
                    ACCESSORY_SNAP_CLIP_WIDTH
                    + 2 * ACCESSORY_SNAP_SLOT_CLEARANCE,
                    ACCESSORY_SNAP_HOOK_LENGTH
                    + 2 * ACCESSORY_SNAP_SLOT_CLEARANCE,
                    wall + 2 * BOOLEAN_MARGIN,
                ),
                location=(
                    ACCESSORY_SNAP_CLIP_X_CENTRE,
                    hook_y,
                    side_sign * (CASE_HEIGHT / 2.0 - wall / 2.0),
                ),
            )
            subtract(enclosure, slot)

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

    cover["print_separately"] = True
    cover["installation"] = "Press straight toward -Y until both clips snap"
    cover["release"] = "Press clips inward through the top and bottom slots"
    cover["flush_snap_clip_count"] = 2 if ENABLE_FLUSH_SNAP_COVER else 0
    cover["alignment_skirt_enabled"] = ENABLE_COVER_ALIGNMENT_SKIRT
    cover["gps_opening"] = "None; rear panel remains intact"
    cover["speaker_vent_pattern"] = (
        f"{SPEAKER_VENT_COLUMNS} x {SPEAKER_VENT_ROWS}, "
        f"diameter {SPEAKER_VENT_HOLE_DIAMETER} mm"
    )
    return cover


def clean_mesh(obj, merge_distance: float = 1e-5) -> None:
    """Weld near-duplicate vertices and drop zero-area faces before export."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=merge_distance)
    bmesh.ops.dissolve_degenerate(bm, dist=merge_distance, edges=bm.edges[:])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def make_material():
    material = bpy.data.materials.new(name="Enclosure_Material")
    material.diffuse_color = (0.055, 0.075, 0.105, 1.0)
    material.metallic = 0.0
    material.roughness = 0.34
    return material


def make_dummy_material(name: str, color: tuple[float, float, float, float]):
    material = bpy.data.materials.new(name=name)
    material.diffuse_color = color
    material.metallic = 0.0
    material.roughness = 0.45
    return material


def build_dummy_esp32(front_y: float) -> list:
    """Create a simplified, viewport-only ESP32 fit-check assembly."""
    if not ENABLE_DUMMY_ESP32:
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
        DISPLAY_OUTER_DIAMETER,
        DISPLAY_RECESS_DEPTH,
        location=(0.0, front_y + DISPLAY_RECESS_DEPTH / 2.0, 0.0),
    )
    register(glass, glass_material)

    carrier = add_box(
        "Dummy_Display_Carrier_STEP_Envelope",
        (DUMMY_CARRIER_WIDTH, DUMMY_CARRIER_DEPTH, DUMMY_CARRIER_HEIGHT),
        location=(
            DUMMY_CARRIER_CENTRE_X,
            front_y
            + DUMMY_CARRIER_FRONT_FROM_DISPLAY
            + DUMMY_CARRIER_DEPTH / 2.0,
            0.0,
        ),
    )
    register(carrier, keepout_material, wire=True)

    pcb_y = (
        front_y
        + DUMMY_PCB_FRONT_FROM_DISPLAY
        + DUMMY_PCB_THICKNESS / 2.0
    )
    pcb = add_y_cylinder(
        "Dummy_Circular_PCB_46mm",
        BOARD_OUTER_DIAMETER,
        DUMMY_PCB_THICKNESS,
        location=(0.0, pcb_y, 0.0),
    )
    register(pcb, pcb_material)

    usb = add_box(
        "Dummy_USB_C_Receptacle",
        (USB_C_RECEPTACLE_WIDTH, USB_C_RECEPTACLE_DEPTH, DUMMY_USB_C_HEIGHT),
        location=(
            DUMMY_USB_C_CENTRE_X,
            front_y + DUMMY_USB_C_CENTRE_FROM_FRONT,
            DUMMY_USB_C_CENTRE_Z,
        ),
    )
    register(usb, connector_material)

    for name, x, depth_from_front, z, width, depth, height in (
        DUMMY_MAJOR_COMPONENT_BOXES
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
        + DUMMY_SCREW_BOSS_FRONT_FROM_DISPLAY
        + DUMMY_SCREW_BOSS_DEPTH / 2.0
    )
    for index, (drawing_x, z) in enumerate(SCREW_CENTRES, 1):
        boss = add_y_cylinder(
            f"Dummy_M2_Boss_{index}",
            DUMMY_SCREW_BOSS_DIAMETER,
            DUMMY_SCREW_BOSS_DEPTH,
            location=(-drawing_x, boss_y, z),
            vertices=VENT_CYLINDER_VERTICES,
        )
        register(boss, connector_material)

    return objects


def validate_parameters() -> None:
    cavity_width = CASE_WIDTH - 2 * SIDE_WALL
    cavity_height = CASE_HEIGHT - 2 * SIDE_WALL
    cavity_depth = CASE_DEPTH - FRONT_WALL - REAR_WALL
    usable_depth_from_front = CASE_DEPTH - REAR_WALL
    required_depth_from_front = (
        NON_CONNECTOR_HARDWARE_DEPTH
        if ALLOW_REAR_CONNECTOR_PROTRUSION
        else MODULE_MAX_DEPTH
    ) + DEVICE_REAR_CLEARANCE

    if min(cavity_width, cavity_height, cavity_depth) <= 0:
        raise ValueError("Wall values leave no internal cavity.")
    if DISPLAY_POCKET_DIAMETER >= min(CASE_WIDTH, CASE_HEIGHT):
        raise ValueError("Display pocket is larger than the enclosure face.")
    if not 0 <= DISPLAY_VERTICAL_RADIUS_COMPENSATION:
        raise ValueError("Display vertical-radius compensation is invalid.")
    if DISPLAY_POCKET_VERTICAL_DIAMETER >= CASE_HEIGHT:
        raise ValueError("Compensated display pocket exceeds case height.")
    if DISPLAY_POCKET_DIAMETER <= BOARD_OPENING_DIAMETER:
        raise ValueError("Display pocket must be wider than the board opening.")
    if DISPLAY_POCKET_VERTICAL_DIAMETER <= BOARD_OPENING_VERTICAL_DIAMETER:
        raise ValueError("Vertical display support band has no width.")
    required_radial_space = BOARD_OUTER_DIAMETER + 2 * DEVICE_RADIAL_CLEARANCE
    if min(cavity_width, cavity_height) < required_radial_space:
        raise ValueError(
            "Side-wall thickness leaves insufficient radial device clearance."
        )
    if DISPLAY_POCKET_DIAMETER + 2 * DISPLAY_SUPPORT_WALL_THICKNESS >= min(
        CASE_WIDTH, CASE_HEIGHT
    ):
        raise ValueError("Circular display support is larger than the enclosure.")
    if (
        DISPLAY_POCKET_VERTICAL_DIAMETER
        + 2 * DISPLAY_SUPPORT_WALL_THICKNESS
        >= CASE_HEIGHT
    ):
        raise ValueError("Compensated display support exceeds case height.")
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
        if not 0 <= SCREW_WELL_DEPTH_REDUCTION < screw_gap:
            raise ValueError("Screw-well depth reduction consumes the bump.")
        if SCREW_WELL_INNER_DIAMETER <= SCREW_HOLE_DIAMETER:
            raise ValueError("Screw well must be wider than its through-hole.")
        if SCREW_WELL_FLOOR_THICKNESS >= (
            CASE_DEPTH
            - SCREW_MOUNT_DEPTH_FROM_FRONT
            - SCREW_WELL_DEPTH_REDUCTION
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
    if ENABLE_DUMMY_ESP32 and (
        DUMMY_PCB_THICKNESS <= 0
        or DUMMY_PCB_FRONT_FROM_DISPLAY + DUMMY_PCB_THICKNESS
        > MODULE_MAX_DEPTH + DIMENSION_EPSILON
        or DUMMY_CARRIER_FRONT_FROM_DISPLAY + DUMMY_CARRIER_DEPTH
        > DUMMY_PCB_FRONT_FROM_DISPLAY + DIMENSION_EPSILON
        or min(DUMMY_CARRIER_WIDTH, DUMMY_CARRIER_HEIGHT) <= 0
        or DUMMY_USB_C_HEIGHT <= 0
        or DUMMY_SCREW_BOSS_DIAMETER <= SCREW_HOLE_DIAMETER
        or DUMMY_SCREW_BOSS_DEPTH <= 0
        or DUMMY_SCREW_BOSS_FRONT_FROM_DISPLAY
        + DUMMY_SCREW_BOSS_DEPTH
        > MODULE_MAX_DEPTH + DIMENSION_EPSILON
        or any(
            min(width, depth, height) <= 0
            or depth_from_front + depth / 2.0
            > MODULE_MAX_DEPTH + DIMENSION_EPSILON
            for _, _, depth_from_front, _, width, depth, height
            in DUMMY_MAJOR_COMPONENT_BOXES
        )
    ):
        raise ValueError("Dummy ESP32 fit-check dimensions are invalid.")
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
        if ACCESSORY_INTERNAL_DEPTH <= ACCESSORY_WALL_THICKNESS:
            raise ValueError("Accessory depth reduction consumes the chamber.")
        if not 0 <= ACCESSORY_DEPTH_REDUCTION < ACCESSORY_MAX_HEIGHT:
            raise ValueError("Accessory depth reduction is invalid.")
        if ACCESSORY_COVER_THICKNESS <= 0:
            raise ValueError("Accessory cover thickness is invalid.")
        if ENABLE_COVER_ALIGNMENT_SKIRT and (
            ACCESSORY_ALIGNMENT_SKIRT_DEPTH <= 0
            or ACCESSORY_ALIGNMENT_SKIRT_DEPTH >= ACCESSORY_INTERNAL_DEPTH
            or ACCESSORY_ALIGNMENT_SKIRT_THICKNESS <= 0
            or ACCESSORY_ALIGNMENT_SKIRT_CLEARANCE < 0
            or ACCESSORY_ALIGNMENT_SKIRT_THICKNESS
            + ACCESSORY_ALIGNMENT_SKIRT_CLEARANCE
            >= ACCESSORY_WALL_THICKNESS
        ):
            raise ValueError("Cover alignment-skirt dimensions are invalid.")
        if ENABLE_FLUSH_SNAP_COVER and (
            ACCESSORY_SNAP_CLIP_LENGTH <= 0
            or ACCESSORY_SNAP_CLIP_LENGTH >= ACCESSORY_INTERNAL_DEPTH
            or ACCESSORY_SNAP_CLIP_THICKNESS <= 0
            or ACCESSORY_SNAP_CLIP_WIDTH <= 0
            or ACCESSORY_SNAP_HOOK_PROJECTION <= 0
            or ACCESSORY_SNAP_HOOK_PROJECTION > ACCESSORY_WALL_THICKNESS
            or ACCESSORY_SNAP_HOOK_LENGTH <= 0
            or ACCESSORY_SNAP_SLOT_CLEARANCE < 0
            or abs(ACCESSORY_SNAP_CLIP_X_CENTRE)
            + ACCESSORY_SNAP_CLIP_WIDTH / 2.0
            >= CASE_WIDTH / 2.0
        ):
            raise ValueError("Flush snap-cover dimensions are invalid.")
        if ENABLE_FLUSH_SNAP_COVER:
            battery = next(
                module for module in ACCESSORY_MODULES
                if module.name.startswith("Battery")
            )
            left_modules = (
                module for module in ACCESSORY_MODULES
                if module.name.startswith(("GPS", "Speaker"))
            )
            left_module_right_edge = max(
                module.x + module.width / 2.0 for module in left_modules
            )
            battery_left_edge = battery.x - battery.width / 2.0
            clip_left_edge = (
                ACCESSORY_SNAP_CLIP_X_CENTRE
                - ACCESSORY_SNAP_CLIP_WIDTH / 2.0
            )
            clip_right_edge = (
                ACCESSORY_SNAP_CLIP_X_CENTRE
                + ACCESSORY_SNAP_CLIP_WIDTH / 2.0
            )
            if not (
                left_module_right_edge < clip_left_edge
                and clip_right_edge < battery_left_edge
            ):
                raise ValueError("Top/bottom snap clips overlap a module footprint.")
        if (
            ENABLE_GPS_MIDDLE_PANEL_OPENING
            and not (
                0 < GPS_MIDDLE_PANEL_OPENING_SIZE <= 24.0
                and GPS_SCREW_KEEP_OUT_MARGIN >= 0
            )
        ):
            raise ValueError("GPS middle-panel window parameters are invalid.")
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

    front_y = -CASE_DEPTH / 2.0

    # Form a concentric recessed cup directly from the front opening. A thin
    # circular sleeve runs inward from the surface and terminates in an annular
    # support ring. The display OD follows the sleeve; the smaller PCB passes
    # through the ring, leaving a flat circular shoulder at exactly 2.05 mm.
    support_outer_diameter = (
        DISPLAY_POCKET_DIAMETER + 2 * DISPLAY_SUPPORT_WALL_THICKNESS
    )
    support_outer_vertical_diameter = (
        support_outer_diameter + 2 * DISPLAY_VERTICAL_RADIUS_COMPENSATION
    )
    # The sleeve starts inside the front wall, not on its outer face: a
    # coplanar front face makes the union non-manifold. The final pocket cut
    # below opens the front surface.
    sleeve_start_y = front_y + FRONT_WALL / 2.0
    sleeve_end_y = front_y + DISPLAY_RECESS_DEPTH + DISPLAY_PLATFORM_THICKNESS
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
        DISPLAY_POCKET_DIAMETER,
        DISPLAY_POCKET_VERTICAL_DIAMETER,
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
        DISPLAY_VERTICAL_RADIUS_COMPENSATION,
    )

    platform_front_y = front_y + DISPLAY_RECESS_DEPTH
    platform_y = platform_front_y + DISPLAY_PLATFORM_THICKNESS / 2.0
    platform = add_y_ellipse(
        "Display_Annular_Support",
        support_outer_diameter,
        support_outer_vertical_diameter,
        DISPLAY_PLATFORM_THICKNESS,
        location=(0.0, platform_y, 0.0),
    )
    board_cutter = add_y_ellipse(
        "PCB_Opening_In_Platform",
        BOARD_OPENING_DIAMETER,
        BOARD_OPENING_VERTICAL_DIAMETER,
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
        DISPLAY_VERTICAL_RADIUS_COMPENSATION,
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
    final_pocket_cutter = add_y_ellipse(
        "Final_Display_Pocket_Opening",
        DISPLAY_POCKET_DIAMETER,
        DISPLAY_POCKET_VERTICAL_DIAMETER,
        pocket_cut_end - pocket_cut_start,
        location=(0.0, (pocket_cut_start + pocket_cut_end) / 2.0, 0.0),
    )
    subtract(enclosure, final_pocket_cutter)

    final_board_cutter = add_y_ellipse(
        "Final_PCB_Through_Opening",
        BOARD_OPENING_DIAMETER,
        BOARD_OPENING_VERTICAL_DIAMETER,
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
        screw_cup_front_y = screw_mount_y + SCREW_WELL_DEPTH_REDUCTION
        screw_cup_depth = rear_y - screw_cup_front_y
        screw_cup_y = (rear_y + screw_cup_front_y) / 2.0
        screw_cup_outer_diameter = (
            SCREW_WELL_INNER_DIAMETER + 2 * SCREW_WELL_WALL_THICKNESS
        )
        well_floor_rear_y = (
            screw_cup_front_y + SCREW_WELL_FLOOR_THICKNESS
        )
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
    dummy_objects = build_dummy_esp32(front_y)

    # Optional cut-edge softening. Leave this at zero for a full-width, flat
    # display seating shoulder; external case corners were already rounded.
    if EDGE_BEVEL > 0:
        apply_bevel(enclosure, EDGE_BEVEL, segments=2)
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
    enclosure["dimensions_mm"] = f"{CASE_WIDTH} x {CASE_HEIGHT} x {CASE_DEPTH}"
    enclosure["display_pocket_diameter_mm"] = DISPLAY_POCKET_DIAMETER
    enclosure["display_pocket_vertical_diameter_mm"] = (
        DISPLAY_POCKET_VERTICAL_DIAMETER
    )
    enclosure["board_opening_diameter_mm"] = BOARD_OPENING_DIAMETER
    enclosure["board_opening_vertical_diameter_mm"] = (
        BOARD_OPENING_VERTICAL_DIAMETER
    )
    enclosure["display_vertical_radius_compensation_mm"] = (
        DISPLAY_VERTICAL_RADIUS_COMPENSATION
    )
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
        enclosure["screw_bump_depth_reduction_mm"] = (
            SCREW_WELL_DEPTH_REDUCTION
        )
        enclosure["screw_bump_inward_projection_mm"] = (
            CASE_DEPTH
            - REAR_WALL
            - SCREW_MOUNT_DEPTH_FROM_FRONT
            - SCREW_WELL_DEPTH_REDUCTION
        )
        enclosure["screw_mount_gap_mm"] = (
            CASE_DEPTH - REAR_WALL - SCREW_MOUNT_DEPTH_FROM_FRONT
        )
        enclosure["screw_head_recess_depth_mm"] = (
            CASE_DEPTH
            - SCREW_MOUNT_DEPTH_FROM_FRONT
            - SCREW_WELL_DEPTH_REDUCTION
            - SCREW_WELL_FLOOR_THICKNESS
        )
    if ENABLE_USB_C_TUNNEL:
        enclosure["usb_c_tunnel_mm"] = (
            f"length {USB_C_TUNNEL_LENGTH}, wall {USB_C_TUNNEL_WALL}"
        )
    enclosure["back_accessory_layer_enabled"] = ENABLE_BACK_ACCESSORY_LAYER
    enclosure["dummy_esp32_enabled"] = ENABLE_DUMMY_ESP32
    enclosure["dummy_esp32_object_count"] = len(dummy_objects)
    enclosure["rear_cover_mechanism"] = (
        "Flush internal top-and-bottom two-clip snap fit"
    )
    enclosure["outer_faces_planar"] = True
    enclosure["gps_middle_panel_opening_enabled"] = (
        ENABLE_GPS_MIDDLE_PANEL_OPENING
    )
    enclosure["base_air_vents_enabled"] = ENABLE_BASE_AIR_VENTS
    enclosure["base_mic_ports_enabled"] = ENABLE_BASE_MIC_PORTS
    enclosure["accessory_bottom_mic_vents_enabled"] = (
        ENABLE_ACCESSORY_BOTTOM_MIC_VENTS
    )
    if ENABLE_BACK_ACCESSORY_LAYER:
        enclosure["accessory_internal_depth_mm"] = ACCESSORY_INTERNAL_DEPTH
        enclosure["accessory_depth_reduction_mm"] = ACCESSORY_DEPTH_REDUCTION
        enclosure["accessory_layout"] = "Battery left; GPS upper-right; speaker lower-right"
    enclosure["notes"] = "Mic centres are drawing-scaled estimates; test fit."
    return enclosure, cover


def export_outputs(enclosure, cover, output_dir: str):
    base_dir = Path(bpy.path.abspath("//")).resolve()
    destination = (base_dir / output_dir).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    blend_path = destination / "esp32_s3_touch_amoled_1_75_enclosure.blend"
    stl_path = destination / "esp32_s3_touch_amoled_1_75_enclosure.stl"
    cover_stl_path = destination / "esp32_s3_touch_amoled_1_75_flush_cover.stl"

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
        f"display pocket {DISPLAY_POCKET_DIAMETER:.2f} x "
        f"{DISPLAY_POCKET_VERTICAL_DIAMETER:.2f} mm, "
        f"recess {DISPLAY_RECESS_DEPTH:.2f} mm, "
        f"board opening {BOARD_OPENING_DIAMETER:.2f} x "
        f"{BOARD_OPENING_VERTICAL_DIAMETER:.2f} mm."
    )
    if args.export:
        blend_path, stl_path, cover_stl_path = export_outputs(
            enclosure, cover, args.output_dir
        )
        print(f"Saved Blender file: {blend_path}")
        print(f"Exported STL: {stl_path}")
        if cover_stl_path is not None:
            print(f"Exported flush snap cover STL: {cover_stl_path}")


# Blender's VS Code extension executes scripts with runpy.run_path(), which
# assigns the special module name "<run_path>" instead of "__main__".
if __name__ in {"__main__", "<run_path>"}:
    main()
