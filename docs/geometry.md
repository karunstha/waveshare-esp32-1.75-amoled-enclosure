# Geometry and fit notes

This page records what is measured, what is a print allowance, and how the
Blender axes map to the hardware drawing. All dimensions are in millimetres.

## Coordinate system

- The display/front face points toward **−Y**; the rear cover is toward **+Y**.
- **X** runs left to right in Blender, and **Z** runs bottom to top.
- The rear drawing is viewed along **−Y**, so its X coordinates are mirrored
  when placed in Blender: `world_x = -drawing_x`.
- The main case is centered at Y = 0. Its front is at `-CASE_DEPTH / 2` and
  its rear is at `+CASE_DEPTH / 2`.

## Measured hardware

| Feature | Dimension or center | Source |
| --- | --- | --- |
| Touch glass outside diameter | Ø48.96 | Hardware drawing and STEP |
| Circular PCB outside diameter | Ø46.00 | Hardware drawing and STEP |
| Display stack from front | 2.05 | Hardware drawing |
| PCB front and thickness | 5.70, 1.20 | STEP bounding boxes |
| Threaded boss tip depth | 10.40 from front | Hardware drawing and STEP |
| Maximum assembly depth | 12.70 | STEP bounding box |
| USB-C receptacle envelope | 9.58 × 4.16 | STEP bounding box |
| USB-C center depth | 8.07 from front | STEP bounding box |
| Rear drawing screw centers | (−14.70, ±13.75), (+20.50, 0) | Hardware drawing |
| Upper KEY1/KEY2 switch bodies | X ≈ ±11.3, Z ≈ +17.1; center depth ≈ 7.6 from front | STEP assembly envelopes, rotated into Blender axes |

The simplified hardware collection represents the major measured envelopes.
It is a visual aid, not an exact copy of every STEP solid.

## Current printed fit allowances

- Display pocket: 49.36 mm horizontally, 49.76 mm vertically.
- PCB opening: 46.70 mm horizontally, 47.10 mm vertically.
- Vertical ellipse compensation: +0.20 mm radius on both front openings.
- Screw through-hole: Ø2.40 for M2; cup outside diameter: Ø7.40.
- USB-C opening: 11.58 × 6.16, centered 9.20 mm behind the front face.
  Its rear edge is at 12.28 mm, leaving 1.22 mm of the 13.50 mm main shell.
  The tunnel ends at 13.08 mm and stays inside the shell. This opening is
  1.13 mm rearward of the STEP receptacle center; confirm plug access with
  the physical board and cable.
- Both microphone holes are centered 9.20 mm behind the front face, in line
  with the USB-C cutout. Check their alignment with the real microphone ports.
- Cover locating rail clearance to the chamber wall: 0.20 mm.
- Rear-cover clips: 1.10 mm flexible beams with 1.70 mm thick, 2.0 mm long
  roots. Root reinforcement grows inward with 0.15 mm clearance to the tray
  wall; only the hooks enter the latch slots.
- Side button guide: Ø4.6 outer, Ø3.2 bore; Ø2.8 plunger and Ø1.8 tip.
- Side button tips nominally touch the switch body's outer envelope. This is
  a tunable first-print position because the exact moving contact face is not
  specified by the enclosure drawing.
- The chosen contact target is X = ±13.6 at Z = 17.1. The whole rotated switch
  body reaches X = ±13.8 elsewhere, so the centerline cross-section matters.

These allowances are design choices for a first print. They are not claims
about the tolerance of a particular printer or material.

## Depth stack

The 13.5 mm main case has a 1.2 mm rear wall. Its inner rear plane is 12.3 mm
behind the front. The non-connector core ends at about 10.4 mm. The three
screw risers project 0.9 mm inward from the rear wall, leaving roughly 1.0 mm
between their front ends and the threaded boss tips. The deeper connector
envelopes can use the rear interface openings.

The rear accessory chamber is currently 10.8 mm from the middle wall to the
cover's inner face. Components at the requested 12 mm maximum height need a
deeper chamber or a different cover arrangement. Confirm the battery, speaker,
and GPS dimensions before a full print.

## Checks before publishing or printing

1. Run the generator and inspect all four STL files in a slicer. Check that the
   display seat, rear wall, screw cups, guides, plungers, and snap clips remain
   connected.
2. Hide/show `FIT_CHECK_DUMMY_ESP32` in Blender to inspect interference.
3. Test the USB-C opening with the actual cable head, not just the receptacle.
4. Measure the two microphone acoustic-port positions on your board. Their
   drawing centers were not explicitly dimensioned.
5. Print a small fit test in the intended orientation and adjust the vertical
   radius compensation from the measured result.
6. Test each side button with the board installed. Adjust `SWITCH_REST_GAP`
   or tip length if a switch is preloaded or cannot be pressed fully.
