from PyQt5.QtCore import Qt, QPropertyAnimation, pyqtProperty , pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout
from PyQt5.QtGui import QColor, QPainter, QBrush

class ToggleSwitch(QWidget):
    stateChanged = pyqtSignal(bool)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 30)
        self._checked = False  # Initial state of the toggle
        self._handle_position = 2  # Initial position of the handle

        # Animation to move the handle
        self.animation = QPropertyAnimation(self, b"handle_position")
        self.animation.setDuration(200)

    def setChecked(self, checked):
        self._checked = checked
        self.update()

    def toggle(self):
        self._checked = not self._checked
        self.stateChanged.emit(self._checked)
        self.animate()

    def animate(self):
        # Animate the handle position
        start = 32 if not self._checked else 2
        end = 2 if not self._checked else 32
        self.animation.setStartValue(start)
        self.animation.setEndValue(end)
        self.animation.start()

    def mousePressEvent(self, event):
        self.toggle()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw background
        background_color = QColor("#007AFF") if self._checked else QColor("#d3d3d3")
        painter.setBrush(QBrush(background_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 15, 15)

        # Draw handle
        handle_color = QColor("white")
        painter.setBrush(QBrush(handle_color))
        painter.drawEllipse(self._handle_position, 2, 26, 26)

    @pyqtProperty(int)
    def handle_position(self):
        return self._handle_position

    @handle_position.setter
    def handle_position(self, pos):
        self._handle_position = pos
        self.update()
