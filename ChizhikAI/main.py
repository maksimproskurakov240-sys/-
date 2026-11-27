import sys
import os
import traceback
import datetime
import time
import math
import random

def log_crash():
    crash_dir = r"C:\Users\New\Desktop\ChizhikAI"
    os.makedirs(crash_dir, exist_ok=True)
    log_path = os.path.join(crash_dir, "crash_log.txt")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"--- CRASH AT {datetime.datetime.now()} ---\n")
        traceback.print_exc(file=f)

try:
    if getattr(sys, 'frozen', False):
        sys.path.insert(0, sys._MEIPASS)
    else:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    from PyQt5.QtWidgets import QApplication, QSplashScreen, QLabel
    from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont
    from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
    from ui.main_window import MainWindow
    from core.db import Database

    # ── АНИМАЦИЯ-ЗАСТАВКА ─────────────────────────────
    class AnimThread(QThread):
        update_signal = pyqtSignal(str)
        def run(self):
            # Тут генерируется красивая галактика в символах
            t = 0
            for _ in range(50):
                lines = []
                for y in range(20):
                    row = ""
                    for x in range(60):
                        dx = (x - 30) / 30
                        dy = (y - 10) / 10
                        r = math.sqrt(dx*dx + dy*dy)
                        v = math.sin(r*10 - t*3) * 0.5 + 0.5
                        chars = " .·:-=+*#%@"
                        row += chars[int(v * (len(chars)-1))]
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
            self.label.setStyleSheet("background-color: black; color: #4fc3f7; font-family: Consolas; font-size: 12px;")
            self.label.setText("Инициализация ядра...")
            
            self.thread = AnimThread()
            self.thread.update_signal.connect(self.update_text)
            self.thread.start()

        def update_text(self, text):
            self.label.setText("ЗАГРУЗКА CHIZHIK ENGINE\n\n" + text)

    def main():
        app = QApplication(sys.argv)
        
        # Показываем заставку на 2 секунды
        splash = SplashScreen()
        splash.show()
        
        db = Database()
        
        def start_main():
            window = MainWindow(db)
            window.show()
            splash.finish(window)
            
        QTimer.singleShot(2500, start_main)
        sys.exit(app.exec_())

    if __name__ == "__main__":
        main()
except Exception:
    log_crash()