from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.download_dialog import DownloadDialog


class MainWindow(QMainWindow):
    """Installer shell: model management stays in this app; no per-model chats."""

    def __init__(self, db=None):
        super().__init__()
        self.db = db
        self.setWindowTitle("Chizhik AI — установщик")
        self.resize(760, 520)
        self.setMinimumSize(600, 420)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(60, 35, 60, 35)
        layout.setSpacing(18)

        title = QLabel("CHIZHIK AI")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 30px; font-weight: bold; color: #4fc3f7;")
        layout.addWidget(title)

        subtitle = QLabel("Локальные модели ИИ — установка и управление")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #cccccc; font-size: 15px;")
        layout.addWidget(subtitle)

        layout.addStretch(1)
        for text, callback in (
            ("Загрузить ИИ", self.install_models),
            ("Удалить ИИ", self.remove_models),
            ("Автор", self.show_author),
            ("Выход", self.close),
        ):
            button = QPushButton(text)
            button.setMinimumHeight(48)
            button.setStyleSheet("font-size: 16px; padding: 8px; background-color: #2d2d2d; color: white;")
            button.clicked.connect(callback)
            layout.addWidget(button)
        layout.addStretch(1)

        self.setStyleSheet("QMainWindow, QWidget { background-color: #1e1e1e; color: #eeeeee; }")

    def install_models(self):
        DownloadDialog(self, mode="install").exec_()

    def remove_models(self):
        DownloadDialog(self, mode="remove").exec_()

    def show_author(self):
        QMessageBox.information(self, "Автор", "Chizhik AI Installer\nАвтор проекта: см. страницу репозитория.")
