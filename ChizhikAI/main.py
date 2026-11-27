import sys
import os
import traceback
import datetime


def app_dir():
    """Directory containing this application's entry point/data."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def log_crash(exc=None):
    """Log startup/runtime errors to a writable location."""
    candidates = []

    if getattr(sys, "frozen", False):
        candidates.append(app_dir())

    if os.path.expanduser("~"):
        candidates.append(os.path.join(os.path.expanduser("~"), ".chizhik_ai"))

    candidates.append(os.path.join(os.getcwd(), "crash_log"))

    log_path = None
    for directory in candidates:
        try:
            os.makedirs(directory, exist_ok=True)
            log_path = os.path.join(directory, "crash_log.txt")
            with open(log_path, "w", encoding="utf-8") as log:
                log.write(f"--- CRASH AT {datetime.datetime.now().isoformat()} ---\n")
                log.write(f"Python: {sys.version}\n")
                log.write(f"Executable: {sys.executable}\n")
                log.write(f"Frozen: {getattr(sys, 'frozen', False)}\n")
                if exc is not None:
                    log.write(f"Exception: {type(exc).__name__}: {exc}\n\n")
                traceback.print_exc(file=log)
            break
        except Exception:
            continue

    return log_path


def main():
    import math
    import time

    if getattr(sys, "frozen", False):
        sys.path.insert(0, sys._MEIPASS)
    else:
        sys.path.insert(0, app_dir())

    os.chdir(app_dir())

    from PyQt5.QtWidgets import QApplication, QSplashScreen, QLabel
    from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
    from ui.main_window import MainWindow
    from core.db import Database

    class AnimThread(QThread):
        update_signal = pyqtSignal(str)

        def run(self):
            t = 0
            for _ in range(50):
                lines = []
                for y in range(20):
                    row = ""
                    for x in range(60):
                        dx = (x - 30) / 30
                        dy = (y - 10) / 10
                        radius = math.sqrt(dx * dx + dy * dy)
                        value = math.sin(radius * 10 - t * 3) * 0.5 + 0.5
                        chars = " .·:-=+*#%@"
                        row += chars[int(value * (len(chars) - 1))]
                    lines.append(row)
                self.update_signal.emit("\n".join(lines))
                t += 0.2
                time.sleep(0.05)

    class SplashScreen(QSplashScreen):
        def __init__(self):
            super().__init__()
            self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
            self.setFixedSize(700, 500)
            self.label = QLabel(self)
            self.label.setGeometry(0, 0, 700, 500)
            self.label.setAlignment(Qt.AlignCenter)
            self.label.setStyleSheet(
                "background-color: black; color: #4fc3f7; "
                "font-family: Consolas; font-size: 12px;"
            )
            self.label.setText("Инициализация ядра...")

            self.thread = AnimThread()
            self.thread.update_signal.connect(self.update_text)
            self.thread.start()

        def update_text(self, text):
            self.label.setText("ЗАГРУЗКА CHIZHIK ENGINE\n\n" + text)

    app = QApplication(sys.argv)
    splash = SplashScreen()
    splash.show()

    db = Database()
    window = None

    def start_main():
        nonlocal window
        window = MainWindow(db)
        window.show()
        splash.finish(window)

    QTimer.singleShot(2500, start_main)
    return app.exec_()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:
        log_crash(exc)
