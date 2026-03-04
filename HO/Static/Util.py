import json
import os
import shutil
import sys

from PySide6 import QtCore, QtGui, QtWidgets

from HO.Static.Constants import (
    user32, VK_TAB, VK_CONTROL, VK_MENU, VK_H, VK1, VK_BT, VK2, VK3, VK4, VK_DELETE, VK_SHIFT, VK_ESC, MAPS,
    CONFIG_VERSION, DEFAULT_HIDDEN_POSSIBLE_XP
)

GetKey = user32.GetAsyncKeyState


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
        try:

            idx = MAPS.index(map_name)

        except ValueError:

            return None

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
            "hold_tab_to_show": False,
            "use_safe_tab_mode": True,
            "keybinds": default_keybinds(),
            "types": {},
            "hidden": {"possible_xp": list(DEFAULT_HIDDEN_POSSIBLE_XP)},
        },
    }


ICON = os.path.join(bd(), "myicon.ico") if os.path.isfile(os.path.join(bd(), "myicon.ico")) else ""
DATA_PATH = ensure_user_file("../../data.json")
STYLE_PATH = ensure_user_file("../../poiData.json")
CONFIG_PATH = os.path.join(udir(), "config.json")


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
