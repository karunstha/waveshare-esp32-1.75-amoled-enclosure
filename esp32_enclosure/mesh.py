"""Mesh cleanup and materials."""

from __future__ import annotations

import bmesh
import bpy


def clean_mesh(obj, merge_distance: float = 1e-5) -> None:
    """Weld near-duplicate vertices and drop zero-area faces before export."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=merge_distance)
    bmesh.ops.dissolve_degenerate(bm, dist=merge_distance, edges=bm.edges[:])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def make_material():
    material = bpy.data.materials.new(name="Enclosure_Material")
    material.diffuse_color = (0.055, 0.075, 0.105, 1.0)
    material.metallic = 0.0
    material.roughness = 0.34
    return material


def make_dummy_material(name: str, color: tuple[float, float, float, float]):
    material = bpy.data.materials.new(name=name)
    material.diffuse_color = color
    material.metallic = 0.0
    material.roughness = 0.45
    return material
