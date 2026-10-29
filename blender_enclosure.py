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

# Cable reliefs interrupt the circular display seat at top and bottom. Width is
# tangential along X; each notch runs radially across the full support band.
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

# Rear connector openings. Tuple values are (centre_x, centre_z, width, height).
# Add tolerance here instead of editing boolean operations below.
PIN8_OPENING = (-18.30, 0.00, 5.20, 21.00)
SPEAKER_OPENING = (+17.50, +7.50, 6.50, 6.00)
BATTERY_OPENING = (+17.50, -7.50, 6.50, 6.00)

# The microphones are the two 2.80 mm components immediately to either side
# of USB-C at the bottom of the rear view. Their acoustic port centres are not
# explicitly dimensioned, so these centres are scaled from the drawing.
MIC_HOLE_DIAMETER = 1.60
MIC_CENTRES = (
    (-11.5, -16.5),
    (+11.5, -16.5),
)

# Optional rear access hole for reaching/removing 3D-print support material.
# Ø28 mm stays centered and clear of the existing rear connector cutouts.
ENABLE_REAR_SUPPORT_ACCESS_HOLE = True
REAR_SUPPORT_ACCESS_HOLE_DIAMETER = 28.0

# USB-C receptacle envelope measured from H1_ASM in the supplied STEP model.
# Width is tangential along X; depth is front-to-rear along Y. A 0.50 mm total
# clearance is added to both dimensions for fit and print tolerance.
USB_C_RECEPTACLE_WIDTH = 9.58
USB_C_RECEPTACLE_DEPTH = 4.16
USB_C_CUTOUT_CLEARANCE = 0.50
USB_C_OPENING_WIDTH = USB_C_RECEPTACLE_WIDTH + USB_C_CUTOUT_CLEARANCE
USB_C_OPENING_DEPTH = USB_C_RECEPTACLE_DEPTH + USB_C_CUTOUT_CLEARANCE
USB_C_CENTRE_FROM_FRONT = 8.07
ENABLE_USB_C_TUNNEL = False
USB_C_TUNNEL_LENGTH = 6.2
USB_C_TUNNEL_WALL = 0.80

# Mesh quality
CYLINDER_VERTICES = 128
BOOLEAN_MARGIN = 1.0


@dataclass(frozen=True)
class RearRectangle:
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
):
    """Add a cylinder whose axis follows Y (front-to-rear)."""
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=CYLINDER_VERTICES,
        radius=diameter / 2.0,
        depth=depth,
        location=location,
        rotation=(math.radians(90.0), 0.0, 0.0),
    )
    obj = bpy.context.object
    obj.name = name
    return obj


def add_z_cylinder(
    name: str,
    diameter: float,
    depth: float,
    location=(0, 0, 0),
):
    """Add a cylinder whose axis follows Z."""
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=CYLINDER_VERTICES,
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


def subtract(target, cutter) -> None:
    modifier = target.modifiers.new(name=f"Cut_{cutter.name}", type="BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.solver = "EXACT"
    modifier.object = cutter
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


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
    """Remove 10 mm top/bottom windows across the circular support band."""
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
    if ENABLE_REAR_SUPPORT_ACCESS_HOLE and not (
        0 < REAR_SUPPORT_ACCESS_HOLE_DIAMETER < min(CASE_WIDTH, CASE_HEIGHT)
    ):
        raise ValueError("Rear support-access hole diameter is invalid.")
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

    # Rear microphone acoustic holes.
    for index, (drawing_x, z) in enumerate(MIC_CENTRES, start=1):
        cutter = add_y_cylinder(
            f"Microphone_Hole_{index}",
            MIC_HOLE_DIAMETER,
            rear_cut_depth,
            location=(-drawing_x, rear_y, z),
        )
        subtract(enclosure, cutter)

    # USB-C access through the bottom (-Z) side wall. The guide tunnel is
    # optional so the opening position can be evaluated on its own first.
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
        tunnel_void = add_box(
            "USB_C_Tunnel_Interior",
            (
                USB_C_OPENING_WIDTH,
                USB_C_OPENING_DEPTH,
                USB_C_TUNNEL_LENGTH + 2 * BOOLEAN_MARGIN,
            ),
            location=(0.0, usb_y, tunnel_z),
        )
        subtract(tunnel, tunnel_void)
        unite(enclosure, tunnel)
        usb_cut_height = USB_C_TUNNEL_LENGTH + 2 * BOOLEAN_MARGIN
        usb_cut_z = tunnel_z
        usb_cutter = add_box(
            "USB_C_Tunnel_Clearance",
            (USB_C_OPENING_WIDTH, USB_C_OPENING_DEPTH, usb_cut_height),
            location=(0.0, usb_y, usb_cut_z),
        )
        subtract(enclosure, usb_cutter)
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

    # Optional cut-edge softening. Leave this at zero for a full-width, flat
    # display seating shoulder; external case corners were already rounded.
    if EDGE_BEVEL > 0:
        apply_bevel(enclosure, EDGE_BEVEL, segments=2)
    enclosure.data.materials.append(make_material())

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
    if ENABLE_USB_C_TUNNEL:
        enclosure["usb_c_tunnel_mm"] = (
            f"length {USB_C_TUNNEL_LENGTH}, wall {USB_C_TUNNEL_WALL}"
        )
    enclosure["notes"] = "Mic centres are drawing-scaled estimates; test fit."
    return enclosure


def export_outputs(enclosure, output_dir: str) -> tuple[Path, Path]:
    base_dir = Path(bpy.path.abspath("//")).resolve()
    destination = (base_dir / output_dir).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    blend_path = destination / "esp32_s3_touch_amoled_1_75_enclosure.blend"
    stl_path = destination / "esp32_s3_touch_amoled_1_75_enclosure.stl"

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
    return blend_path, stl_path


def main() -> None:
    args = parse_args()
    enclosure = build_enclosure()
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
        blend_path, stl_path = export_outputs(enclosure, args.output_dir)
        print(f"Saved Blender file: {blend_path}")
        print(f"Exported STL: {stl_path}")


# Blender's VS Code extension executes scripts with runpy.run_path(), which
# assigns the special module name "<run_path>" instead of "__main__".
if __name__ in {"__main__", "<run_path>"}:
    main()
