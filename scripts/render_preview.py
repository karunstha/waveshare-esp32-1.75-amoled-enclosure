"""Render front and rear previews of the enclosure with Blender.

From the repository root:

    blender --background --python scripts/render_preview.py

The script builds the same geometry as the esp32_enclosure package. It writes only
images, not STLs. The optional fit-check dummy is hidden from the renders.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import bpy
from mathutils import Vector


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from esp32_enclosure.enclosure import build_enclosure  # noqa: E402


def parse_args() -> argparse.Namespace:
    """Accept arguments after Blender's conventional -- separator."""
    arguments = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "docs" / "images",
        help="Directory for the two PNG files (default: docs/images).",
    )
    return parser.parse_args(arguments)


def point_camera(camera, eye: tuple[float, float, float]) -> None:
    """Aim an orthographic camera at the center of the assembled case."""
    camera.location = eye
    direction = Vector((0.0, 4.0, 0.0)) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def main() -> None:
    args = parse_args()
    destination = args.output_dir.resolve()
    destination.mkdir(parents=True, exist_ok=True)

    build_enclosure()
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    world = bpy.data.worlds.new("Preview_World")
    world.color = (0.93, 0.94, 0.96)
    scene.world = world
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_cavity = True
    scene.display.shading.show_object_outline = True
    scene.display.shading.background_type = "WORLD"

    camera_data = bpy.data.cameras.new("Preview_Camera")
    camera = bpy.data.objects.new("Preview_Camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 112.0

    views = (
        ("blender-front.png", (85.0, -110.0, 72.0)),
        ("blender-back.png", (-85.0, 110.0, 72.0)),
    )
    for filename, eye in views:
        point_camera(camera, eye)
        scene.render.filepath = str(destination / filename)
        bpy.ops.render.render(write_still=True)
        print(f"Rendered {scene.render.filepath}")


if __name__ in {"__main__", "<run_path>"}:
    main()
