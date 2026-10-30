"""Inspect printable objects in a generated .blend for open mesh edges.

Usage: blender --background FILE.blend --python scripts/inspect_mesh.py
"""

from __future__ import annotations

import bmesh
import bpy


failures = []
for obj in bpy.data.objects:
    if obj.type != "MESH" or obj.get("fit_check_only"):
        continue
    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        bad_edges = sum(1 for edge in bm.edges if not edge.is_manifold)
        # A closed but detached guide would still be manifold, so count mesh
        # islands as well. Each printable object should be one connected shell.
        unseen = set(bm.verts)
        islands = 0
        while unseen:
            islands += 1
            stack = [unseen.pop()]
            while stack:
                vertex = stack.pop()
                for edge in vertex.link_edges:
                    neighbour = edge.other_vert(vertex)
                    if neighbour in unseen:
                        unseen.remove(neighbour)
                        stack.append(neighbour)
        print(
            f"MESH_CHECK {obj.name}: {len(bm.verts)} vertices, "
            f"{len(bm.faces)} faces, {bad_edges} non-manifold edges, "
            f"{islands} island(s)"
        )
        if bad_edges or islands != 1:
            failures.append(obj.name)
    finally:
        bm.free()

if failures:
    raise SystemExit(f"Printable mesh check failed: {', '.join(failures)}")
