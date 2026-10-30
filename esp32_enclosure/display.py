"""Display-seat helpers."""

from __future__ import annotations

from . import config as cfg
from .primitives import add_box, subtract


def cut_display_cable_reliefs(
    target,
    name_prefix: str,
    y: float,
    cut_depth: float,
    outer_diameter: float,
    inner_diameter: float,
    vertical_radius_compensation: float = 0.0,
) -> None:
    """Remove top, bottom, left, and right windows across the support band."""
    if not cfg.ENABLE_DISPLAY_CABLE_RELIEFS:
        return
    radial_band = (outer_diameter - inner_diameter) / 2.0
    relief_height = radial_band + 2 * cfg.BOOLEAN_MARGIN
    horizontal_relief_center = (outer_diameter + inner_diameter) / 4.0
    vertical_relief_center = (
        horizontal_relief_center + vertical_radius_compensation
    )
    for label, direction in (("Top", 1.0), ("Bottom", -1.0)):
        cutter = add_box(
            f"{name_prefix}_{label}_Cable_Relief",
            (cfg.DISPLAY_CABLE_RELIEF_WIDTH, cut_depth, relief_height),
            location=(0.0, y, direction * vertical_relief_center),
        )
        subtract(target, cutter)

    for label, direction in (("Left", -1.0), ("Right", 1.0)):
        cutter = add_box(
            f"{name_prefix}_{label}_Cable_Relief",
            (relief_height, cut_depth, cfg.DISPLAY_CABLE_RELIEF_WIDTH),
            location=(direction * horizontal_relief_center, y, 0.0),
        )
        subtract(target, cutter)
