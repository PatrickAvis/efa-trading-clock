"""The clock window."""

import sys
from datetime import UTC, datetime

from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QLCDNumber, QMainWindow

from efa_trading_clock.colours import countdown_colour
from efa_trading_clock.periods import clock_state

APP_NAME = "EFA Trading Clock"
APP_ID = "PatrickAvis.EFATradingClock"
DISPLAY_DIGITS = 8


def build_icon() -> QIcon:
    """Draw a simple clock face, so the app needs no image files."""
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor(20, 20, 20), 5))
    painter.setBrush(QColor(60, 200, 80))
    painter.drawEllipse(4, 4, size - 8, size - 8)

    centre = QPointF(size / 2, size / 2)
    painter.setPen(QPen(QColor(20, 20, 20), 5, c=Qt.PenCapStyle.RoundCap))
    painter.drawLine(centre, QPointF(size / 2, 15))
    painter.drawLine(centre, QPointF(45, size / 2))
    painter.end()
    return QIcon(pixmap)


class ClockWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setGeometry(50, 50, 540, 110)
        self.setWindowIcon(build_icon())

        self.lcd = QLCDNumber(DISPLAY_DIGITS, self)
        self.setCentralWidget(self.lcd)
        self._colour: tuple[int, int, int] | None = None

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.timeout.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        now = datetime.now(UTC)
        state = clock_state(now)

        self.lcd.display(state.now.strftime("%H:%M:%S"))
        self.setWindowTitle(state.title)
        self._set_colour(countdown_colour(state.seconds_to_gate_closure))

        # Schedule from the wall clock so the display stays aligned to whole seconds.
        self.timer.start(1000 - now.microsecond // 1000)

    def _set_colour(self, colour: tuple[int, int, int]) -> None:
        if colour == self._colour:
            return
        self._colour = colour
        red, green, blue = colour
        self.lcd.setStyleSheet(
            f"QLCDNumber {{ color: rgb(0, 0, 0); background-color: rgb({red}, {green}, {blue}); }}"
        )


def _set_windows_app_id() -> None:
    """Give the app its own taskbar icon rather than grouping it under Python."""
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)


def main() -> int:
    _set_windows_app_id()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    window = ClockWindow()
    window.show()
    return app.exec()
