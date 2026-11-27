import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QPushButton, QLabel, QVBoxLayout, QWidget

from ui.download_dialog import DownloadDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chizhik AI")
        self.resize(760, 520)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(60, 35, 60, 35)

        title = QLabel("CHIZHIK AI")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 30px; font-weight: bold; color: #4fc3f7;")
        layout.addWidget(title)

        layout.addStretch()
        for text, callback in (
            ("Загрузить ИИ", lambda: DownloadDialog(self, "install").exec_()),
            ("Удалить ИИ", lambda: DownloadDialog(self, "remove").exec_()),
            ("Выход", self.close),
        ):
            button = QPushButton(text)
            button.setMinimumHeight(48)
            button.clicked.connect(callback)
            layout.addWidget(button)
        layout.addStretch()

        self.setStyleSheet("QMainWindow, QWidget { background: #1e1e1e; color: white; }")
