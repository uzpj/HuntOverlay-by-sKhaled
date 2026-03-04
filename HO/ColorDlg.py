from PySide6 import QtCore, QtGui, QtWidgets

from HO.Svpad import SVPad


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

