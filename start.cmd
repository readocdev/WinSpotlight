@echo off
chcp 65001 >nul
title WinSpotlight Launcher
cd /d "%~dp0"

echo ##############################################
echo #                                            #
echo #        WINSPOTLIGHT SYSTEM STARTUP         #
echo #                                            #
echo ##############################################
echo.
echo [+] Инициализация пути: %~dp0

if exist .venv\ (
    echo [+] Активация виртуального окружения .venv...
    call .venv\Scripts\activate
    
    echo [+] Проверка и установка зависимостей...
    pip install -r requirements.txt
) else (
    echo [!] Предупреждение: .venv не найден.
    echo [+] Попытка установки библиотек в глобальный Python...
    pip install -r requirements.txt
)

echo.
echo [+] Запуск основного модуля main.py...
echo.
echo -----------------------------------------------------
echo    Hotkeys: [Alt+Z] - Overlay ^| [Alt+E] - Eject USB
echo    Статус: ПРИЛОЖЕНИЕ АКТИВНО
echo -----------------------------------------------------

python main.py

echo.
echo ----------------------------------------------------
echo [!] Работа программы завершена или прервана.
pause
