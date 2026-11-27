import json
import os
import re
import sys
import time
import urllib.request

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLabel, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal


class LlamaWorker(QThread):
    response_ready = pyqtSignal(str)
    error_ready = pyqtSignal(str)

    def __init__(self, prompt, model_path, context="4096"):
        super().__init__()
        self.prompt = prompt
        self.model_path = model_path
        self.context = context

    def run(self):
        import requests
        import subprocess

        llama = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runtime", "llama-server.exe")
        if not os.path.isfile(llama):
            self.error_ready.emit("llama-server.exe не найден в папке runtime. Пересоберите приложение с runtime llama.cpp.")
            return

        try:
            process = subprocess.Popen(
                [llama, "-m", self.model_path, "-c", self.context, "--port", "18080", "--host", "127.0.0.1"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            for _ in range(40):
                try:
                    requests.get("http://127.0.0.1:18080/health", timeout=0.25)
                    break
                except requests.RequestException:
                    time.sleep(0.25)

            response = requests.post(
                "http://127.0.0.1:18080/completion",
                json={"prompt": self.prompt, "n_predict": 1024, "temperature": 0.7},
                timeout=180,
            )
            response.raise_for_status()
            data = response.json()
            self.response_ready.emit(data.get("content", "Модель не вернула ответ."))
        except Exception as exc:
            self.error_ready.emit(str(exc))


class ChatWindow(QMainWindow):
    """Standalone chat opened by a desktop shortcut."""

    def __init__(self, model_name, model_path):
        super().__init__()
        self.model_name = model_name
        self.model_path = model_path
        self.worker = None
        self.setWindowTitle(f"Chizhik AI — {model_name}")
        self.resize(900, 700)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        title = QLabel(model_name)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #4fc3f7;")
        layout.addWidget(title)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.messages = QWidget()
        self.messages_layout = QVBoxLayout(self.messages)
        self.messages_layout.addStretch()
        self.scroll.setWidget(self.messages)
        layout.addWidget(self.scroll)

        bottom = QHBoxLayout()
        self.input = QTextEdit()
        self.input.setMaximumHeight(90)
        self.input.setPlaceholderText("Введите сообщение…")
        bottom.addWidget(self.input)

        self.send = QPushButton("Отправить")
        self.send.setMinimumWidth(120)
        self.send.setMinimumHeight(44)
        self.send.clicked.connect(self.send_message)
        bottom.addWidget(self.send)
        layout.addLayout(bottom)

        self.setStyleSheet("QMainWindow, QWidget { background-color: #1e1e1e; color: white; } QTextEdit { background: #303030; }")

    def add_message(self, role, text):
        frame = QFrame()
        frame.setStyleSheet("background-color: #0e639c;" if role == "Вы" else "background-color: #3c3c3c;")
        frame_layout = QVBoxLayout(frame)
        label = QLabel(f"{role}: {text}")
        label.setWordWrap(True)
        frame_layout.addWidget(label)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, frame)

    def send_message(self):
        text = self.input.toPlainText().strip()
        if not text:
            return
        self.input.clear()
        self.add_message("Вы", text)
        self.send.setEnabled(False)

        self.worker = LlamaWorker(text, self.model_path)
        self.worker.response_ready.connect(self._response)
        self.worker.error_ready.connect(self._error)
        self.worker.start()

    def _response(self, text):
        self.send.setEnabled(True)
        self.add_message(self.model_name, text)

    def _error(self, text):
        self.send.setEnabled(True)
        self.add_message("Ошибка", text)
