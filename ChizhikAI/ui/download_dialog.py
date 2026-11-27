import os
import shutil

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
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
        self.worker = None
        self.setWindowTitle("Установка ИИ" if mode == "install" else "Удаление ИИ")
        self.resize(680, 480)
        self._build_ui()
        self._refresh_items()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Выберите диск для установки:" if self.mode == "install" else "Выберите диск с установленной моделью:"))

        self.drive = QComboBox()
        if os.name == "nt":
            for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
                path = f"{letter}:\\"
                if os.path.exists(path):
                    self.drive.addItem(path)
        else:
            self.drive.addItem(os.path.expanduser("~"))
        if self.drive.count() == 0:
            self.drive.addItem(os.path.abspath(os.sep))
        self.drive.currentIndexChanged.connect(self._refresh_items)
        layout.addWidget(self.drive)

        self.models = QListWidget()
        layout.addWidget(self.models)

        self.details = QLabel(
            "Для работы модели нужен совместимый llama.cpp runtime. "
            "Загрузка модели требует интернет; после загрузки генерация работает локально."
            if self.mode == "install" else "Будет удалён только выбранный файл модели."
        )
        self.details.setWordWrap(True)
        layout.addWidget(self.details)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        layout.addWidget(self.progress)

        self.status = QTextEdit()
        self.status.setReadOnly(True)
        self.status.setMaximumHeight(90)
        layout.addWidget(self.status)

        buttons = QHBoxLayout()
        self.action = QPushButton("СКАЧАТЬ" if self.mode == "install" else "УДАЛИТЬ")
        self.action.clicked.connect(self._act)
        buttons.addWidget(self.action)
        close = QPushButton("Закрыть")
        close.clicked.connect(self.close)
        buttons.addWidget(close)
        layout.addLayout(buttons)

    def _refresh_items(self, *_):
        self.models.clear()
        drive = self.drive.currentText()
        if self.mode == "install":
            for model in MODELS:
                item = QListWidgetItem(f"{model['name']} — около {model['size_gb']} ГБ")
                item.setData(Qt.UserRole, model)
                self.models.addItem(item)
        else:
            for model in list_installed_models(drive):
                item = QListWidgetItem(model.get("name", "Модель"))
                item.setData(Qt.UserRole, model.get("id"))
                self.models.addItem(item)
            if not self.models.count():
                self.status.setPlainText("На выбранном диске установленные модели не найдены.")

    def _act(self):
        item = self.models.currentItem()
        if item is None:
            QMessageBox.information(self, "Выбор модели", "Сначала выберите модель из списка.")
            return
        if self.mode == "remove":
            answer = QMessageBox.question(self, "Подтверждение", f"Удалить модель «{item.text()}»?")
            if answer != QMessageBox.Yes:
                return
            ok, message = remove_model(self.drive.currentText(), item.data(Qt.UserRole))
            self.status.setPlainText(f"Модель удалена: {message}" if ok else f"Ошибка: {message}")
            self._refresh_items()
            return

        self.action.setEnabled(False)
        self.models.setEnabled(False)
        self.drive.setEnabled(False)
        self.status.setPlainText("Проверяю доступный файл модели и начинаю загрузку…")
        self.worker = DownloadWorker(item.data(Qt.UserRole), self.drive.currentText())
        self.worker.progress.connect(self._update_progress)
        self.worker.completed.connect(self._download_done)
        self.worker.start()

    def _update_progress(self, downloaded, total, filename):
        if total > 0:
            self.progress.setValue(min(100, int(downloaded * 100 / total)))
            size_text = f"{downloaded / 1024**3:.2f} / {total / 1024**3:.2f} ГБ"
        else:
            self.progress.setRange(0, 0)
            size_text = f"{downloaded / 1024**3:.2f} ГБ"
        self.status.setPlainText(f"Загружается {filename}: {size_text}")

    def _download_done(self, success, result):
        self.progress.setRange(0, 100)
        self.progress.setValue(100 if success else 0)
        self.status.setPlainText(f"Готово: {result}" if success else f"Ошибка загрузки: {result}")
        self.action.setEnabled(True)
        self.models.setEnabled(True)
        self.drive.setEnabled(True)
        if success:
            QMessageBox.information(self, "Готово", "Модель загружена на выбранный диск. Ярлыки на рабочем столе не создавались.")
