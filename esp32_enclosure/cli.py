"""Command-line entry point shared by the root script and Blender's text editor."""

from __future__ import annotations

import argparse
import sys

from . import config as cfg
from .enclosure import build_enclosure
from .export import export_outputs


def parse_args() -> argparse.Namespace:
    """Parse only arguments after Blender's conventional `--` separator."""
    user_args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(
        description="Generate the ESP32-S3 AMOLED enclosure in Blender."
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Export STL and save a .blend file after generation.",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help=(
            "Output directory used with --export. Relative paths resolve "
            "from the repository root (default: output)."
        ),
    )
    return parser.parse_args(user_args)


def main() -> None:
    args = parse_args()
    enclosure, cover = build_enclosure()
    internal_depth = cfg.CASE_DEPTH - cfg.FRONT_WALL - cfg.REAR_WALL
    print(
        "Created ESP32 enclosure: "
        f"{cfg.CASE_WIDTH:.1f} x {cfg.CASE_HEIGHT:.1f} x "
        f"{cfg.CASE_DEPTH:.1f} mm, "
        f"hollow {cfg.ENCLOSURE_THICKNESS:.2f} mm shell, "
        f"internal depth {internal_depth:.1f} mm, "
        f"display pocket {cfg.DISPLAY_POCKET_DIAMETER:.2f} x "
        f"{cfg.DISPLAY_POCKET_VERTICAL_DIAMETER:.2f} mm, "
        f"recess {cfg.DISPLAY_RECESS_DEPTH:.2f} mm, "
        f"board opening {cfg.BOARD_OPENING_DIAMETER:.2f} x "
        f"{cfg.BOARD_OPENING_VERTICAL_DIAMETER:.2f} mm."
    )
    if args.export:
        blend_path, stl_path, cover_stl_path = export_outputs(
            enclosure, cover, args.output_dir
        )
        print(f"Saved Blender file: {blend_path}")
        print(f"Exported STL: {stl_path}")
        if cover_stl_path is not None:
            print(f"Exported flush snap cover STL: {cover_stl_path}")
