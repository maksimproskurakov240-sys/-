from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QListWidget, QListWidgetItem, QTextEdit, QProgressBar, QLabel, QComboBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from core.downloader import MODELS, download_model

class DownloadWorker(QThread):
    progress = pyqtSignal(float, int, int, list)
    finished = pyqtSignal(bool, str)

    def __init__(self, model_info, target_dir):
        super().__init__()
        self.model_info = model_info
        self.target_dir = target_dir

    def run(self):
        def callback(prog, down, total, lines):
            self.progress.emit(prog, down, total, lines)
        success, msg = download_model(self.model_info, self.target_dir, callback)
        self.finished.emit(success, msg)

class DownloadDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Менеджер загрузок ИИ")
        self.resize(900, 600)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        
        # Левая панель
        left_panel = QVBoxLayout()
        
        lbl_drive = QLabel("Выберите диск:")
        left_panel.addWidget(lbl_drive)
        
        self.combo_drive = QComboBox()
        self.combo_drive.addItems(["C:\\", "D:\\", "E:\\", "F:\\"])
        left_panel.addWidget(self.combo_drive)
        
        lbl_model = QLabel("Выберите нейросеть:")
        left_panel.addWidget(lbl_model)
        
        self.list_models = QListWidget()
        for m in MODELS:
            item = QListWidgetItem(f"{m['name']} ({m['size_gb']} GB)")
            item.setData(Qt.UserRole, m)
            self.list_models.addItem(item)
        left_panel.addWidget(self.list_models)
        
        self.btn_download = QPushButton("СКАЧАТЬ")
        self.btn_download.setStyleSheet("background-color: #0e639c; font-weight: bold; padding: 10px;")
        self.btn_download.clicked.connect(self.start_download)
        left_panel.addWidget(self.btn_download)
        
        layout.addLayout(left_panel, 1)
        
        # Правая панель (консоль)
        right_panel = QVBoxLayout()
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("background-color: #000; color: #0f0; font-family: Consolas; font-size: 12px;")
        right_panel.addWidget(self.console)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #4fc3f7; }")
        right_panel.addWidget(self.progress_bar)
        
        self.lbl_status = QLabel("Ожидание...")
        self.lbl_status.setStyleSheet("color: #aaa;")
        right_panel.addWidget(self.lbl_status)
        
        layout.addLayout(right_panel, 2)

    def start_download(self):
        item = self.list_models.currentItem()
        if not item: return
        
        model_info = item.data(Qt.UserRole)
        target_dir = self.combo_drive.currentText()
        
        self.btn_download.setEnabled(False)
        self.console.clear()
        
        self.worker = DownloadWorker(model_info, target_dir)
        self.worker.progress.connect(self.update_ui)
        self.worker.finished.connect(self.download_finished)
        self.worker.start()

    def update_ui(self, prog, down, total, lines):
        self.progress_bar.setValue(int(prog))
        self.lbl_status.setText(f"Скачано: {down/(1024**3):.2f} / {total/(1024**3):.2f} GB")
        self.console.clear()
        self.console.setPlainText("\n".join(lines))
        # Автоскролл вниз
        scrollbar = self.console.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def download_finished(self, success, msg):
        self.btn_download.setEnabled(True)
        if success:
            self.lbl_status.setText(f"✅ Установлено в: {msg}")
            self.console.append("\n[+] УСТАНОВКА ЗАВЕРШЕНА!")
        else:
            self.lbl_status.setText(f"❌ Ошибка: {msg}")