from PySide6 import QtCore, QtGui, QtWidgets


from HO.Static.Constants import MAPS

from HO.Dotchip import DotChip


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
    holdTabModeChanged = QtCore.Signal(bool)
    safeTabModeChanged = QtCore.Signal(bool)

    def __init__(self, type_order, type_specs, start_scale: float, help_text: str, binds_label_map: dict, start_min_to_tray: bool, start_hold_tab_mode: bool, start_safe_tab_mode: bool, p=None):
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

        self.chk_tray = self._create_option(v, "Minimize to system tray", start_min_to_tray, self.minimizeToTrayChanged)
        self.chk_hold_tab = self._create_option(v, "Hold Tab to show overlay", start_hold_tab_mode, self.holdTabModeChanged)
        self.chk_safe_tab = self._create_option(v, "Lock Tab while Ctrl/Shift/Alt held", start_safe_tab_mode, self.safeTabModeChanged)

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

    def _create_option(self, v, title, start_val, func):
        widget = QtWidgets.QCheckBox(title)
        widget.setChecked(bool(start_val))
        v.addWidget(widget)
        widget.toggled.connect(lambda b: func.emit(bool(b)))
        return widget

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
