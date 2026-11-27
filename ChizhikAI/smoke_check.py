import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db import Database
from ui.main_window import MainWindow


def smoke_check():
    db = Database()
    assert db.get_chats() == db.get_chats()


if __name__ == '__main__':
    smoke_check()
    print('ChizhikAI startup smoke check: OK')
