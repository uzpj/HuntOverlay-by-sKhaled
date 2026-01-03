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
#   1) Config version gate
#      If config.json missing or version mismatch, it is replaced with a fresh default config.
#      Current config version: CONFIG_VERSION
#
#   2) Aspect aware rectangles
#      For each map, config stores rect_ratio_by_aspect:
#         "16:9", "21:9", "32:9"
#      On launch, the app detects the current screen aspect and uses the corresponding ratio.
#
#   3) GUI keybind editor
#      Keybinds can be changed from the GUI instead of editing config.json manually.
#
#   4) Default hidden possible_xp entries since they do not include xp as of the post malone event.
#      config.settings.hidden.possible_xp includes:
#         "armories:1508:2096" "
#         "big_towers:1320:3328"
#
#   5) Reset to default config button
#      A GUI button overwrites config.json with fresh defaults and reloads settings immediately.
#
#   6) Minimize to system tray
#      A GUI checkbox controls whether minimizing hides the panel into the system tray.
#
# Map order and numeric switching
# Map order is set to match release order as requested:
#   1 Stillwater Bayou
#   2 Lawson Delta
#   3 DeSalle
#   4 Mammon's Gulch
#
# Hotkeys
# All hotkeys are configurable via GUI.
# Default:
#   toggle_master        ` (backtick)
#   toggle_overlay       Tab
#   hide_overlay         H
#   map_1..map_4         1 2 3 4
#   hide_hovered         Ctrl Alt Shift Delete
#
# Hide behavior note
# If you hide a POI while hovering possible_xp, it only hides it from possible_xp,
# not from its source category (armories, towers, big_towers).
# Hidden POIs are stored per category in config.json.

import sys, os, json, ctypes, traceback, shutil
from PySide6 import QtCore, QtGui, QtWidgets

# Map order is intentionally set to the release order requested.
MAPS = ["Stillwater Bayou", "Lawson Delta", "DeSalle", "Mammon's Gulch"]

CONFIG_VERSION = "1.0.1"

user32 = ctypes.windll.user32
GetKey = user32.GetAsyncKeyState

# Win32 virtual key codes used by defaults and modifier detection.
VK_TAB = 0x09
VK_H = 0x48
VK_BT = 0xC0
VK1, VK2, VK3, VK4 = 0x31, 0x32, 0x33, 0x34

VK_ESC = 0x1B
VK_DELETE = 0x2E
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12

DEFAULT_HIDDEN_POSSIBLE_XP = [
    "armories:1508:2096",
    "big_towers:1320:3328",
]

def key(vk: int) -> bool:
    return (GetKey(vk) & 0x8000) != 0

def topmost(hwnd: int) -> None:
    try:
        user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x1 | 0x2 | 0x10 | 0x40)
    except:
        pass

def click_through(hwnd: int) -> None:
    try:
        style = user32.GetWindowLongW(hwnd, -20)
        user32.SetWindowLongW(hwnd, -20, style | 0x80000 | 0x80 | 0x8000000 | 0x20)
    except:
        pass

def bd() -> str:
    # Base directory used by bundled builds (PyInstaller _MEIPASS) and normal .py runs.
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))

def udir() -> str:
    # All runtime files live here.
    p = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "HuntOverlay")
    os.makedirs(p, exist_ok=True)
    return p

def ensure_user_file(filename: str) -> str:
    """
    Ensure a file exists in %LOCALAPPDATA%\\HuntOverlay by copying from:
      1) bundled resources (PyInstaller _MEIPASS)
      2) script folder (when running as .py)
    Returns the user file path.
    """
    dst = os.path.join(udir(), filename)
    if os.path.isfile(dst):
        return dst

    src1 = os.path.join(bd(), filename)
    src2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

    src = src1 if os.path.isfile(src1) else (src2 if os.path.isfile(src2) else "")
    if src:
        try:
            shutil.copyfile(src, dst)
        except:
            pass

    return dst

ICON = os.path.join(bd(), "myicon.ico") if os.path.isfile(os.path.join(bd(), "myicon.ico")) else ""
DATA_PATH = ensure_user_file("data.json")
STYLE_PATH = ensure_user_file("poiData.json")
CONFIG_PATH = os.path.join(udir(), "config.json")

def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: str, obj) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(obj, indent=2))
    except:
        pass

def q2rgb(c: QtGui.QColor):
    return [c.red(), c.green(), c.blue()]

def rgb2q(v, fallback=QtGui.QColor(255, 180, 80)) -> QtGui.QColor:
    try:
        r, g, b = v
        return QtGui.QColor(int(r), int(g), int(b))
    except:
        return QtGui.QColor(fallback)

def screenWH():
    g = QtGui.QGuiApplication.primaryScreen().geometry()
    return g.width(), g.height()

def detect_aspect_label(w: int, h: int) -> str:
    """
    Aspect bucketing
    32:9 if a >= 3.20
    21:9 if a >= 2.20
    else 16:9
    """
    if h <= 0:
        return "16:9"
    a = float(w) / float(h)
    if a >= 3.20:
        return "32:9"
    if a >= 2.20:
        return "21:9"
    return "16:9"

def default_rect_ratio_16_9():
    return {"rx": 0.30859375, "ry": 0.14583333333333334, "rw": 0.383984375, "rh": 0.6833333333333333}

def default_rect_ratio_21_9():
    return {"rx": 0.35625, "ry": 0.14722222222222223, "rw": 0.287109375, "rh": 0.6814814814814815}
def default_rect_ratio_32_9():
    return {"rx": 0.404296875, "ry": 0.14722222222222223, "rw": 0.191015625, "rh": 0.6791666666666667}

def default_rect_ratio_by_aspect():
    return {"16:9": default_rect_ratio_16_9(), "21:9": default_rect_ratio_21_9(), "32:9": default_rect_ratio_32_9()}

def default_keybinds():
    """
    Keybind schema is stored under settings.keybinds
    Each action is a dict:
      vk: int virtual key code
      ctrl alt shift: optional booleans for modifier gated binds
    Only hide_hovered uses modifiers by default.
    """
    return {
        "toggle_master": {"vk": VK_BT},
        "toggle_overlay": {"vk": VK_TAB},
        "hide_overlay": {"vk": VK_H},
        "map_1": {"vk": VK1},
        "map_2": {"vk": VK2},
        "map_3": {"vk": VK3},
        "map_4": {"vk": VK4},
        "hide_hovered": {"vk": VK_DELETE, "ctrl": True, "alt": True, "shift": True},
    }

