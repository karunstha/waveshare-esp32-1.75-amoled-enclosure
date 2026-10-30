"""Blender-independent hole-pattern calculations."""

from __future__ import annotations

import math


def staggered_lattice_offsets(
    columns: int,
    rows: int,
    pitch: float,
) -> list[tuple[float, float]]:
    """Return a centered triangular lattice with alternating shorter rows."""
    offsets: list[tuple[float, float]] = []
    row_pitch = pitch * math.sqrt(3.0) / 2.0
    row_origin = (rows - 1) / 2.0
    for row in range(rows):
        row_columns = columns if row % 2 == 0 else max(1, columns - 1)
        column_origin = (row_columns - 1) / 2.0
        for column in range(row_columns):
            offsets.append(
                (
                    (column - column_origin) * pitch,
                    (row - row_origin) * row_pitch,
                )
            )
    return offsets


def honeycomb_rosette_offsets(pitch: float) -> list[tuple[float, float]]:
    """Return one center and six evenly spaced surrounding hole centres."""
    offsets = [(0.0, 0.0)]
    for index in range(6):
        angle = math.radians(index * 60.0)
        offsets.append((pitch * math.cos(angle), pitch * math.sin(angle)))
    return offsets
