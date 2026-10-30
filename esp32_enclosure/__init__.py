"""Parametric Blender enclosure for the Waveshare ESP32-S3-Touch-AMOLED-1.75.

Modules:

* ``config``      - every dimension, allowance, and feature switch
* ``patterns``    - pure-Python vent and hole-pattern maths
* ``primitives``  - Blender primitives and Boolean helpers
* ``display``     - display-seat cable reliefs
* ``accessory``   - rear component tray and flush snap cover
* ``fit_check``   - viewport-only hardware model for checking fit
* ``enclosure``   - assembles the main shell (``build_enclosure``)
* ``export``      - Blend and STL output
* ``cli``         - argument parsing and ``main``
"""
