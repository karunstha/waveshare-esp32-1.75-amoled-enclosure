# Printing and assembly

## Files

| File | What it is |
| --- | --- |
| `esp32_s3_touch_amoled_1_75_enclosure.stl` | Main shell with the rear component tray |
| `esp32_s3_touch_amoled_1_75_flush_cover.stl` | Separate snap-on rear cover |

Both STLs are in [`models/`](../models/) and are in millimetres.

## Printing

These are starting points, not tested settings. Adjust for your printer.

- **Walls.** The design assumes 0.4 mm extrusion lines and 1.2 mm walls
  (three lines). Use at least three perimeters.
- **Upright prints.** `DISPLAY_VERTICAL_RADIUS_COMPENSATION` (default 0.2 mm)
  stretches the display pocket and PCB opening vertically to offset an
  upright print's tendency to come out slightly narrow in one axis. If you
  print in another orientation, set it to `0` and regenerate.
- **Cover.** The clips are thin cantilevers. Orient the cover so that layer
  lines run along the clips' length rather than across them, which is
  weakest.
- **Supports.** Inspect the model in your slicer and add supports where it
  reports overhangs (the USB-C tunnel and screw risers are the likeliest).

Print a quick fit test before the full part: the display seat, USB-C opening
and snap clips are the sensitive areas. Adjust the constants in
[`config.py`](../esp32_enclosure/config.py) and regenerate if needed.

## Assembly

1. Seat the display glass in the stepped pocket from the front, with the PCB
   passing through the smaller opening.
2. Fasten the board with three M2 screws through the rear holes. The heads sit
   in recessed cups; do not overtighten.
3. Route the 8-pin, speaker and battery connectors through their rear openings.
   Check the polarity of every connector.
4. Place the battery, GPS module and speaker into the corner holders of the
   rear tray.
5. Press the cover straight in until both clips click. Its internal rails
   locate it in the tray.

To open, press the clips inward through the slots in the top and bottom walls
and lift the cover.

## Safety

The tray fits a lithium battery. Never let a screw, connector, or sharp edge
press on a cell, and do not seal a battery in without checking clearances.
The rear chamber is 10.8 mm deep; see
[geometry notes](geometry.md#depth-stack) before fitting a thicker battery.
