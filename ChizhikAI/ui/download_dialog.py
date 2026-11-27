import os

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QMessageBox, QProgressBar, QPushButton,
    QTextEdit, QVBoxLayout
)

from core.downloader import MODELS, download_model, list_installed_models, remove_model


class DownloadWorker(QThread):
    progress = pyqtSignal(int, int, str)
    completed = pyqtSignal(bool, str)

    def __init__(self, model_info, drive):
        super().__init__()
        self.model_info = model_info
        self.drive = drive

    def run(self):
        try:
            success, result = download_model(self.model_info, self.drive, self.progress.emit)
            self.completed.emit(success, result)
        except Exception as exc:
            self.completed.emit(False, str(exc))


class DownloadDialog(QDialog):
    def __init__(self, parent=None, mode="install"):
        super().__init__(parent)
        self.mode = mode
        self.setWindowTitle("Установка ИИ" if mode == "install" else "Удаление ИИ")
        self.resize(680, 480)
        self.build_ui()
        self.refresh_items()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Выберите диск:"))
        self.drive = QComboBox()
        for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            path = f"{letter}:\\"
            if os.path.exists(path):
                self.drive.addItem(path)
        if not self.drive.count():
            self.drive.addItem(os.path.expanduser("~"))
        self.drive.currentIndexChanged.connect(self.refresh_items)
        layout.addWidget(self.drive)

        self.models = QListWidget()
        layout.addWidget(self.models)

        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        self.status = QTextEdit()
        self.status.setReadOnly(True)
        self.status.setMaximumHeight(90)
        layout.addWidget(self.status)

        buttons = QHBoxLayout()
        self.action = QPushButton("СКАЧАТЬ" if self.mode == "install" else "УДАЛИТЬ")
        self.action.clicked.connect(self.act)
        buttons.addWidget(self.action)
        close = QPushButton("Закрыть")
        close.clicked.connect(self.close)
        buttons.addWidget(close)
        layout.addLayout(buttons)

    def refresh_items(self, *_):
        self.models.clear()
        if self.mode == "install":
            for model in MODELS:
                item = QListWidgetItem(f"{model['name']} — около {model['size_gb']} ГБ")
                item.setData(Qt.UserRole, model)
                self.models.addItem(item)
        else:
            for model in list_installed_models(self.drive.currentText()):
                item = QListWidgetItem(model["name"])
                item.setData(Qt.UserRole, model["id"])
                self.models.addItem(item)

    def act(self):
        item = self.models.currentItem()
        if item is None:
            QMessageBox.information(self, "Выбор", "Сначала выберите модель.")
            return

        if self.mode == "remove":
            success, message = remove_model(self.drive.currentText(), item.data(Qt.UserRole))
            self.status.setPlainText(f"Удалено: {message}" if success else f"Ошибка: {message}")
            self.refresh_items()
            return

        self.action.setEnabled(False)
        self.status.setPlainText("Начинается загрузка модели…")
        self.worker = DownloadWorker(item.data(Qt.UserRole), self.drive.currentText())
        self.worker.progress.connect(self.update_progress)
        self.worker.completed.connect(self.download_done)
        self.worker.start()

    def update_progress(self, downloaded, total, filename):
        if total:
            self.progress.setValue(int(downloaded * 100 / total))
        self.status.setPlainText(f"Загружается {filename}: {downloaded / 1024**3:.2f} ГБ")

    def download_done(self, success, message):
        self.action.setEnabled(True)
        self.progress.setValue(100 if success else 0)
        self.status.setPlainText(f"Готово: {message}" if success else f"Ошибка: {message}")
        if success:
            QMessageBox.information(self, "Готово", "Модель установлена и ярлык создан на рабочем столе.")