def vk_to_label(vk: int) -> str:
    if vk == VK_TAB: return "Tab"
    if vk == VK_BT: return "`"
    if vk == VK_DELETE: return "Delete"
    if vk == VK_SHIFT: return "Shift"
    if vk == VK_CONTROL: return "Ctrl"
    if vk == VK_MENU: return "Alt"
    if 0x30 <= vk <= 0x39: return chr(vk)
    if 0x41 <= vk <= 0x5A: return chr(vk)
    if vk == VK_ESC: return "Esc"
    return f"VK_{vk}"

def rotate90cw_norm(x, y):
    """
    Converts 4096 map coordinates into normalized u,v (0..1) after 90° clockwise rotation.
    v is top down for painting.
    """
    xr = float(y)
    yr = 4095.0 - float(x)
    u = xr / 4095.0
    v = yr / 4095.0
    if u < 0: u = 0.0
    if u > 1: u = 1.0
    if v < 0: v = 0.0
    if v > 1: v = 1.0
    return u, v

def detect_data_format(game_data) -> str:
    """
    Supports two formats
    indexed_r: list of dicts with "i" map index and "r" categories
    named: list of dicts with "n" map name and direct category arrays
    """
    if isinstance(game_data, list) and game_data:
        a = game_data[0]
        if isinstance(a, dict) and "i" in a and ("r" in a or "a" in a):
            return "indexed_r"
        if isinstance(a, dict) and "n" in a:
            return "named"
    return "unknown"

def get_map_block(game_data, fmt: str, map_name: str):
    if fmt == "named":
        for m in game_data:
            if isinstance(m, dict) and m.get("n") == map_name:
                return m
        return None

    if fmt == "indexed_r":
        idx = MAPS.index(map_name)
        for m in game_data:
            if isinstance(m, dict) and m.get("i") == idx:
                return m
        return None

    return None

def get_category_list(map_block, fmt: str, category: str):
    if not isinstance(map_block, dict):
        return []
    if fmt == "named":
        v = map_block.get(category, [])
        return v if isinstance(v, list) else []
    if fmt == "indexed_r":
        r = map_block.get("r", {})
        if isinstance(r, dict):
            v = r.get(category, [])
            return v if isinstance(v, list) else []
        return []
    return []

def find_style_by_category(style_json, category: str):
    if not isinstance(style_json, dict):
        return None
    for _, spec in style_json.items():
        if isinstance(spec, dict) and spec.get("categories") == category:
            return spec
    return None

def qcolor_from_any(value, fallback: QtGui.QColor) -> QtGui.QColor:
    try:
        c = QtGui.QColor(str(value))
        return c if c.isValid() else QtGui.QColor(fallback)
    except:
        return QtGui.QColor(fallback)

def overlay_radius_from_spec(spec_radius) -> int:
    """
    Converts poiData.json radius into a stable on screen radius baseline.
    """
    try:
        r = float(spec_radius)
    except:
        r = 12.0
    px = int(round(r * 0.25))
    if px < 3: px = 3
    if px > 10: px = 10
    return px

def build_default_config():
    profiles = {}
    for m in MAPS:
        profiles[m] = {"rect_ratio_by_aspect": default_rect_ratio_by_aspect()}
    return {
        "version": CONFIG_VERSION,
        "profiles": profiles,
        "settings": {
            "enable_num_switch": True,
            "selected_map": MAPS[0],
            "visible_overlay": False,
            "master_on": True,
            "global_scale": 1.00,
            "minimize_to_tray": False,
            "keybinds": default_keybinds(),
            "types": {},
            "hidden": {"possible_xp": list(DEFAULT_HIDDEN_POSSIBLE_XP)},
        },
    }

def load_or_replace_config():
    """
    Option C
    If config.json missing OR version mismatch, replace with a fresh default config.
    """
    if not os.path.isfile(CONFIG_PATH):
        d = build_default_config()
        save_json(CONFIG_PATH, d)
        return d

    try:
        d = load_json(CONFIG_PATH)
    except:
        d = {}

    if not isinstance(d, dict) or d.get("version") != CONFIG_VERSION:
        d = build_default_config()
        save_json(CONFIG_PATH, d)
        return d

    return d

class KeyCaptureDialog(QtWidgets.QDialog):
    """
    Small capture dialog that polls GetAsyncKeyState and records one non modifier key press.
    Ctrl Alt Shift are captured and returned too.
    Esc cancels.
    """
    def __init__(self, action_name: str, p=None):
        super().__init__(p)
        self.setWindowTitle(f"Set keybind: {action_name}")
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)

        self.result_bind = None

        v = QtWidgets.QVBoxLayout(self)
        lbl = QtWidgets.QLabel("Press a key now\nCtrl Alt Shift are captured too\nEsc cancels")
        lbl.setAlignment(QtCore.Qt.AlignCenter)
        v.addWidget(lbl)

        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._timer.start(10)

        self._prev_down = set()

    def _poll(self):
        if key(VK_ESC):
            self.reject()
            return

        mods = {"ctrl": key(VK_CONTROL), "alt": key(VK_MENU), "shift": key(VK_SHIFT)}

        down = set()
        for vk in range(1, 256):
            if key(vk):
                down.add(vk)

        new_down = [vk for vk in down if vk not in self._prev_down]
        self._prev_down = down

        for vk in new_down:
            if vk in (VK_CONTROL, VK_MENU, VK_SHIFT):
                continue
            self.result_bind = {"vk": int(vk), "ctrl": bool(mods["ctrl"]), "alt": bool(mods["alt"]), "shift": bool(mods["shift"])}
            self.accept()
            return

