# ESP32-S3 Touch AMOLED 1.75 enclosure

The enclosure is a parameterized square shell plus a separate flush rear
cover generated in Blender. It contains:

-   a fully hollow 1.20 mm shell sized for three extrusion lines with a
    standard 0.40 mm nozzle;
-   a stepped front pocket: a shallow display recess followed by a smaller
    PCB opening in a concentric annular support ring. A thin circular sleeve
    connects the ring directly to the front shell, supporting the display
    flush with the front surface;
-   10 mm-wide top, bottom, left, and right relief windows through the circular
    seat for display cables;
-   three rear M2 access holes;
-   three recessed screw cups that bridge the rear-wall gap to the hardware's
    M2 × 3.5 mm threaded standoffs;
-   rear openings for the 8-pin interface, speaker connector, and battery  
    connector; and
-   two bottom microphone holes flanking a rounded USB-C access opening
    with an optional internal guide tunnel;
-   an independently switchable centered rear support-access hole, disabled by
    default so the accessory holders have a continuous mounting surface;
-   an optional rear accessory chamber with L-shaped corner holders for a
    22 × 53 mm battery, 30 × 30 mm GPS module, and a speaker rotated to
    30 × 20 mm; and
-   a flush press-on cover retained by two hidden cantilever clips engaging
    the top and bottom walls, with no raised rails, tabs, or latch bar; and
-   a staggered circular speaker grille aligned with the speaker holder.
-   Mac-Pro-inspired staggered circular vent lattices through both base side
    walls and the base top wall, using support-friendly 2 mm holes;
-   one microphone hole on each side of USB-C through the base bottom; and
-   matching seven-hole honeycomb microphone/air rosettes through the
    accessory-layer bottom.

The supplied mechanical drawings are the dimensional reference. The microphone
acoustic-port centres are not dimensioned on those drawings, so their bottom
positions beside USB-C are estimates scaled from the rear view. They are clearly
identified near the top of the script for adjustment after a test fit.

## Generate in Blender

Open Blender, switch to **Scripting**, open `blender_enclosure.py`, then press  
**Run Script**. The generated object is named `ESP32_Display_Enclosure`.

The script also supports the Jacques Lucke **Blender Development** extension:
open `blender_enclosure.py` in VS Code and use **Blender: Run Script**.

For command-line generation and automatic STL/Blend export:

```sh
blender --background --python blender_enclosure.py -- --export
```

This writes the Blend file, enclosure STL, and separate flush-cover STL to
`output/`. To select another directory:

```sh
blender --background --python blender_enclosure.py -- \
  --export --output-dir my_output
```

## First parameters to tune

All measurements use millimetres and are grouped under `USER PARAMETERS`.

-   `CASE_WIDTH`, `CASE_HEIGHT`, `CASE_DEPTH`: overall square enclosure size;
    depth defaults to 14.0 mm and automatically grows if thicker walls require
    more space for the device.
-   `ENCLOSURE_THICKNESS`: side, front, and rear wall thickness, currently
    1.20 mm.
-   `OUTER_CORNER_RADIUS`: currently `0.0`, producing sharp square corners;
    set it above zero when rounded corners are restored.
-   `DEVICE_REAR_CLEARANCE` and `DEVICE_RADIAL_CLEARANCE`: required fit
    allowances checked whenever dimensions or wall thickness change. Rear
    clearance is now 0.10 mm to fit the 12.70 mm hardware in the 14 mm section.
-   `DISPLAY_POCKET_DIAMETER`: shallow recess for the Ø48.96 mm display.
-   `DISPLAY_RECESS_DEPTH`: 2.05 mm, matching the protruding display stack.
-   `BOARD_OPENING_DIAMETER`: 46.70 mm through-opening for the Ø46.00 mm PCB,
    providing 0.35 mm radial clearance.
-   `DISPLAY_PLATFORM_THICKNESS` and `DISPLAY_SUPPORT_WALL_THICKNESS`: both
    follow the 1.20 mm enclosure thickness. The sleeve and flat ring are fused
    into one watertight display cup before it is joined to the shell, preventing
    Bambu Studio from treating the ring as a separate floating body. Both
    concentric display passages are re-cut after the union to prevent slicer
    mesh repair from closing the opening with a solid top skin.
