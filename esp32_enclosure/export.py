"""Blend and STL export."""

from __future__ import annotations

from pathlib import Path

import bpy


def export_outputs(enclosure, cover, output_dir: str):
    """Save the Blend scene and export only the two printable objects as STLs."""
    base_dir = Path(__file__).resolve().parents[1]
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
