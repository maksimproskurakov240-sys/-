@echo off
title СБОРКА CHIZHIK AI (PYQT5)
echo Установка зависимостей...
pip install PyQt5==5.15.10 pywin32 winshell keyboard

echo.
echo Сборка EXE файла...
pyinstaller --noconfirm --onefile --windowed --name "Chizhik_AI" --hidden-import pkgutil main.py

echo.
echo [ГОТОВО] Файл лежит в папке dist/Chizhik_AI.exe
pause