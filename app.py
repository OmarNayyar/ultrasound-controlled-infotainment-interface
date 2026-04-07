"""Application entry point for the gesture-controlled infotainment demo."""

import sys

from PyQt6.QtWidgets import QApplication

from ui_mainwindow import MainWindow


def main() -> int:
    """Launch the desktop interface."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
