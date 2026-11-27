import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Chizhik AI")

    if "--chat" in sys.argv:
        try:
            index = sys.argv.index("--chat")
            model_path = sys.argv[index + 1]
            model_name = sys.argv[index + 2]
        except (ValueError, IndexError):
            model_path = ""
            model_name = "Chizhik AI"

        from ui.chat_widget import ChatWindow
        window = ChatWindow(model_name, model_path)
        window.show()
        return app.exec_()

    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
