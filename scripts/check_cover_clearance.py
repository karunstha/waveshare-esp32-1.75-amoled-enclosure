"""Check contact or overlap between the assembled cover and main shell.

Usage: blender --background FILE.blend --python scripts/check_cover_clearance.py
The clip hooks should enter their slots without intersecting the tray walls.
"""

from __future__ import annotations

import bmesh
import bpy


shell = bpy.data.objects["ESP32_Display_Enclosure"]
cover = bpy.data.objects["Accessory_Flush_Snap_Cover"]
probe = cover.copy()
probe.data = cover.data.copy()
bpy.context.scene.collection.objects.link(probe)

modifier = probe.modifiers.new("Cover_Shell_Intersection", "BOOLEAN")
modifier.operation = "INTERSECT"
modifier.solver = "EXACT"
modifier.object = shell
bpy.context.view_layer.objects.active = probe
bpy.ops.object.modifier_apply(modifier=modifier.name)

bm = bmesh.new()
try:
    bm.from_mesh(probe.data)
    contact_faces = len(bm.faces)
    if bm.verts:
        xs = [v.co.x for v in bm.verts]
        ys = [v.co.y for v in bm.verts]
        zs = [v.co.z for v in bm.verts]
        bounds = (
            (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))
        )
    else:
        bounds = None
    print(
        f"COVER_CLEARANCE contact_faces={contact_faces}, bounds={bounds}"
    )
finally:
    bm.free()
    bpy.data.objects.remove(probe, do_unlink=True)

if contact_faces:
    raise SystemExit("The rear cover touches or intersects the enclosure.")
