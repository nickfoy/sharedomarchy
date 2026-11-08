#!/usr/bin/env python3
"""Start FreeCAD with Omarchy's current GNOME/GTK text scale applied to Qt."""
import math
import os
import subprocess
import sys

if 'QT_FONT_DPI' not in os.environ:
    try:
        scale = float(subprocess.check_output(
            ['gsettings', 'get', 'org.gnome.desktop.interface', 'text-scaling-factor'],
            text=True, stderr=subprocess.DEVNULL, timeout=3).strip())
        if math.isfinite(scale) and 0.25 <= scale <= 4:
            os.environ['QT_FONT_DPI'] = str(round(96 * scale))
    except (OSError, ValueError, subprocess.SubprocessError):
        pass  # Fall back to Qt's normal font settings if GNOME settings are absent.

os.execv('/usr/bin/FreeCAD', ['/usr/bin/FreeCAD', *sys.argv[1:]])
