"""Generate the ESP32-S3 AMOLED enclosure and flush cover in Blender.

Run from Blender's Scripting workspace (Run Script), the VS Code Blender
Development extension, or the command line from the repository root:

    blender --background --python blender_enclosure.py -- --export

All dimensions are millimetres; edit ``esp32_enclosure/config.py`` to tune the
fit. The implementation lives in the ``esp32_enclosure`` package beside this
file. See docs/geometry.md for the source dimensions and tolerance assumptions.
"""

import sys
from pathlib import Path

import bpy


def _repository_root() -> Path:
    """Locate the repository even when run from Blender's text editor."""
    if "__file__" in globals():
        return Path(__file__).resolve().parent
    for text in bpy.data.texts:
        if text.filepath and text.name == "blender_enclosure.py":
            return Path(bpy.path.abspath(text.filepath)).resolve().parent
    return Path.cwd()


ROOT = _repository_root()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Re-running inside a live Blender session must pick up edited modules.
for _name in [name for name in sys.modules if name.split(".")[0] == "esp32_enclosure"]:
    del sys.modules[_name]

from esp32_enclosure.cli import main  # noqa: E402


# Blender's VS Code extension executes scripts with runpy.run_path(), which
# assigns the special module name "<run_path>" instead of "__main__".
if __name__ in {"__main__", "<run_path>"}:
    main()
