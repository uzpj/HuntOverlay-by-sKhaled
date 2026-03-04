# HuntOverlay.py
# Hunt Map Overlay By sKhaled
#
# Project overview
# This app is a click through, always on top overlay that draws POIs (points of interest)
# inside a user defined rectangle on the screen.
#
# Runtime folder
# All runtime files live in:
#   %LOCALAPPDATA%\HuntOverlay
#
# Seeded files on first run
#   data.json     POI coordinate dataset
#   poiData.json  style definitions for POI types
#   config.json   user settings, per map rect ratios, keybinds, hidden POIs
#
# Core behavior
#   Loads data.json and poiData.json from %LOCALAPPDATA%\HuntOverlay
#   Applies a screen rectangle per map based on detected aspect ratio
#   Draws POIs in that rectangle using normalized coordinates derived from a 4096x4096 grid
#
# New features in this version
#
# Hold to show overlay:
# Added a "Hold Tab to show overlay" checkbox in the panel.
# When enabled, the overlay is visible only while the toggle key is held.
# When disabled, the overlay uses the existing toggle behavior.
# The setting is persisted to config.json and reloads correctly after reset.
#
# Tab safety logic:
# The overlay toggle key (Tab by default) is ignored while Ctrl, Alt, or Shift
# are held. This prevents accidental overlay activation during combinations
# such as Alt+Tab, Ctrl+Tab, or Shift+Tab.
#
# Startup behavior and tray handling
# The application now starts minimized to the system tray if you have it set to start meinimized.
# Fresh configs default to tray-minimize disabled.
#
# Primary monitor enforcement
# The overlay window geometry is explicitly bound to QGuiApplication.primaryScreen().
# Each time the overlay is shown, geometry is re-applied to ensure it opens
# on the primary monitor.
#
# New POI type: brutes
# Added support for the "brutes" category:
# - Included in type order and drawing pass
# - Loaded from poiData.json like other styled categories ( Still Empty As Of Right Now )  
#
# Config version update
# Retained guard against invalid indexed map names (MAPS.index).
# Bumped CONFIG_VERSION to trigger migration to updated defaults and settings.


# Hide behavior note
# If you hide a POI while hovering possible_xp, it only hides it from possible_xp,
# not from its source category (armories, towers, big_towers).
# Hidden POIs are stored per category in config.json.

# Possible Future Update:
# Adding the ability to retain config settings through version updates.
import sys
from PySide6 import QtGui, QtWidgets

from HO.Static.Util import ICON

from HO.Overlay import Overlay


def main():
    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QApplication.setStyle("Fusion")

    # Consistent dark palette for the panel.
    pal = app.palette()
    for role, color in [
        (QtGui.QPalette.Window, QtGui.QColor(30, 31, 34)),
        (QtGui.QPalette.WindowText, QtGui.QColor(230, 230, 230)),
        (QtGui.QPalette.Base, QtGui.QColor(43, 45, 48)),
        (QtGui.QPalette.AlternateBase, QtGui.QColor(36, 38, 41)),
        (QtGui.QPalette.Text, QtGui.QColor(230, 230, 230)),
        (QtGui.QPalette.Button, QtGui.QColor(43, 45, 48)),
        (QtGui.QPalette.ButtonText, QtGui.QColor(230, 230, 230)),
        (QtGui.QPalette.Highlight, QtGui.QColor(90, 120, 200)),
        (QtGui.QPalette.HighlightedText, QtGui.QColor(255, 255, 255)),
    ]:
        pal.setColor(role, color)
    app.setPalette(pal)

    if ICON:
        app.setWindowIcon(QtGui.QIcon(ICON))

    try:
        w = Overlay()
    except Exception as e:
        QtWidgets.QMessageBox.critical(None, "HuntOverlay error", str(e))
        sys.exit(1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
