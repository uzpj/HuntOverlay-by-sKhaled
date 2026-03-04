import os
import traceback

from PySide6 import QtCore, QtGui, QtWidgets

from HO.Static.Constants import (
    VK_TAB, VK_CONTROL, VK_MENU, VK_SHIFT, MAPS, CONFIG_VERSION, DEFAULT_HIDDEN_POSSIBLE_XP
)

from HO.Static.Util import (
    ICON, DATA_PATH, STYLE_PATH, udir, load_json, detect_data_format, screenWH, detect_aspect_label,
    load_or_replace_config, click_through, rgb2q, topmost, find_style_by_category, qcolor_from_any,
    overlay_radius_from_spec, default_keybinds, q2rgb, key, vk_to_label, save_json, default_rect_ratio_16_9,
    build_default_config, get_map_block, get_category_list, rotate90cw_norm, KeyCaptureDialog,
    default_rect_ratio_by_aspect, CONFIG_PATH)

from HO.Panel import Panel


class Overlay(QtWidgets.QWidget):
    def __init__(self):
        super().__init__(None, QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setMouseTracking(False)
        self._set_overlay_to_primary_monitor()

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
            "brutes",
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
        self.panel = Panel(self.type_order, self.type_specs, self.global_scale, help_text, binds_label_map,
                           self.minimize_to_tray, self.hold_tab_mode, self.safe_tab_mode)
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
        self.panel.holdTabModeChanged.connect(self._set_hold_tab_mode)
        self.panel.safeTabModeChanged.connect(self._set_safe_tab_mode)

        # Seed GUI with current state.
        self.panel.chk_nums.setChecked(self.num_sw)
        self.panel.setMap(self.prof)
        for k in self.type_order:
            self.panel.setTypeState(k, self.types[k]["enabled"],
                                    rgb2q(self.types[k]["color"], self.type_specs[k]["default_fill"]))

        self.panel.move(40, 40)

        # System tray setup.
        self.tray = None
        if self.minimize_to_tray:
            self._ensure_tray()

        # Make overlay click through and topmost on primary monitor.
        click_through(int(self.winId()))
        if self.visible and self.master:

            self._show_overlay_on_primary()

        else:

            self.hide()
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

        # Start with the control panel minimized to tray.
        if self.minimize_to_tray:
            self._hide_panel_to_tray()
        else:
            self.panel.show()
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

    def _set_hold_tab_mode(self, v: bool):

        self.hold_tab_mode = bool(v)

        self._save()

        self.panel.setHelpText(self._build_help_text())

    def _set_safe_tab_mode(self, v: bool):
        self.safe_tab_mode = bool(v)

        self._save()

        self.panel.setHelpText(self._build_help_text())

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
        add_from_style("brutes", "Brutes")
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
        self.hold_tab_mode = bool(st.get("hold_tab_to_show", False))
        self.safe_tab_mode = bool(st.get("use_safe_tab_mode", True))

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

        safe_tab_violation = self.safe_tab_mode and (key(VK_CONTROL) or key(VK_MENU) or key(VK_SHIFT))
        if vk == VK_TAB and safe_tab_violation:
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
            f"{self._bind_label('toggle_overlay'):12s} {'Hold to show overlay' if self.hold_tab_mode else 'Show or hide overlay'}\n"
            f"{self._bind_label('hide_overlay'):12s} Hide overlay\n"
            f"{vk_to_label(self.binds['map_1']['vk'])} {vk_to_label(self.binds['map_2']['vk'])} {vk_to_label(self.binds['map_3']['vk'])} {vk_to_label(self.binds['map_4']['vk'])}      Switch map (if enabled)\n"
            f"{self._bind_label('hide_hovered')}   Hide hovered POI for current category only\n"
            "\n"
            f"Detected aspect: {self.aspect}\n"
            f"Config version: {self.data.get('version', '?')}\n"
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
        st["hold_tab_to_show"] = bool(self.hold_tab_mode)
        st["use_safe_tab_mode"] = bool(self.safe_tab_mode)

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

    def _set_overlay_to_primary_monitor(self):

        ps = QtGui.QGuiApplication.primaryScreen()

        if ps is None:
            return

        self.setGeometry(ps.geometry())

    def _show_overlay_on_primary(self):

        self._set_overlay_to_primary_monitor()

        self.show()

        topmost(int(self.winId()))

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
        self.panel.chk_hold_tab.setChecked(self.hold_tab_mode)
        self.panel.chk_safe_tab.setChecked(self.safe_tab_mode)
        self.panel.scale_box.setValue(float(self.global_scale))
        self.panel.setMap(self.prof)

        for k in self.type_order:
            self.panel.setTypeState(k, self.types[k]["enabled"],
                                    rgb2q(self.types[k]["color"], self.type_specs[k]["default_fill"]))

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
        if self.hold_tab_mode:
            next_visible = bool(nt)
            if self.visible != next_visible:
                self.visible = next_visible
                if self.visible:
                    self._show_overlay_on_primary()
                else:
                    self.hide()
                self._save()
            self.p_toggle_overlay = nt
        else:
            if nt and not self.p_toggle_overlay:
                self.visible = not self.visible
                if self.visible:
                    self._show_overlay_on_primary()
                else:
                    self.hide()
                self._save()
            self.p_toggle_overlay = nt

        # Map switching uses MAPS order. Since MAPS changed, 2 is Lawson and 3 is DeSalle.
        if self.visible and self.num_sw:
            if self._bind_pressed("map_1"):
                self.switch(MAPS[0])
            elif self._bind_pressed("map_2"):
                self.switch(MAPS[1])
            elif self._bind_pressed("map_3"):
                self.switch(MAPS[2])
            elif self._bind_pressed("map_4"):
                self.switch(MAPS[3])

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
