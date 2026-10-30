"""Measured hardware, print allowances, and feature switches.

Every dimension is in millimetres. Edit the USER PARAMETERS below for ordinary
fit tuning; derived values are computed from them at import time.
"""

from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# USER PARAMETERS: measured hardware, chosen print allowances, and switches.
# See docs/geometry.md before changing any depth or coordinate references.
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
ACCESSORY_ALIGNMENT_SKIRT_DEPTH = 1.50
ACCESSORY_ALIGNMENT_SKIRT_THICKNESS = 0.50
ACCESSORY_ALIGNMENT_SKIRT_CLEARANCE = 0.20
ACCESSORY_SNAP_CLIP_LENGTH = 6.0
ACCESSORY_SNAP_CLIP_THICKNESS = 1.00
ACCESSORY_SNAP_CLIP_WIDTH = 3.40
ACCESSORY_SNAP_HOOK_PROJECTION = 1.00
ACCESSORY_SNAP_HOOK_LENGTH = 2.00
ACCESSORY_SNAP_SLOT_CLEARANCE = 0.35
ACCESSORY_SNAP_CLIP_X_CENTRE = 4.0
ACCESSORY_SNAP_ROOT_DEPTH = 1.50
ACCESSORY_SNAP_ROOT_EXTRA_WIDTH = 0.20
ACCESSORY_SNAP_ROOT_EXTRA_THICKNESS = 0.40

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
BASE_SIDE_VENT_COLUMNS = 2
BASE_SIDE_VENT_ROWS = 15
# Place the main-shell half at 65% of its front-to-rear depth.
BASE_SIDE_VENT_MAIN_DEPTH_FRACTION = 0.65
ENABLE_ACCESSORY_SIDE_AIR_VENTS = True
ACCESSORY_SIDE_VENT_COLUMNS = 2
ACCESSORY_SIDE_VENT_DEPTH_FRACTION = 0.55
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
# Width is along X; depth is along Y. The cutout adds 1.0 mm clearance per side.
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


# ---------------------------------------------------------------------------
# Drawing-space data and small, Blender-independent pattern calculations
# ---------------------------------------------------------------------------

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
