from PySide6 import QtCore, QtGui, QtWidgets

from HO.Static.Util import ICON

from HO.ColorDlg import AdvColorDlg


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
            "QPushButton:hover { background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255,255,255,50), stop:1 transparent); }"
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
