import ctypes

user32 = ctypes.windll.user32

# Map order is intentionally set to the release order requested.
MAPS = ["Stillwater Bayou", "Lawson Delta", "DeSalle", "Mammon's Gulch"]

CONFIG_VERSION = "1.0.2"

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
