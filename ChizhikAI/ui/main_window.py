from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QListWidget, QListWidgetItem, QPushButton, QStackedWidget, QLabel)
from PyQt5.QtCore import Qt
from ui.chat_widget import ChatWidget
from ui.download_dialog import DownloadDialog

class MainWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Чижик Инсталлер")
        self.resize(1200, 800)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Левая панель (кнопки)
        left_panel = QWidget()
        left_panel.setFixedWidth(250)
        left_panel.setStyleSheet("background-color: #252526; border-right: 1px solid #3c3c3c;")
        left_layout = QVBoxLayout(left_panel)
        
        lbl_menu = QLabel("ГЛАВНОЕ МЕНЮ")
        lbl_menu.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: bold; padding: 10px;")
        left_layout.addWidget(lbl_menu)

        btn_new_chat = QPushButton("+ Новый чат")
        btn_new_chat.setStyleSheet("color: white; background-color: #0e639c; padding: 10px; border-radius: 5px; font-weight: bold;")
        btn_new_chat.clicked.connect(self.create_new_chat)
        left_layout.addWidget(btn_new_chat)
        
        btn_download = QPushButton("⬇ Менеджер ИИ")
        btn_download.setStyleSheet("color: white; background-color: #2d2d2d; padding: 10px; border-radius: 5px;")
        btn_download.clicked.connect(self.open_download_manager)
        left_layout.addWidget(btn_download)

        self.list_chats = QListWidget()
        self.list_chats.setStyleSheet("color: white; background-color: #1e1e1e; border: none;")
        self.list_chats.itemClicked.connect(self.load_chat)
        left_layout.addWidget(self.list_chats)
        
        main_layout.addWidget(left_panel)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: #1e1e1e;")
        main_layout.addWidget(self.stack, 1)
        self.load_chats_list()

    def load_chats_list(self):
        self.list_chats.clear()
        chats = self.db.get_chats()
        for chat_id, title in chats:
            item = QListWidgetItem(title)
            item.setData(Qt.UserRole, chat_id)
            self.list_chats.addItem(item)

    def create_new_chat(self):
        chat_id = self.db.create_chat("Новый диалог")
        self.load_chats_list()
        self.open_chat(chat_id)

    def load_chat(self, item):
        self.open_chat(item.data(Qt.UserRole))

    def open_chat(self, chat_id):
        chat_widget = ChatWidget(self.db, chat_id)
        self.stack.addWidget(chat_widget)
        self.stack.setCurrentWidget(chat_widget)

    def open_download_manager(self):
        dialog = DownloadDialog(self)
        dialog.exec_()