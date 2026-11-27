import os
import sys
import traceback
import datetime


def log_crash():
    try:
        directory = os.path.join(os.path.expanduser("~"), ".chizhik_ai")
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, "crash_log.txt")
        with open(path, "a", encoding="utf-8") as log:
            log.write(f"\n--- CRASH {datetime.datetime.now().isoformat()} ---\n")
            traceback.print_exc(file=log)
    except Exception:
        pass


def main():
    if getattr(sys, "frozen", False):
        sys.path.insert(0, sys._MEIPASS)
    else:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    from PyQt5.QtWidgets import QApplication, QSplashScreen, QLabel
    from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
    from ui.main_window import MainWindow

    class AnimThread(QThread):
        text_updated = pyqtSignal(str)

        def run(self):
            import math
            import time
            for frame in range(35):
                rows = []
                for y in range(16):
                    line = ""
                    for x in range(48):
                        radius = math.hypot((x - 24) / 24, (y - 8) / 8)
                        value = math.sin(radius * 10 - frame * 0.3) * 0.5 + 0.5
                        chars = " .·:-=+*#%@"
                        line += chars[min(len(chars) - 1, int(value * len(chars)))]
                    rows.append(line)
                self.text_updated.emit("\n".join(rows))
                time.sleep(0.06)

    class Splash(QSplashScreen):
        def __init__(self):
            super().__init__()
            self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
            self.setFixedSize(640, 420)
            self.label = QLabel("ЗАПУСК CHIZHIK AI…", self)
            self.label.setGeometry(0, 0, 640, 420)
            self.label.setAlignment(Qt.AlignCenter)
            self.label.setStyleSheet("background:#000;color:#4fc3f7;font-family:Consolas;font-size:12px")
            self.thread = AnimThread(self)
            self.thread.text_updated.connect(lambda text: self.label.setText("CHIZHIK AI\n\n" + text))
            self.thread.start()

    app = QApplication(sys.argv)
    app.setApplicationName("Chizhik AI Installer")
    splash = Splash()
    splash.show()
    window = MainWindow()

    def show_main():
        window.show()
        splash.finish(window)

    QTimer.singleShot(2200, show_main)
    return app.exec_()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        log_crash()
        raise
