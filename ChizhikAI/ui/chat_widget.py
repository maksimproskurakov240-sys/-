import os
import urllib.request
import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                             QPushButton, QFileDialog, QLabel, QScrollArea, QFrame)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# Текст запроса к локальному серверу llama.cpp
class AIChatWorker(QThread):
    response_ready = pyqtSignal(str)
    
    def __init__(self, prompt):
        super().__init__()
        self.prompt = prompt

    def run(self):
        try:
            # Отправляем POST запрос на локальный сервер (порт 8080)
            url = "http://127.0.0.1:8080/completion"
            data = {
                "prompt": self.prompt,
                "temperature": 0.7,
                "max_tokens": 1024
            }
            req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
                self.response_ready.emit(result.get("content", "Ошибка чтения ответа"))
        except Exception as e:
            self.response_ready.emit(f"[Ошибка подключения к ИИ: {e}]\nУбедитесь, что модель запущена (через ярлык на рабочем столе).")

class ChatWidget(QWidget):
    def __init__(self, db, chat_id):
        super().__init__()
        self.db = db
        self.chat_id = chat_id
        self.media_path = None
        self.init_ui()
        self.load_messages()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.msg_container = QWidget()
        self.msg_layout = QVBoxLayout(self.msg_container)
        self.msg_layout.addStretch()
        self.scroll.setWidget(self.msg_container)
        layout.addWidget(self.scroll)

        input_layout = QHBoxLayout()
        
        self.btn_attach = QPushButton("📎")
        self.btn_attach.setFixedSize(40, 40)
        self.btn_attach.clicked.connect(self.attach_file)
        input_layout.addWidget(self.btn_attach)

        self.input_field = QTextEdit()
        self.input_field.setMaximumHeight(60)
        self.input_field.setPlaceholderText("Введите сообщение...")
        self.input_field.setStyleSheet("color: white; background-color: #3c3c3c;")
        input_layout.addWidget(self.input_field)

        self.btn_send = QPushButton("Отправить")
        self.btn_send.setStyleSheet("color: white; background-color: #0e639c;")
        self.btn_send.clicked.connect(self.send_message)
        input_layout.addWidget(self.btn_send)

        layout.addLayout(input_layout)

    def attach_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", "Images/Videos (*.png *.jpg *.jpeg *.mp4)")
        if file_path:
            self.media_path = file_path
            self.input_field.setPlaceholderText(f"Прикреплено: {os.path.basename(file_path)}")

    def send_message(self):
        text = self.input_field.toPlainText().strip()
        if not text: return

        self.db.add_message(self.chat_id, "user", text)
        self.add_message_bubble("user", text)
        
        self.input_field.clear()
        
        # Запускаем поток запроса к ИИ
        self.ai_worker = AIChatWorker(text)
        self.ai_worker.response_ready.connect(self.receive_ai_response)
        self.ai_worker.start()

    def receive_ai_response(self, response):
        self.db.add_message(self.chat_id, "ai", response)
        self.add_message_bubble("ai", response)

    def add_message_bubble(self, role, text):
        bubble = QFrame()
        bubble.setStyleSheet(f"QFrame {{ background-color: {'#0e639c' if role == 'user' else '#3c3c3c'}; border-radius: 10px; padding: 10px; margin: 5px; }}")
        bubble_layout = QVBoxLayout(bubble)
        
        msg_label = QLabel(text)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet("color: white;")
        bubble_layout.addWidget(msg_label)
        
        h_layout = QHBoxLayout()
        if role == "user":
            h_layout.addStretch()
            h_layout.addWidget(bubble)
        else:
            h_layout.addWidget(bubble)
            h_layout.addStretch()
            
        wrapper = QWidget()
        wrapper.setLayout(h_layout)
        self.msg_layout.insertWidget(self.msg_layout.count() - 1, wrapper)
        
        # Автоскролл вниз
        QTimer.singleShot(100, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        scrollbar = self.scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def load_messages(self):
        for i in reversed(range(self.msg_layout.count() - 1)): 
            widget = self.msg_layout.itemAt(i).widget()
            if widget: widget.deleteLater()
            
        messages = self.db.get_messages(self.chat_id)
        for role, content, media in messages:
            self.add_message_bubble(role, content)