from PySide6 import QtCore, QtGui, QtWidgets


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
