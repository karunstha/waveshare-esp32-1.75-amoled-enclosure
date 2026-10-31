"""Two guided side plungers for the board's upper KEY1/KEY2 switches.

The parts are shown in their assembled positions. Each plunger is a separate
printable object. Install it from inside the shell before seating the board:
its shoulder is wider than the bore and keeps it from escaping through the
side wall. Its X reach is a configurable starting point; tune the tip against
the moving contact face on the real board after the vertical fit adjustment.
"""

from __future__ import annotations

from . import config as cfg
from .primitives import add_x_cylinder, subtract, unite


def build_side_switches(enclosure, front_y: float) -> list:
    """Union hollow guides to the shell and return the two loose plungers."""
    if not cfg.ENABLE_SIDE_SWITCH_BUTTONS:
        return []

    switch_y = front_y + cfg.SWITCH_CENTRE_FROM_FRONT
    outer_x = cfg.CASE_WIDTH / 2.0
    inner_x = cfg.SWITCH_GUIDE_INNER_X
    guide_end_x = outer_x - cfg.SIDE_WALL / 2.0
    guide_depth = guide_end_x - inner_x
    bore_end_x = outer_x + cfg.BOOLEAN_MARGIN
    tip_end_x = cfg.SWITCH_OUTER_FACE_X + cfg.SWITCH_REST_GAP
    shoulder_outer_x = inner_x
    shoulder_inner_x = inner_x - cfg.SWITCH_SHOULDER_LENGTH
    button_outer_x = outer_x - cfg.SWITCH_BUTTON_RECESS
    plungers = []

    for side, sign in (("Left", -1), ("Right", 1)):
        guide = add_x_cylinder(
            f"{side}_Switch_Guide",
            cfg.SWITCH_GUIDE_OUTER_DIAMETER,
            guide_depth,
            location=(sign * (inner_x + guide_end_x) / 2.0,
                      switch_y, cfg.SWITCH_CENTRE_Z),
        )
        unite(enclosure, guide)
        bore = add_x_cylinder(
            f"{side}_Switch_Bore",
            cfg.SWITCH_GUIDE_BORE_DIAMETER,
            bore_end_x - inner_x + cfg.BOOLEAN_MARGIN,
            location=(sign * (inner_x + bore_end_x - cfg.BOOLEAN_MARGIN) / 2.0,
                      switch_y, cfg.SWITCH_CENTRE_Z),
        )
        subtract(enclosure, bore)

        # The wider inner shoulder stops at the guide entrance. The small tip
        # projects beyond the guide toward the switch's contact face.
        shaft = add_x_cylinder(
            f"{side}_Switch_Plunger",
            cfg.SWITCH_PLUNGER_DIAMETER,
            button_outer_x - inner_x + 0.10,
            location=(sign * (inner_x - 0.05 + button_outer_x) / 2.0,
                      switch_y, cfg.SWITCH_CENTRE_Z),
        )
        shoulder = add_x_cylinder(
            f"{side}_Switch_Stop",
            cfg.SWITCH_SHOULDER_DIAMETER,
            cfg.SWITCH_SHOULDER_LENGTH + 0.10,
            location=(sign * (shoulder_inner_x + shoulder_outer_x - 0.10) / 2.0,
                      switch_y, cfg.SWITCH_CENTRE_Z),
        )
        unite(shaft, shoulder)
        tip = add_x_cylinder(
            f"{side}_Switch_Tip",
            cfg.SWITCH_TIP_DIAMETER,
            shoulder_inner_x - tip_end_x + 0.10,
            location=(sign * (tip_end_x + shoulder_inner_x + 0.10) / 2.0,
                      switch_y, cfg.SWITCH_CENTRE_Z),
        )
        unite(shaft, tip)
        shaft["switch_rest_gap_mm"] = cfg.SWITCH_REST_GAP
        shaft["assembly"] = "Insert from inside before installing the board"
        plungers.append(shaft)

    return plungers
