# Development notes

## Code layout

The generator is a small Python package, run through the root script
`blender_enclosure.py` so it works the same from the Blender UI, the VS Code
extension, and the command line.

```text
blender_enclosure.py        thin entry point; puts the repo on sys.path
esp32_enclosure/
  config.py                 all constants and feature switches (edit this)
  patterns.py               vent-lattice maths, no Blender dependency
  primitives.py             boxes, cylinders, Boolean helpers
  display.py                display-seat cable reliefs
  switches.py               side guide tubes and two loose plungers
  accessory.py              rear tray, module holders, snap cover
  fit_check.py              viewport-only ESP32 reference model
  mesh.py                   mesh cleanup, materials
  validation.py             parameter checks run before building
  enclosure.py              build_enclosure(): main shell, in order
  export.py                 .blend and STL output
  cli.py                    argument parsing and main()
scripts/render_preview.py   front/rear/side PNG renders
scripts/inspect_mesh.py     manifold and connected-island check
scripts/check_cover_clearance.py   cover-to-tray contact check
```

`config.py` holds plain module-level constants. Other modules read them as
`cfg.NAME` at build time, so changing a value there (or assigning
`config.NAME = ...` from another script before building) takes effect.

## Order matters

`enclosure.build_enclosure()` applies Boolean unions and cuts one after another
and later steps see earlier results. Reordering steps, or changing the mesh
resolution constants, can change the exported mesh. Keep edits intentional.

## Checking that a refactor did not change the model

Export before and after a change and compare the STL hashes:

```sh
blender --background --python blender_enclosure.py -- --export --output-dir /tmp/before
# ... make changes ...
blender --background --python blender_enclosure.py -- --export --output-dir /tmp/after
shasum /tmp/before/*.stl /tmp/after/*.stl
```

The output is deterministic for a given Blender version, so identical hashes
mean identical geometry. Different Blender versions may produce different
triangulation even for the same shape.

## Regenerating the distributed files

```sh
blender --background --python blender_enclosure.py -- --export --output-dir models
blender --background --python scripts/render_preview.py
blender --background models/esp32_s3_touch_amoled_1_75_enclosure.blend --python scripts/inspect_mesh.py
blender --background models/esp32_s3_touch_amoled_1_75_enclosure.blend --python scripts/check_cover_clearance.py
```

Then delete the generated `.blend` from `models/` (it is git-ignored) and
commit the updated STLs and PNGs.

## Style

Dimensions are millimetres. Prefer adding a named constant to `config.py` over
editing a literal inside geometry code, and add a check to `validation.py` when
a new parameter can make the model impossible.
