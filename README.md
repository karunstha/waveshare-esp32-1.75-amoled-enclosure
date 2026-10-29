# ESP32-S3 Touch AMOLED 1.75 enclosure

The enclosure is a parameterized, single-piece square shell generated in  
Blender. It contains:

-   a fully hollow 1.20 mm shell sized for three extrusion lines with a
    standard 0.40 mm nozzle;
-   a stepped front pocket: a shallow display recess followed by a smaller
    PCB opening in a concentric annular support ring. A thin circular sleeve
    connects the ring directly to the front shell, supporting the display
    flush with the front surface;
-   10 mm-wide top and bottom relief windows through the circular seat for the
    display cables;
-   three rear M2 access holes;
-   rear openings for the 8-pin interface, speaker connector, and battery  
    connector; and
-   two rear microphone holes and a bottom-side rounded USB-C access opening
    with an optional internal guide tunnel;
-   an independently switchable centered rear support-access hole.

The supplied mechanical drawings are the dimensional reference. The microphone  
acoustic-port centres are not dimensioned on those drawings, so their current  
positions are estimates scaled from the rear view. They are clearly identified  
near the top of the script for adjustment after a test fit.

## Generate in Blender

Open Blender, switch to **Scripting**, open `blender_enclosure.py`, then press  
**Run Script**. The generated object is named `ESP32_Display_Enclosure`.

The script also supports the Jacques Lucke **Blender Development** extension:
open `blender_enclosure.py` in VS Code and use **Blender: Run Script**.

For command-line generation and automatic STL/Blend export:

```sh
blender --background --python blender_enclosure.py -- --export
```

This writes both files to `output/`. To select another directory:

```sh
blender --background --python blender_enclosure.py -- \
  --export --output-dir my_output
```

## First parameters to tune

All measurements use millimetres and are grouped under `USER PARAMETERS`.

-   `CASE_WIDTH`, `CASE_HEIGHT`, `CASE_DEPTH`: overall square enclosure size;
    depth defaults to 15.0 mm and automatically grows if thicker walls require
    more space for the device.
-   `ENCLOSURE_THICKNESS`: side, front, and rear wall thickness, currently
    1.20 mm.
-   `OUTER_CORNER_RADIUS`: currently `0.0`, producing sharp square corners;
    set it above zero when rounded corners are restored.
-   `DEVICE_REAR_CLEARANCE` and `DEVICE_RADIAL_CLEARANCE`: required fit
    allowances checked whenever dimensions or wall thickness change.
-   `DISPLAY_POCKET_DIAMETER`: shallow recess for the Ø48.96 mm display.
-   `DISPLAY_RECESS_DEPTH`: 2.05 mm, matching the protruding display stack.
-   `BOARD_OPENING_DIAMETER`: through-opening for the Ø46.00 mm PCB.
-   `DISPLAY_PLATFORM_THICKNESS` and `DISPLAY_SUPPORT_WALL_THICKNESS`: both
    follow the 1.20 mm enclosure thickness. The sleeve and flat ring are fused
    into one watertight display cup before it is joined to the shell, preventing
    Bambu Studio from treating the ring as a separate floating body. Both
    concentric display passages are re-cut after the union to prevent slicer
    mesh repair from closing the opening with a solid top skin.
-   `ENABLE_DISPLAY_CABLE_RELIEFS` and `DISPLAY_CABLE_RELIEF_WIDTH`: control
    the top and bottom cable windows; their default width is 10.0 mm.
-   `SCREW_CENTRES`: the three M2 locations from the mechanical drawing.
-   `PIN8_OPENING`, `SPEAKER_OPENING`, `BATTERY_OPENING`: rear connector  
    openings as `(centre_x, centre_z, width, height)`.
-   `MIC_CENTRES`: estimated rear acoustic-port centres.
-   `USB_C_OPENING_WIDTH`, `USB_C_OPENING_DEPTH`, and
    `USB_C_CENTRE_FROM_FRONT`: STEP-derived bottom-side USB-C geometry. The
    receptacle envelope is 9.58 × 4.16 mm; the cutout is 10.08 × 4.66 mm after
    adding 0.50 mm total clearance, centered 8.07 mm behind the display. The
    cutout uses the connector's rounded capsule profile rather than a box.
-   `USB_C_TUNNEL_LENGTH` and `USB_C_TUNNEL_WALL`: internal guide sleeve
    length and wall thickness.
-   `ENABLE_USB_C_TUNNEL`: currently `False`, leaving only the STEP-derived
    rounded USB-C cutout.
-   `ENABLE_REAR_SUPPORT_ACCESS_HOLE`: enables or disables the additional
    centered rear opening without changing any other hole.
-   `REAR_SUPPORT_ACCESS_HOLE_DIAMETER`: rear support-access diameter,
    defaulting to 28.0 mm to remain clear of the connector openings.

Rear feature coordinates match the mechanical drawing as viewed from outside
the rear: positive drawing X is right and positive Z is up. The script mirrors
drawing X into Blender world X because the rear face is viewed along -Y. The
front/display face is -Y and the rear/connector face is +Y.
