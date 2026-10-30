"""Scene, primitive, and Boolean helpers shared by the geometry builders."""

from __future__ import annotations

import math

import bpy

from . import config as cfg


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def set_units() -> None:
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "MILLIMETERS"
    scene.unit_settings.scale_length = 0.001


def add_box(name: str, size: tuple[float, float, float], location=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj


def add_y_cylinder(
    name: str,
    diameter: float,
    depth: float,
    location=(0, 0, 0),
    vertices: int = cfg.CYLINDER_VERTICES,
):
    """Add a cylinder whose axis follows Y (front-to-rear)."""
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=diameter / 2.0,
        depth=depth,
        location=location,
        rotation=(math.radians(90.0), 0.0, 0.0),
    )
    obj = bpy.context.object
    obj.name = name
    return obj


def add_y_ellipse(
    name: str,
    horizontal_diameter: float,
    vertical_diameter: float,
    depth: float,
    location=(0, 0, 0),
    vertices: int = cfg.CYLINDER_VERTICES,
):
    """Add a transform-normalized elliptical cylinder along global Y."""
    if horizontal_diameter <= 0 or vertical_diameter <= 0 or depth <= 0:
        raise ValueError("Ellipse dimensions must be positive.")
    obj = add_y_cylinder(
        name,
        horizontal_diameter,
        depth,
        location=location,
        vertices=vertices,
    )
    bpy.context.view_layer.objects.active = obj
    # Bake the 90-degree cylinder rotation first. Scaling Z before doing this
    # can elongate a local axis that Blender later maps into the cut depth,
    # producing malformed or unstable Boolean results.
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    obj.scale.z = vertical_diameter / horizontal_diameter
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj


def add_x_cylinder(
    name: str,
    diameter: float,
    depth: float,
    location=(0, 0, 0),
    vertices: int = cfg.CYLINDER_VERTICES,
):
    """Add a cylinder whose axis follows X."""
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=diameter / 2.0,
        depth=depth,
        location=location,
        rotation=(0.0, math.radians(90.0), 0.0),
    )
    obj = bpy.context.object
    obj.name = name
    return obj


def add_z_cylinder(
    name: str,
    diameter: float,
    depth: float,
    location=(0, 0, 0),
    vertices: int = cfg.CYLINDER_VERTICES,
):
    """Add a cylinder whose axis follows Z."""
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=diameter / 2.0,
        depth=depth,
        location=location,
    )
    obj = bpy.context.object
    obj.name = name
    return obj


def apply_bevel(obj, width: float, segments: int = 3) -> None:
    modifier = obj.modifiers.new(name="Edge_Softening", type="BEVEL")
    modifier.width = width
    modifier.segments = segments
    modifier.limit_method = "ANGLE"
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)


def configure_exact_boolean(modifier) -> None:
    """Make EXACT Booleans tolerate coplanar faces and touching shells.

    Without these options the many unions/cuts that land on the rear-wall plane
    leave edges shared by three faces, which slicers report as non-manifold.
    """
    if modifier.solver != "EXACT":
        return
    modifier.use_self = True
    modifier.use_hole_tolerant = True


def subtract(target, cutter, solver: str = "EXACT") -> None:
    modifier = target.modifiers.new(name=f"Cut_{cutter.name}", type="BOOLEAN")
    modifier.operation = "DIFFERENCE"
    try:
        modifier.solver = solver
    except TypeError:
        # Blender 5.x renamed the FAST solver to FLOAT.
        modifier.solver = "FLOAT" if solver == "FAST" else solver
    modifier.object = cutter
    configure_exact_boolean(modifier)
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


def subtract_many(target, cutters: list, name: str) -> None:
    """Join simple vent cutters and apply one fast Boolean operation."""
    if not cutters:
        return
    bpy.ops.object.select_all(action="DESELECT")
    for cutter in cutters:
        cutter.select_set(True)
    combined = cutters[0]
    bpy.context.view_layer.objects.active = combined
    bpy.ops.object.join()
    combined.name = name
    subtract(target, combined, solver="FAST")


def unite(target, addition) -> None:
    modifier = target.modifiers.new(name=f"Join_{addition.name}", type="BOOLEAN")
    modifier.operation = "UNION"
    modifier.solver = "EXACT"
    modifier.object = addition
    configure_exact_boolean(modifier)
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(addition, do_unlink=True)


def subtract_z_capsule(
    target,
    name: str,
    width: float,
    depth: float,
    cut_height: float,
    location: tuple[float, float, float],
) -> None:
    """Cut a rounded USB-style slot extruded along Z."""
    if width <= depth:
        raise ValueError("Capsule width must be greater than its depth.")
    x, y, z = location
    straight_length = width - depth
    center = add_box(
        f"{name}_Centre",
        (straight_length, depth, cut_height),
        location=(x, y, z),
    )
    subtract(target, center)
    for suffix, x_offset in (("Left", -straight_length / 2.0),
                             ("Right", straight_length / 2.0)):
        end = add_z_cylinder(
            f"{name}_{suffix}",
            depth,
            cut_height,
            location=(x + x_offset, y, z),
        )
        subtract(target, end)