-   `ENABLE_DISPLAY_CABLE_RELIEFS` and `DISPLAY_CABLE_RELIEF_WIDTH`: control
    all four cable windows; their default width is 10.0 mm.
-   `SCREW_CENTRES`: the three M2 locations from the mechanical drawing.
-   `ENABLE_RECESSED_SCREW_WELLS` and the `SCREW_WELL_*` parameters: control
    the three guided screw recesses and their bottom shoulders. The default
    `SCREW_WELL_DEPTH_REDUCTION` shortens each bump by 1.5 mm. With the 14 mm
    main section, each bump projects 0.9 mm inward from the rear wall.
-   `PIN8_OPENING`, `SPEAKER_OPENING`, `BATTERY_OPENING`: rear connector  
    openings as `(centre_x, centre_z, width, height)`.
-   `BASE_MIC_CENTRES_X`: estimated bottom acoustic-port centres beside USB-C.
-   `USB_C_OPENING_WIDTH`, `USB_C_OPENING_DEPTH`, and
    `USB_C_CENTRE_FROM_FRONT`: STEP-derived bottom-side USB-C geometry. The
    receptacle envelope is 9.58 × 4.16 mm. The cutout is now 11.58 × 6.16 mm,
    providing 1.0 mm clearance on every side. Its center is 9.39 mm behind the
    display after the latest 2.40 mm move toward the base/rear. The
    cutout uses the connector's rounded capsule profile rather than a box.
-   `USB_C_TUNNEL_LENGTH` and `USB_C_TUNNEL_WALL`: internal guide sleeve
    length and wall thickness.
-   `ENABLE_USB_C_TUNNEL`: currently `True`, adding a 6.2 mm-long rounded guide
    tunnel from the shell exterior to the STEP-aligned USB-C receptacle.
-   `ENABLE_REAR_SUPPORT_ACCESS_HOLE`: enables or disables the additional
    centered rear opening without changing any other hole. It is currently
    `False` for a solid accessory mounting floor.
-   `REAR_SUPPORT_ACCESS_HOLE_DIAMETER`: rear support-access diameter,
    defaulting to 28.0 mm to remain clear of the connector openings.
-   `ENABLE_BACK_ACCESSORY_LAYER`: enables the complete rear component chamber
    and separate flush snap cover.
-   `ACCESSORY_DEPTH_REDUCTION`: shortens the rear chamber by 2 mm, leaving
    10.8 mm internal depth. Verify any nominally 12 mm component before print.
-   `ENABLE_GPS_MIDDLE_PANEL_OPENING`: cuts a 24 × 24 mm GPS antenna window
    through the fixed middle panel while leaving the rear cover intact. A
    circular solid keep-out preserves and connects the nearby screw cup.
-   `MODULE_HOLDER_CLEARANCE`, `MODULE_HOLDER_HEIGHT`, and
    `MODULE_HOLDER_ARM_LENGTH`: control the open L-shaped corner retainers.
-   `ENABLE_FLUSH_SNAP_COVER` and the `ACCESSORY_SNAP_*` parameters control one
    top and one bottom clip with matching release slots. Both clips sit in the
    X-axis gap between the GPS/speaker and battery footprints. All retention
    features remain inside the 60 × 60 mm outline.
-   `ENABLE_SPEAKER_VENTS` and the `SPEAKER_VENT_*` parameters: control the
    rear-cover speaker grille pattern.
-   `ENABLE_BASE_AIR_VENTS`, `BASE_AIR_VENT_PITCH`, and the related row/column
    parameters: control the centered staggered vent lattices on the original
    display enclosure.
-   `ENABLE_BASE_MIC_PORTS` and the `BASE_MIC_*` parameters: control the two
    bottom microphone holes beside USB-C.
-   `ENABLE_ACCESSORY_BOTTOM_MIC_VENTS` and the
    `ACCESSORY_BOTTOM_MIC_VENT_*` parameters: control the matching holes in the
    accessory-layer bottom wall.

Rear feature coordinates match the mechanical drawing as viewed from outside
the rear: positive drawing X is right and positive Z is up. The script mirrors
drawing X into Blender world X because the rear face is viewed along -Y. The
front/display face is -Y and the rear/connector face is +Y.
