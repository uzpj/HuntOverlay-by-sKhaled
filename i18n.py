# i18n.py
# Lightweight translation layer for HuntOverlay.
#
# Design: English is the source of truth ("under the hood"). Every translatable
# string in the app is passed through tr() using its exact English text as the key.
# Translations live in _TR keyed by that English string. Missing keys (or language
# "en") fall back to the English text unchanged, so the UI never shows blanks.
#
# Translation provenance:
#   zh - Chinese, from a native-speaker community reference
#        (Hunt.Map.Overlay.txt) plus two user-supplied strings.
#   ru - Russian, authored. Terms tied to official Hunt entities (Brutes, map
#        names) are best-effort native; see FLAGGED below.
#   es - Spanish, authored. American place names kept as proper nouns, which is
#        how Spanish localizations typically render them; see FLAGGED below.
#
# FLAGGED (confirm against in-game text / a native speaker):
#   - "Brutes": zh 蛮兽 / ru Громилы / es Brutos  (Hunt's official creature wording)
#   - "Block Shift+Tab" zh 屏蔽 Shift+Tab  (reference entry was incomplete)
#   - RU map-name transliterations (Стилуотер-Байю, Дельта Лоусон, ДеСалль, Ущелье Маммона)
#   - ES map names intentionally left as English proper nouns

# (code, display name) — display name shown in the language selector, in its own script.
LANGUAGES = [
    ("en", "English"),
    ("zh", "中文"),
    ("ru", "Русский"),
    ("es", "Español"),
]

_CODES = {c for c, _ in LANGUAGES}

