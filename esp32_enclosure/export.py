"""Blend and STL export."""

from __future__ import annotations

from pathlib import Path

import bpy


def _export_selected_stl(path: Path) -> None:
    """Export the current selection using Blender's available STL operator."""
    if hasattr(bpy.ops.wm, "stl_export"):
        bpy.ops.wm.stl_export(filepath=str(path), export_selected_objects=True)
    else:
        bpy.ops.export_mesh.stl(filepath=str(path), use_selection=True)


def export_outputs(enclosure, cover, plungers, output_dir: str):
    """Save the scene and one STL per independently printable part."""
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

    _export_selected_stl(stl_path)

    if cover is not None:
        bpy.ops.object.select_all(action="DESELECT")
        cover.select_set(True)
        bpy.context.view_layer.objects.active = cover
        _export_selected_stl(cover_stl_path)
    else:
        cover_stl_path = None
    button_paths = []
    for plunger in plungers:
        bpy.ops.object.select_all(action="DESELECT")
        plunger.select_set(True)
        bpy.context.view_layer.objects.active = plunger
        side = "left" if plunger.name.startswith("Left") else "right"
        button_path = destination / f"esp32_s3_touch_amoled_1_75_{side}_button.stl"
        _export_selected_stl(button_path)
        button_paths.append(button_path)
    return blend_path, stl_path, cover_stl_path, button_paths
