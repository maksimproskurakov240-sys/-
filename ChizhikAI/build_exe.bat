@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel% neq 0 (
    echo [ОШИБКА] Python не найден в PATH.
    pause
    exit /b 1
)

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install --upgrade pyinstaller

if %errorlevel% neq 0 (
    echo [ОШИБКА] Не удалось установить зависимости.
    pause
    exit /b 1
)

python -m PyInstaller --clean --noconfirm build.spec
if %errorlevel% neq 0 (
    echo [ОШИБКА] Сборка PyInstaller завершилась с ошибкой.
    pause
    exit /b 1
)

echo.
echo [ГОТОВО] dist\Chizhik_AI.exe
pause