class SVPad(QtWidgets.QWidget):
    changed = QtCore.Signal(int, int)
    def __init__(self, p=None):
        super().__init__(p)
        self.setMinimumSize(180, 140)
        self.h = 255
        self.s = 255
        self.v = 255
        self.cross = QtCore.QPointF(0, 0)

    def setHue(self, h: int):
        self.h = max(0, min(359, int(h)))
        self.update()

    def setSV(self, sv: int, vv: int):
        self.s = max(0, min(255, int(sv)))
        self.v = max(0, min(255, int(vv)))
        self.cross = QtCore.QPointF(self.s / 255 * self.width(), (1 - self.v / 255) * self.height())
        self.update()

    def mousePressEvent(self, e):
        self._hit(e)

    def mouseMoveEvent(self, e):
        self._hit(e)

    def _hit(self, e):
        x = max(0, min(self.width(), e.position().x()))
        y = max(0, min(self.height(), e.position().y()))
        S = int(round(x / max(1, self.width()) * 255))
        V = int(round((1 - y / max(1, self.height())) * 255))
        if S != self.s or V != self.v:
            self.setSV(S, V)
            self.changed.emit(self.s, self.v)

    def paintEvent(self, _):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        hc = QtGui.QColor()
        hc.setHsv(self.h, 255, 255)
        g = QtGui.QLinearGradient(0, 0, self.width(), 0)
        g.setColorAt(0, QtGui.QColor(255, 255, 255))
        g.setColorAt(1, hc)
        p.fillRect(self.rect(), g)
        g2 = QtGui.QLinearGradient(0, 0, 0, self.height())
        g2.setColorAt(0, QtGui.QColor(0, 0, 0, 0))
        g2.setColorAt(1, QtGui.QColor(0, 0, 0, 255))
        p.fillRect(self.rect(), g2)
        p.setPen(QtGui.QPen(QtGui.QColor(240, 240, 240), 1))
        p.drawEllipse(self.cross, 5, 5)
        p.setPen(QtGui.QPen(QtGui.QColor(20, 20, 20), 1))
        p.drawEllipse(self.cross, 3, 3)