_TR = {
    "zh": {
        # Title / tabs
        "Hunt Map Overlay": "猎杀地图叠加",
        "Types": "类型",
        "Keybinds": "快捷键",
        "Settings": "设置",
        # POI type labels
        "Possible XP Location": "可能的经验值获取地点",
        "Spawns": "出生点",
        "Armories": "军械库",
        "Hunting Towers": "小塔",
        "Watch Towers": "大塔",
        "Workbenches": "工作台",
        "Wild Targets": "野生目标",
        "Brutes": "蛮兽",
        "Beetles": "甲虫",
        "Easter Eggs": "复活节彩蛋",
        "Melee Weapons": "近战武器",
        "Cash Registers": "收银机",
        # Types tab
        "Map:": "地图：",
        "1–4 map switch": "1-4 地图切换按钮",
        "Scale:": "规模：",
        "Reset Colors": "重置颜色",
        # Keybind labels
        "Toggle master": "切换主模式",
        "Toggle overlay": "切换显示/隐藏面板",
        "Hide overlay": "隐藏覆盖层",
        "Map 1  Stillwater": "地图 1 静水河口",
        "Map 2  Lawson": "地图 2 劳森三角洲",
        "Map 3  DeSalle": "地图 3 德萨莱",
        "Map 4  Mammon": "地图 4 玛门峡谷",
        "Hide hovered POI": "隐藏悬停的地点信息点",
        "Set": "设定",
        # Settings tab
        "Language:": "语言：",
        "Minimize to system tray": "最小化至系统托盘",
        "Hold Tab to show overlay": "按住 Tab 键可显示覆盖层",
        "Block Shift+Tab": "屏蔽 Shift+Tab",
        "Reset to Default Config": "恢复为默认设置配置",
        "Force Refresh": "强制刷新",
        # Data status
        "Data: checking...": "数据：检查中…",
        "Data: updating...": "数据：更新中…",
        "Data updated: ": "数据更新于：",
        "Data: never updated": "数据：从未更新",
        "Data: unknown": "数据：未知",
        # Color dialog
        "Pick Color": "选择颜色",
        "Hue": "色相",
        "Hex": "十六进制",
        "Presets": "预设",
        "OK": "确定",
        "Cancel": "取消",
        # Keybind capture dialog
        "Set keybind: ": "设置快捷键：",
        "Press a key now\nCtrl Alt Shift are captured too\nEsc cancels":
            "现在按下一个按键\nCtrl Alt Shift 也会被记录\nEsc 取消",
        # Tray / errors
        "Restore panel": "恢复面板",
        "Quit": "退出",
        "Panel minimized to tray": "面板已最小化至托盘",
        "HuntOverlay error": "HuntOverlay 错误",
        # Map display names
        "Stillwater Bayou": "静水河口",
        "Lawson Delta": "劳森三角洲",
        "DeSalle": "德萨莱",
        "Mammon's Gulch": "玛门峡谷",
    },
    "ru": {
        # Title / tabs
        "Hunt Map Overlay": "Карта-оверлей Hunt",
        "Types": "Типы",
        "Keybinds": "Клавиши",
        "Settings": "Настройки",
        # POI type labels
        "Possible XP Location": "Возможное место опыта",
        "Spawns": "Точки появления",
        "Armories": "Оружейные",
        "Hunting Towers": "Охотничьи вышки",
        "Watch Towers": "Сторожевые вышки",
        "Workbenches": "Верстаки",
        "Wild Targets": "Дикие цели",
        "Brutes": "Громилы",
        "Beetles": "Жуки",
        "Easter Eggs": "Пасхалки",
        "Melee Weapons": "Холодное оружие",
        "Cash Registers": "Кассы",
        # Types tab
        "Map:": "Карта:",
        "1–4 map switch": "Смена карты 1–4",
        "Scale:": "Масштаб:",
        "Reset Colors": "Сбросить цвета",
        # Keybind labels
        "Toggle master": "Главный переключатель",
        "Toggle overlay": "Показать/скрыть оверлей",
        "Hide overlay": "Скрыть оверлей",
        "Map 1  Stillwater": "Карта 1  Стилуотер",
        "Map 2  Lawson": "Карта 2  Лоусон",
        "Map 3  DeSalle": "Карта 3  ДеСалль",
        "Map 4  Mammon": "Карта 4  Маммон",
        "Hide hovered POI": "Скрыть точку под курсором",
        "Set": "Задать",
        # Settings tab
        "Language:": "Язык:",
        "Minimize to system tray": "Свернуть в системный трей",
        "Hold Tab to show overlay": "Удерживать Tab для показа оверлея",
        "Block Shift+Tab": "Блокировать Shift+Tab",
        "Reset to Default Config": "Сбросить к настройкам по умолчанию",
        "Force Refresh": "Обновить принудительно",
        # Data status
        "Data: checking...": "Данные: проверка…",
        "Data: updating...": "Данные: обновление…",
        "Data updated: ": "Данные обновлены: ",
        "Data: never updated": "Данные: не обновлялись",
        "Data: unknown": "Данные: неизвестно",
        # Color dialog
        "Pick Color": "Выбор цвета",
        "Hue": "Тон",
        "Hex": "Hex",
        "Presets": "Предустановки",
        "OK": "ОК",
        "Cancel": "Отмена",
        # Keybind capture dialog
        "Set keybind: ": "Назначить клавишу: ",
        "Press a key now\nCtrl Alt Shift are captured too\nEsc cancels":
            "Нажмите клавишу\nCtrl Alt Shift также учитываются\nEsc — отмена",
        # Tray / errors
        "Restore panel": "Восстановить панель",
        "Quit": "Выход",
        "Panel minimized to tray": "Панель свёрнута в трей",
        "HuntOverlay error": "Ошибка HuntOverlay",
        # Map display names
        "Stillwater Bayou": "Стилуотер-Байю",
        "Lawson Delta": "Дельта Лоусон",
        "DeSalle": "ДеСалль",
        "Mammon's Gulch": "Ущелье Маммона",
    },
    "es": {
        # Title / tabs
        "Hunt Map Overlay": "Superposición de mapa de Hunt",
        "Types": "Tipos",
        "Keybinds": "Atajos",
        "Settings": "Ajustes",
        # POI type labels
        "Possible XP Location": "Posible ubicación de XP",
        "Spawns": "Puntos de aparición",
        "Armories": "Armerías",
        "Hunting Towers": "Torres de caza",
        "Watch Towers": "Atalayas",
        "Workbenches": "Bancos de trabajo",
        "Wild Targets": "Objetivos salvajes",
        "Brutes": "Brutos",
        "Beetles": "Escarabajos",
        "Easter Eggs": "Huevos de Pascua",
        "Melee Weapons": "Armas cuerpo a cuerpo",
        "Cash Registers": "Cajas registradoras",
        # Types tab
        "Map:": "Mapa:",
        "1–4 map switch": "Cambio de mapa 1–4",
        "Scale:": "Escala:",
        "Reset Colors": "Restablecer colores",
        # Keybind labels
        "Toggle master": "Interruptor principal",
        "Toggle overlay": "Mostrar/ocultar superposición",
        "Hide overlay": "Ocultar superposición",
        "Map 1  Stillwater": "Mapa 1  Stillwater",
        "Map 2  Lawson": "Mapa 2  Lawson",
        "Map 3  DeSalle": "Mapa 3  DeSalle",
        "Map 4  Mammon": "Mapa 4  Mammon",
        "Hide hovered POI": "Ocultar PDI bajo el cursor",
        "Set": "Asignar",
        # Settings tab
        "Language:": "Idioma:",
        "Minimize to system tray": "Minimizar a la bandeja del sistema",
        "Hold Tab to show overlay": "Mantén Tab para mostrar la superposición",
        "Block Shift+Tab": "Bloquear Shift+Tab",
        "Reset to Default Config": "Restablecer configuración predeterminada",
        "Force Refresh": "Forzar actualización",
        # Data status
        "Data: checking...": "Datos: comprobando…",
        "Data: updating...": "Datos: actualizando…",
        "Data updated: ": "Datos actualizados: ",
        "Data: never updated": "Datos: nunca actualizados",
        "Data: unknown": "Datos: desconocido",
        # Color dialog
        "Pick Color": "Elegir color",
        "Hue": "Tono",
        "Hex": "Hex",
        "Presets": "Preajustes",
        "OK": "Aceptar",
        "Cancel": "Cancelar",
        # Keybind capture dialog
        "Set keybind: ": "Asignar tecla: ",
        "Press a key now\nCtrl Alt Shift are captured too\nEsc cancels":
            "Pulsa una tecla ahora\nCtrl Alt Shift también se capturan\nEsc cancela",
        # Tray / errors
        "Restore panel": "Restaurar panel",
        "Quit": "Salir",
        "Panel minimized to tray": "Panel minimizado a la bandeja",
        "HuntOverlay error": "Error de HuntOverlay",
        # Map display names (kept as proper nouns in Spanish)
        "Stillwater Bayou": "Stillwater Bayou",
        "Lawson Delta": "Lawson Delta",
        "DeSalle": "DeSalle",
        "Mammon's Gulch": "Mammon's Gulch",
    },
}

_current = "en"


def set_language(code: str) -> None:
    global _current
    _current = code if code in _CODES else "en"


def get_language() -> str:
    return _current


def is_valid(code: str) -> bool:
    return code in _CODES


def tr(s: str) -> str:
    """Return the active-language string for the English source text s.
    Falls back to s itself when language is English or the key is missing."""
    if _current == "en":
        return s
    return _TR.get(_current, {}).get(s, s)