class AdvColorDlg(QtWidgets.QDialog):
    def __init__(self, start: QtGui.QColor, p=None):
        super().__init__(p)
        self.setWindowTitle("Pick Color")
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)
        self.setStyleSheet(
            "QWidget{background:#1e1f22;color:#e6e6e6;}"
            "QSlider::groove:horizontal{height:6px;background:#2b2d30;}"
            "QSlider::handle:horizontal{width:12px;background:#90a0ff;margin:-6px 0;border-radius:3px;}"
            "QSpinBox,QLineEdit{background:#2b2d30;color:#e6e6e6;border:1px solid #3a3c40;}"
            "QPushButton{background:#2b2d30;border:1px solid #3a3c40;padding:4px 10px;}"
            "QPushButton:hover{background:#34363a;}"
        )
        self.pad = SVPad(self)
        self.h = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.h.setRange(0, 359)
        self.r = QtWidgets.QSpinBox()
        self.g = QtWidgets.QSpinBox()
        self.b = QtWidgets.QSpinBox()
        for sp in (self.r, self.g, self.b):
            sp.setRange(0, 255)
        self.hex = QtWidgets.QLineEdit()
        self.hex.setMaxLength(7)
        self.hex.setPlaceholderText("#RRGGBB")
        self.prev = QtWidgets.QLabel()
        self.prev.setFixedSize(48, 48)
        self.prev.setFrameShape(QtWidgets.QFrame.Panel)
        self.prev.setFrameShadow(QtWidgets.QFrame.Sunken)

        presets = [
            "#ffffff", "#000000", "#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff", "#00ffff",
            "#ffa500", "#ffc107", "#795548", "#9e9e9e", "#607d8b", "#8bc34a", "#3f51b5", "#e91e63"
        ]
        grid = QtWidgets.QGridLayout()
        for i, hx in enumerate(presets):
            b = QtWidgets.QPushButton()
            b.setFixedSize(20, 20)
            b.setStyleSheet(f"border:1px solid #3a3c40;background:{hx};")
            b.clicked.connect(lambda _, h=hx: self._set_hex(h))
            grid.addWidget(b, i // 8, i % 8)

        def row(lbl, spin):
            h = QtWidgets.QHBoxLayout()
            h.addWidget(QtWidgets.QLabel(lbl))
            h.addWidget(spin)
            return h

        v = QtWidgets.QVBoxLayout(self)
        v.addWidget(self.pad)
        v.addWidget(QtWidgets.QLabel("Hue"))
        v.addWidget(self.h)
        rgb = QtWidgets.QHBoxLayout()
        rgb.addLayout(row("R", self.r))
        rgb.addLayout(row("G", self.g))
        rgb.addLayout(row("B", self.b))
        v.addLayout(rgb)
        hh = QtWidgets.QHBoxLayout()
        hh.addWidget(QtWidgets.QLabel("Hex"))
        hh.addWidget(self.hex)
        hh.addStretch(1)
        hh.addWidget(self.prev)
        v.addLayout(hh)
        v.addWidget(QtWidgets.QLabel("Presets"))
        v.addLayout(grid)
        bt = QtWidgets.QHBoxLayout()
        ok = QtWidgets.QPushButton("OK")
        ca = QtWidgets.QPushButton("Cancel")
        bt.addStretch(1)
        bt.addWidget(ok)
        bt.addWidget(ca)
        v.addLayout(bt)

        self.h.valueChanged.connect(self._h_changed)
        self.pad.changed.connect(self._sv_changed)
        self.r.valueChanged.connect(self._rgb_changed)
        self.g.valueChanged.connect(self._rgb_changed)
        self.b.valueChanged.connect(self._rgb_changed)
        self.hex.editingFinished.connect(self._hex_changed)
        ok.clicked.connect(self.accept)
        ca.clicked.connect(self.reject)

        self._lock = False
        self._from_color(start)

    def _preview(self, c: QtGui.QColor):
        self.prev.setStyleSheet(f"background: rgb({c.red()},{c.green()},{c.blue()}); border:1px solid #3a3c40;")

    def _set_hex(self, hx: str):
        c = QtGui.QColor(hx if hx.startswith("#") else "#" + hx)
        if c.isValid():
            self._from_color(c)

    def _hex_changed(self):
        self._set_hex(self.hex.text().strip())

    def _h_changed(self, h: int):
        if self._lock:
            return
        self._lock = True
        self.pad.setHue(h)
        self._sync_rgb_hex(self.selectedColor())
        self._lock = False

    def _sv_changed(self, S: int, V: int):
        if self._lock:
            return
        self._lock = True
        c = QtGui.QColor()
        c.setHsv(self.h.value(), S, V)
        self._sync_rgb_hex(c)
        self._lock = False

    def _rgb_changed(self, _=None):
        if self._lock:
            return
        self._lock = True
        c = QtGui.QColor(self.r.value(), self.g.value(), self.b.value())
        h, S, V, _a = c.getHsv()
        h = max(0, h)
        self.h.setValue(h)
        self.pad.setHue(h)
        self.pad.setSV(S, V)
        self._sync_hex_only(c)
        self._lock = False

    def _sync_rgb_hex(self, c: QtGui.QColor):
        self._preview(c)
        self.hex.setText("#{0:02x}{1:02x}{2:02x}".format(c.red(), c.green(), c.blue()))
        self.r.setValue(c.red())
        self.g.setValue(c.green())
        self.b.setValue(c.blue())

    def _sync_hex_only(self, c: QtGui.QColor):
        self._preview(c)
        self.hex.setText("#{0:02x}{1:02x}{2:02x}".format(c.red(), c.green(), c.blue()))

    def _from_color(self, c: QtGui.QColor):
        h, S, V, _a = c.getHsv()
        h = max(0, h)
        self._lock = True
        self.h.setValue(h)
        self.pad.setHue(h)
        self.pad.setSV(S, V)
        self._sync_rgb_hex(c)
        self._lock = False

    def selectedColor(self) -> QtGui.QColor:
        c = QtGui.QColor()
        c.setHsv(self.h.value(), self.pad.s, self.pad.v)
        return c

class DotChip(QtWidgets.QPushButton):
    changed = QtCore.Signal(QtGui.QColor)
    def __init__(self, fill: QtGui.QColor, border=QtGui.QColor(85, 85, 85), p=None):
        super().__init__(p)
        self.fill = QtGui.QColor(fill)
        self.border = QtGui.QColor(border)
        self.setFixedSize(20, 20)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.clicked.connect(self.pick)
        self._paint()

    def _paint(self):
        f = self.fill
        b = self.border
        self.setStyleSheet(
            "QPushButton{"
            f"border:2px solid rgb({b.red()},{b.green()},{b.blue()});"
            "border-radius:10px;"
            f"background: rgb({f.red()},{f.green()},{f.blue()});"
            "}"
            "QPushButton:hover{filter:brightness(1.05);}"
        )

    def setFill(self, c: QtGui.QColor):
        self.fill = QtGui.QColor(c)
        self._paint()
        self.changed.emit(self.fill)

    def pick(self):
        d = AdvColorDlg(self.fill, self)
        if ICON:
            d.setWindowIcon(QtGui.QIcon(ICON))
        if d.exec() == QtWidgets.QDialog.Accepted:
            self.setFill(d.selectedColor())

class Panel(QtWidgets.QWidget):
    mapSel = QtCore.Signal(str)
    tnums = QtCore.Signal(bool)
    resetColors = QtCore.Signal()
    typeToggled = QtCore.Signal(str, bool)
    typeColor = QtCore.Signal(str, QtGui.QColor)
    scaleChanged = QtCore.Signal(float)

    requestBindEdit = QtCore.Signal(str)
    resetConfig = QtCore.Signal()
    minimizeToTrayChanged = QtCore.Signal(bool)

    def __init__(self, type_order, type_specs, start_scale: float, help_text: str, binds_label_map: dict, start_min_to_tray: bool, p=None):
        super().__init__(p, QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowTitle("Hunt Map Overlay By sKhaled")
        self.setFixedWidth(360)
        self.setStyleSheet(
            "QWidget{background:#1e1f22;color:#e6e6e6;}"
            "QComboBox,QLineEdit,QSpinBox,QDoubleSpinBox{background:#2b2d30;color:#e6e6e6;border:1px solid #3a3c40;}"
            "QPushButton{background:#2b2d30;border:1px solid #3a3c40;padding:4px 8px;}"
            "QPushButton:hover{background:#34363a;}"
            "QLabel{color:#cfd1d4;}"
            "QCheckBox{spacing:10px;}"
            "QCheckBox::indicator{width:16px;height:16px;}"
        )

        self.type_widgets = {}
        v = QtWidgets.QVBoxLayout(self)

        title = QtWidgets.QLabel("POI Types")
        f = title.font()
        f.setBold(True)
        title.setFont(f)
        v.addWidget(title)

        for tkey in type_order:
            spec = type_specs[tkey]
            chk = QtWidgets.QCheckBox(spec["label"])
            chip = DotChip(spec["default_fill"], spec["border"])
            row = QtWidgets.QHBoxLayout()
            row.addWidget(chk)
            row.addStretch(1)
            row.addWidget(chip)
            v.addLayout(row)
            self.type_widgets[tkey] = (chk, chip)
            chk.toggled.connect(lambda val, k=tkey: self.typeToggled.emit(k, val))
            chip.changed.connect(lambda col, k=tkey: self.typeColor.emit(k, col))

            if tkey == "possible_xp":
                line = QtWidgets.QFrame()
                line.setFrameShape(QtWidgets.QFrame.HLine)
                line.setFrameShadow(QtWidgets.QFrame.Sunken)
                line.setStyleSheet("color:#2b2d30;background:#2b2d30;max-height:1px;")
                v.addWidget(line)

        v.addSpacing(6)

        self.chk_nums = QtWidgets.QCheckBox("Enable 1 to 4 Map Switch")
        v.addWidget(self.chk_nums)
        self.chk_nums.toggled.connect(self.tnums)

        v.addWidget(QtWidgets.QLabel("Map:"))
        self.cmb = QtWidgets.QComboBox()
        self.cmb.addItems(MAPS)
        v.addWidget(self.cmb)
        self.cmb.currentTextChanged.connect(self.mapSel)

        v.addSpacing(6)

        v.addWidget(QtWidgets.QLabel("POI Size Scale (global):"))
        scale_row = QtWidgets.QHBoxLayout()
        self.btn_dec = QtWidgets.QPushButton("Smaller")
        self.btn_inc = QtWidgets.QPushButton("Bigger")
        self.scale_box = QtWidgets.QDoubleSpinBox()
        self.scale_box.setRange(0.10, 5.00)
        self.scale_box.setDecimals(2)
        self.scale_box.setSingleStep(0.05)
        self.scale_box.setValue(float(start_scale))
        self.scale_box.setFixedWidth(90)

        scale_row.addWidget(self.btn_dec)
        scale_row.addWidget(self.btn_inc)
        scale_row.addStretch(1)
        scale_row.addWidget(self.scale_box)
        v.addLayout(scale_row)

        self.btn_dec.clicked.connect(self._dec_scale)
        self.btn_inc.clicked.connect(self._inc_scale)
        self.scale_box.valueChanged.connect(lambda x: self.scaleChanged.emit(float(x)))

        v.addSpacing(6)

        self.btn_def_colors = QtWidgets.QPushButton("Default Colors")
        v.addWidget(self.btn_def_colors)
        self.btn_def_colors.clicked.connect(self.resetColors)

        v.addSpacing(8)

        kb_title = QtWidgets.QLabel("Keybinds")
        f2 = kb_title.font()
        f2.setBold(True)
        kb_title.setFont(f2)
        v.addWidget(kb_title)

        self.kb_rows = {}
        for action, label in binds_label_map.items():
            row = QtWidgets.QHBoxLayout()
            row.addWidget(QtWidgets.QLabel(label))
            row.addStretch(1)
            btn = QtWidgets.QPushButton("Set")
            btn.setFixedWidth(60)
            row.addWidget(btn)
            v.addLayout(row)
            self.kb_rows[action] = btn
            btn.clicked.connect(lambda _, a=action: self.requestBindEdit.emit(a))

        v.addSpacing(8)

        self.chk_tray = QtWidgets.QCheckBox("Minimize to system tray")
        self.chk_tray.setChecked(bool(start_min_to_tray))
        v.addWidget(self.chk_tray)
        self.chk_tray.toggled.connect(lambda b: self.minimizeToTrayChanged.emit(bool(b)))

        v.addSpacing(6)

        self.btn_reset_cfg = QtWidgets.QPushButton("Reset to Default Config")
        v.addWidget(self.btn_reset_cfg)
        self.btn_reset_cfg.clicked.connect(self.resetConfig)

        v.addSpacing(8)

        v.addWidget(QtWidgets.QLabel("Controls"))
        self.help = QtWidgets.QTextEdit()
        self.help.setReadOnly(True)
        self.help.setFixedHeight(210)
        self.help.setStyleSheet("QTextEdit{background:#202225;border:1px solid #3a3c40;}")
        self.help.setText(help_text)
        v.addWidget(self.help)

        v.addStretch(1)

    def _dec_scale(self):
        self.scale_box.setValue(max(self.scale_box.minimum(), self.scale_box.value() - 0.05))

    def _inc_scale(self):
        self.scale_box.setValue(min(self.scale_box.maximum(), self.scale_box.value() + 0.05))

    def setTypeState(self, tkey: str, enabled: bool, fill_color: QtGui.QColor):
        chk, chip = self.type_widgets[tkey]
        chk.blockSignals(True)
        chip.blockSignals(True)
        chk.setChecked(bool(enabled))
        chip.setFill(fill_color)
        chip.blockSignals(False)
        chk.blockSignals(False)

    def setMap(self, name: str):
        i = self.cmb.findText(name)
        if i >= 0:
            self.cmb.blockSignals(True)
            self.cmb.setCurrentIndex(i)
            self.cmb.blockSignals(False)

    def setHelpText(self, txt: str):
        self.help.setText(txt)

class Overlay(QtWidgets.QWidget):
    def __init__(self):
        super().__init__(None, QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setMouseTracking(False)
        self.showFullScreen()

        if ICON:
            QtWidgets.QApplication.instance().setWindowIcon(QtGui.QIcon(ICON))
            self.setWindowIcon(QtGui.QIcon(ICON))

        if not os.path.isfile(DATA_PATH):
            raise RuntimeError(f"Missing data.json in {udir()}")
        if not os.path.isfile(STYLE_PATH):
            raise RuntimeError(f"Missing poiData.json in {udir()}")

        self.game_data = load_json(DATA_PATH)
        self.fmt = detect_data_format(self.game_data)
        if self.fmt == "unknown":
            raise RuntimeError("Unrecognized data.json format")

        self.poi_style = load_json(STYLE_PATH)

        # Order of types controls draw order and GUI ordering.
        self.type_order = [
            "possible_xp",
            "spawns",
            "armories",
            "towers",
            "big_towers",
            "workbenches",
            "wild_targets",
            "beetles",
            "easter_eggs",
            "melee_weapons",
            "cash_registers",
        ]

        self.type_specs = self._build_type_specs()

        W, H = screenWH()
        self.aspect = detect_aspect_label(W, H)

        self.data = load_or_replace_config()
        self._load_state_from_config(self.data)

        # Build the panel window.
        binds_label_map = {
            "toggle_master": "Toggle master",
            "toggle_overlay": "Toggle overlay",
            "hide_overlay": "Hide overlay",
            "map_1": "Map 1  Stillwater",
            "map_2": "Map 2  Lawson",
            "map_3": "Map 3  DeSalle",
            "map_4": "Map 4  Mammon",
            "hide_hovered": "Hide hovered POI",
        }
        help_text = self._build_help_text()
        self.panel = Panel(self.type_order, self.type_specs, self.global_scale, help_text, binds_label_map, self.minimize_to_tray)
        if ICON:
            self.panel.setWindowIcon(QtGui.QIcon(ICON))

        # Wire GUI events.
        self.panel.tnums.connect(self._set_num_switch)
        self.panel.mapSel.connect(self.switch)
        self.panel.resetColors.connect(self._reset_colors)
        self.panel.typeToggled.connect(self._type_toggle)
        self.panel.typeColor.connect(self._type_color)
        self.panel.scaleChanged.connect(self._scale_changed)
        self.panel.requestBindEdit.connect(self._edit_keybind)
        self.panel.resetConfig.connect(self._reset_config_to_defaults)
        self.panel.minimizeToTrayChanged.connect(self._set_minimize_to_tray)

        # Seed GUI with current state.
        self.panel.chk_nums.setChecked(self.num_sw)
        self.panel.setMap(self.prof)
        for k in self.type_order:
            self.panel.setTypeState(k, self.types[k]["enabled"], rgb2q(self.types[k]["color"], self.type_specs[k]["default_fill"]))

        self.panel.move(40, 40)
        self.panel.show()

        # System tray setup.
        self.tray = None
        self._ensure_tray()

        # Make overlay click through and topmost.
        click_through(int(self.winId()))
        (self.show if self.visible and self.master else self.hide)()
        topmost(int(self.winId()))

        # Edge detection for hotkeys so they do not toggle repeatedly while held.
        self.p_toggle_master = False
        self.p_hide = False
        self.p_toggle_overlay = False
        self.p_hide_hovered = False

        # Hover state is computed each tick when visible.
        self.hover = None
        self.hover_radius = 10

        # Cache computed point lists per map to avoid rebuilding every frame.
        self.cache = {}
        self._rebuild_all_caches()

        # Save once at the end to ensure config contains any missing keys we added.
        self._save()

        # Timer tick drives input polling and hover updates.
        self.t = QtCore.QTimer(self)
        self.t.timeout.connect(self._tick_safe)
        self.t.start(16)

        # Minimize to tray needs access to the panel state changes.
        self.panel.installEventFilter(self)

    def eventFilter(self, obj, ev):
        if obj is self.panel:
            if ev.type() == QtCore.QEvent.WindowStateChange:
                if self.minimize_to_tray and self.panel.isMinimized():
                    self._hide_panel_to_tray()
                    return True
        return super().eventFilter(obj, ev)

    def _ensure_tray(self):
        """
        Creates tray icon and menu once.
        Tray is only used when minimize_to_tray is enabled, but we keep it available.
        """
        if self.tray is not None:
            return

        self.tray = QtWidgets.QSystemTrayIcon(self)
        if ICON:
            self.tray.setIcon(QtGui.QIcon(ICON))
        else:
            self.tray.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon))

        menu = QtWidgets.QMenu()
        act_restore = QtGui.QAction("Restore panel", menu)
        act_quit = QtGui.QAction("Quit", menu)
        menu.addAction(act_restore)
        menu.addSeparator()
        menu.addAction(act_quit)

        act_restore.triggered.connect(self._restore_panel_from_tray)
        act_quit.triggered.connect(QtWidgets.QApplication.quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

    def _tray_activated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.Trigger:
            self._restore_panel_from_tray()

    def _hide_panel_to_tray(self):
        self._ensure_tray()
        self.panel.hide()
        self.panel.setWindowState(QtCore.Qt.WindowNoState)
        try:
            self.tray.showMessage("HuntOverlay", "Panel minimized to tray", QtWidgets.QSystemTrayIcon.Information, 1500)
        except:
            pass

    def _restore_panel_from_tray(self):
        self.panel.showNormal()
        self.panel.raise_()
        self.panel.activateWindow()

    def _set_minimize_to_tray(self, v: bool):
        self.minimize_to_tray = bool(v)
        self._save()

    def _build_type_specs(self):
        specs = {}

        # possible_xp is a special union category.
        specs["possible_xp"] = {
            "label": "Possible XP Location",
            "border": QtGui.QColor("#FFFFFF"),
            "default_fill": QtGui.QColor("#FFD34D"),
            "radius_px": 6,
        }

        def add_from_style(category, fallback_label):
            spec = find_style_by_category(self.poi_style, category) or {}
            label = spec.get("label", fallback_label)
            border = qcolor_from_any(spec.get("borderColor", "#555555"), QtGui.QColor("#555555"))
            fill = qcolor_from_any(spec.get("fillColor", "#B4B4B4"), QtGui.QColor("#B4B4B4"))
            radius_px = overlay_radius_from_spec(spec.get("radius", 12))
            specs[category] = {"label": str(label), "border": border, "default_fill": fill, "radius_px": radius_px}

        add_from_style("spawns", "Spawns")
        add_from_style("armories", "Armories")
        add_from_style("towers", "Hunting Towers")
        add_from_style("big_towers", "Watch Towers")
        add_from_style("workbenches", "Workbenches")
        add_from_style("wild_targets", "Wild Targets")
        add_from_style("beetles", "Beetles")
        add_from_style("easter_eggs", "Easter Eggs")
        add_from_style("melee_weapons", "Melee Weapons")
        add_from_style("cash_registers", "Cash Registers")

        return specs

    def _normalize_keybinds(self, binds: dict) -> dict:
        """
        Merges config keybinds with defaults and forces correct types.
        Unknown keys are ignored.
        """
        base = default_keybinds()
        merged = {k: dict(v) for k, v in base.items()}

        if isinstance(binds, dict):
            for k, v in binds.items():
                if k not in merged:
                    continue
                if not isinstance(v, dict):
                    continue
                for kk, vv in v.items():
                    merged[k][kk] = vv

        for k, v in merged.items():
            try:
                v["vk"] = int(v.get("vk", base[k]["vk"]))
            except:
                v["vk"] = int(base[k]["vk"])

            if k == "hide_hovered":
                v["ctrl"] = bool(v.get("ctrl", True))
                v["alt"] = bool(v.get("alt", True))
                v["shift"] = bool(v.get("shift", True))

        return merged

    def _load_state_from_config(self, d: dict):
        """
        Loads stateful runtime fields from the config dict.
        This is used at startup and after a full reset to default config.
        """
        st = d.get("settings", {}) if isinstance(d, dict) else {}
        if not isinstance(st, dict):
            st = {}

        self.num_sw = bool(st.get("enable_num_switch", True))
        sel = st.get("selected_map", MAPS[0])
        self.prof = sel if sel in MAPS else MAPS[0]
        self.visible = bool(st.get("visible_overlay", False))
        self.master = bool(st.get("master_on", True))

        self.global_scale = float(st.get("global_scale", 1.00))
        if self.global_scale < 0.10: self.global_scale = 0.10
        if self.global_scale > 5.00: self.global_scale = 5.00

        self.minimize_to_tray = bool(st.get("minimize_to_tray", False))

        self.binds = self._normalize_keybinds(st.get("keybinds", {}))

        # Per type settings.
        self.types = st.get("types", {})
        if not isinstance(self.types, dict):
            self.types = {}
        for k in self.type_order:
            if k not in self.types or not isinstance(self.types.get(k), dict):
                self.types[k] = {"enabled": True, "color": q2rgb(self.type_specs[k]["default_fill"])}
            if "enabled" not in self.types[k]:
                self.types[k]["enabled"] = True
            if "color" not in self.types[k]:
                self.types[k]["color"] = q2rgb(self.type_specs[k]["default_fill"])

        # Hidden lists.
        self.hidden = st.get("hidden", {})
        if not isinstance(self.hidden, dict):
            self.hidden = {}
        for k in self.type_order:
            if k not in self.hidden or not isinstance(self.hidden.get(k), list):
                self.hidden[k] = []

        # Ensure default hidden possible_xp entries exist.
        px = self.hidden.get("possible_xp", [])
        if not isinstance(px, list):
            px = []
        for s in DEFAULT_HIDDEN_POSSIBLE_XP:
            if s not in px:
                px.append(s)
        self.hidden["possible_xp"] = px

        self.hidden_sets = {k: set(self.hidden.get(k, [])) for k in self.type_order}

        # Apply aspect aware rect.
        self.rect = None
        self._apply_rect()

    def _bind_pressed(self, name: str) -> bool:
        b = self.binds.get(name, {})
        try:
            vk = int(b.get("vk", 0))
        except:
            return False
        if vk == 0:
            return False

        if name == "hide_hovered":
            need_ctrl = bool(b.get("ctrl", True))
            need_alt = bool(b.get("alt", True))
            need_shift = bool(b.get("shift", True))
            if need_ctrl and not key(VK_CONTROL): return False
            if need_alt and not key(VK_MENU): return False
            if need_shift and not key(VK_SHIFT): return False
            return key(vk)

        return key(vk)

    def _bind_label(self, name: str) -> str:
        b = self.binds.get(name, {})
        try:
            vk = int(b.get("vk", 0))
        except:
            vk = 0

        if name == "hide_hovered":
            parts = []
            if bool(b.get("ctrl", True)): parts.append("Ctrl")
            if bool(b.get("alt", True)): parts.append("Alt")
            if bool(b.get("shift", True)): parts.append("Shift")
            parts.append(vk_to_label(vk))
            return " + ".join(parts)

        return vk_to_label(vk)

    def _build_help_text(self) -> str:
        return (
            f"{self._bind_label('toggle_master'):12s} Toggle master on or off\n"
            f"{self._bind_label('toggle_overlay'):12s} Show or hide overlay\n"
            f"{self._bind_label('hide_overlay'):12s} Hide overlay\n"
            f"{vk_to_label(self.binds['map_1']['vk'])} {vk_to_label(self.binds['map_2']['vk'])} {vk_to_label(self.binds['map_3']['vk'])} {vk_to_label(self.binds['map_4']['vk'])}      Switch map (if enabled)\n"
            f"{self._bind_label('hide_hovered')}   Hide hovered POI for current category only\n"
            "\n"
            f"Detected aspect: {self.aspect}\n"
            f"Config version: {self.data.get('version','?')}\n"
            "Files are stored at:\n"
            "%LOCALAPPDATA%\\HuntOverlay\n"
        )

    def _save(self):
        st = self.data.setdefault("settings", {})
        self.data["version"] = CONFIG_VERSION

        st["enable_num_switch"] = self.num_sw
        st["selected_map"] = self.prof
        st["visible_overlay"] = self.visible
        st["master_on"] = self.master
        st["global_scale"] = float(self.global_scale)
        st["minimize_to_tray"] = bool(self.minimize_to_tray)

        st["types"] = self.types
        st["keybinds"] = self.binds

        # Persist hidden sets.
        st["hidden"] = {k: sorted(list(self.hidden_sets.get(k, set()))) for k in self.type_order}

        save_json(CONFIG_PATH, self.data)

    def _apply_rect(self):
        """
        Uses detected aspect label to select the correct ratio for the current map.
        """
        pm = self.data.get("profiles", {}).get(self.prof, {})
        rra = pm.get("rect_ratio_by_aspect", {})
        rr = rra.get(self.aspect, None)
        if not isinstance(rr, dict):
            rr = default_rect_ratio_by_aspect().get(self.aspect, default_rect_ratio_16_9())

        W, H = screenWH()
        self.rect = QtCore.QRect(
            int(rr["rx"] * W),
            int(rr["ry"] * H),
            max(1, int(rr["rw"] * W)),
            max(1, int(rr["rh"] * H))
        )

    def _set_num_switch(self, v: bool):
        self.num_sw = bool(v)
        self._save()

    def _type_toggle(self, tkey: str, enabled: bool):
        if tkey in self.types:
            self.types[tkey]["enabled"] = bool(enabled)
            self._save()
            self.update()

    def _type_color(self, tkey: str, color: QtGui.QColor):
        if tkey in self.types:
            self.types[tkey]["color"] = q2rgb(QtGui.QColor(color))
            self._save()
            self.update()

    def _scale_changed(self, scale: float):
        self.global_scale = float(scale)
        if self.global_scale < 0.10: self.global_scale = 0.10
        if self.global_scale > 5.00: self.global_scale = 5.00
        self._save()
        self.update()

    def _reset_colors(self):
        for k in self.type_order:
            self.types[k]["enabled"] = True
            self.types[k]["color"] = q2rgb(self.type_specs[k]["default_fill"])
            self.panel.setTypeState(k, True, self.type_specs[k]["default_fill"])
        self._save()
        self.update()

    def _reset_config_to_defaults(self):
        """
        Overwrites config.json with fresh defaults and reloads state immediately.
        This does not touch data.json or poiData.json.
        """
        fresh = build_default_config()
        save_json(CONFIG_PATH, fresh)

        self.data = load_or_replace_config()
        self._load_state_from_config(self.data)

        # Re apply map selection and rectangle because the selected map may have changed.
        self._apply_rect()

        # Push state back into GUI widgets.
        self.panel.chk_nums.setChecked(self.num_sw)
        self.panel.chk_tray.setChecked(self.minimize_to_tray)
        self.panel.scale_box.setValue(float(self.global_scale))
        self.panel.setMap(self.prof)

        for k in self.type_order:
            self.panel.setTypeState(k, self.types[k]["enabled"], rgb2q(self.types[k]["color"], self.type_specs[k]["default_fill"]))

        # Refresh help text because keybinds and aspect might differ.
        self.panel.setHelpText(self._build_help_text())

        # Apply overlay visibility state.
        (self.show if self.visible and self.master else self.hide)()
        self._save()
        self.update()

    def switch(self, name: str):
        if name in MAPS and name != self.prof:
            self.prof = name
            self._apply_rect()
            self._save()
            self.update()

    def _rebuild_all_caches(self):
        for m in MAPS:
            self.cache[m] = self._build_points_for_map(m)

    def _build_points_for_map(self, map_name: str):
        block = get_map_block(self.game_data, self.fmt, map_name)
        out = {k: [] for k in self.type_order}
        if not block:
            return out

        def build_for_category(cat: str):
            items = get_category_list(block, self.fmt, cat)
            pts = []
            for it in items:
                if not isinstance(it, dict):
                    continue
                c = it.get("c")
                if not c or len(c) < 2:
                    continue
                try:
                    x, y = float(c[0]), float(c[1])
                except:
                    continue
                u, v = rotate90cw_norm(x, y)
                pts.append({"u": u, "v": v, "x": x, "y": y, "raw": it, "src": cat})
            return pts

        for cat in self.type_order:
            if cat == "possible_xp":
                continue
            out[cat] = build_for_category(cat)

        union = []
        for src in ("towers", "big_towers", "armories"):
            union.extend(out.get(src, []))
        out["possible_xp"] = union

        return out

    def _hidden_key(self, tkey: str, pt: dict) -> str:
        """
        Stable hide id.
        For possible_xp we include src so hiding only affects possible_xp entries.
        For other categories use xi:yi.
        """
        xi = int(round(float(pt.get("x", 0))))
        yi = int(round(float(pt.get("y", 0))))
        if tkey == "possible_xp":
            src = str(pt.get("src", ""))
            return f"{src}:{xi}:{yi}"
        return f"{xi}:{yi}"

    def _is_hidden(self, tkey: str, pt: dict) -> bool:
        return self._hidden_key(tkey, pt) in self.hidden_sets.get(tkey, set())

    def _hide_hovered(self):
        if self.hover is None:
            return
        tkey = self.hover["type"]
        pt = self.hover["pt_ref"]
        hk = self._hidden_key(tkey, pt)
        self.hidden_sets.setdefault(tkey, set()).add(hk)
        self._save()
        self.hover = None
        self.update()

    def _update_hover(self):
        self.hover = None
        if not (self.master and self.visible and self.rect):
            return

        gp = QtGui.QCursor.pos()
        lp = self.mapFromGlobal(gp)
        mx, my = float(lp.x()), float(lp.y())

        pts_by_type = self.cache.get(self.prof, {})
        best = None
        best_d2 = float(self.hover_radius * self.hover_radius)

        for tkey in self.type_order:
            if not self.types.get(tkey, {}).get("enabled", True):
                continue

            for idx, pt in enumerate(pts_by_type.get(tkey, [])):
                if self._is_hidden(tkey, pt):
                    continue
                cx = self.rect.left() + pt["u"] * self.rect.width()
                cy = self.rect.top() + pt["v"] * self.rect.height()
                dx = mx - cx
                dy = my - cy
                d2 = dx * dx + dy * dy
                if d2 <= best_d2:
                    best_d2 = d2
                    best = {"map": self.prof, "type": tkey, "index": idx, "pt_ref": pt}

        self.hover = best

    def _tick_safe(self):
        try:
            self._tick()
        except Exception:
            print("Overlay tick crashed:\n" + traceback.format_exc(), flush=True)

    def _tick(self):
        nm = self._bind_pressed("toggle_master")
        if nm and not self.p_toggle_master:
            self.master = not self.master
            if not self.master and self.visible:
                self.visible = False
                self.hide()
            self._save()
        self.p_toggle_master = nm

        nh = self._bind_pressed("hide_overlay")
        if nh and not self.p_hide and self.visible:
            self.visible = False
            self.hide()
            self._save()
        self.p_hide = nh

        if not self.master:
            return

        nt = self._bind_pressed("toggle_overlay")
        if nt and not self.p_toggle_overlay:
            self.visible = not self.visible
            (self.show if self.visible else self.hide)()
            if self.visible:
                topmost(int(self.winId()))
            self._save()
        self.p_toggle_overlay = nt

        # Map switching uses MAPS order. Since MAPS changed, 2 is Lawson and 3 is DeSalle.
        if self.visible and self.num_sw:
            if self._bind_pressed("map_1"): self.switch(MAPS[0])
            elif self._bind_pressed("map_2"): self.switch(MAPS[1])
            elif self._bind_pressed("map_3"): self.switch(MAPS[2])
            elif self._bind_pressed("map_4"): self.switch(MAPS[3])

        if self.visible:
            self._update_hover()

        hide_now = self._bind_pressed("hide_hovered")
        if hide_now and not self.p_hide_hovered:
            self._hide_hovered()
        self.p_hide_hovered = hide_now

        self.update()

    def _edit_keybind(self, action: str):
        """
        GUI initiated keybind edit.
        Captures next key press plus modifiers.
        Modifiers are only applied to hide_hovered by design.
        """
        d = KeyCaptureDialog(action, self.panel)
        if ICON:
            d.setWindowIcon(QtGui.QIcon(ICON))

        if d.exec() != QtWidgets.QDialog.Accepted:
            return

        b = d.result_bind
        if not isinstance(b, dict) or action not in self.binds:
            return

        self.binds[action]["vk"] = int(b.get("vk", self.binds[action]["vk"]))

        if action == "hide_hovered":
            self.binds[action]["ctrl"] = bool(b.get("ctrl", True))
            self.binds[action]["alt"] = bool(b.get("alt", True))
            self.binds[action]["shift"] = bool(b.get("shift", True))

        self._save()
        self.panel.setHelpText(self._build_help_text())

    def paintEvent(self, _):
        if not (self.master and self.visible and self.rect):
            return

        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)

        pts_by_type = self.cache.get(self.prof, {})

        for tkey in self.type_order:
            if not self.types.get(tkey, {}).get("enabled", True):
                continue

            fill = rgb2q(self.types[tkey].get("color"), self.type_specs[tkey]["default_fill"])
            border = self.type_specs[tkey]["border"]

            base_rpx = int(self.type_specs[tkey]["radius_px"])
            scaled = int(round(base_rpx * float(self.global_scale)))
            if scaled < 1: scaled = 1
            if scaled > 40: scaled = 40

            p.setPen(QtGui.QPen(border, 2))
            p.setBrush(fill)

            for pt in pts_by_type.get(tkey, []):
                if self._is_hidden(tkey, pt):
                    continue
                p.drawEllipse(
                    QtCore.QPointF(
                        self.rect.left() + pt["u"] * self.rect.width(),
                        self.rect.top() + pt["v"] * self.rect.height()
                    ),
                    scaled, scaled
                )

        # Map label at top right.
        m = 20
        txt = f"{self.prof}  ({self.aspect})"
        f = p.font()
        f.setBold(True)
        p.setFont(f)
        fm = QtGui.QFontMetrics(f)
        tw, th = fm.horizontalAdvance(txt), fm.height()
        r = QtCore.QRectF(self.width() - m - tw - 16, m, tw + 16, th + 10)
        p.setPen(QtCore.Qt.NoPen)
        p.setBrush(QtGui.QColor(0, 0, 0, 150))
        p.drawRoundedRect(r, 8, 8)
        p.setPen(QtGui.QPen(QtGui.QColor(230, 230, 230), 1))
        p.drawText(r.adjusted(8, 7, -8, -4), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, txt)
        p.end()

if __name__ == "__main__":
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
