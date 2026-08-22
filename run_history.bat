@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo           ЗАПУСК РЕЖИМА HISTORY (АНАЛИЗ ИСТОРИИ)
echo ============================================================
echo.

:: Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден в системе!
    echo.
    echo Установите Python 3.11 или выше с https://www.python.org/downloads/
    echo При установке отметьте галочку "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo [OK] Python найден
python --version

:: Создание виртуального окружения, если его нет
if not exist ".venv" (
    echo.
    echo [INFO] Создание виртуального окружения...
    python -m venv .venv
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось создать виртуальное окружение
        pause
        exit /b 1
    )
    echo [OK] Виртуальное окружение создано
) else (
    echo [OK] Виртуальное окружение уже существует
)

:: Активация виртуального окружения
call .venv\Scripts\activate.bat

:: Установка зависимостей
echo.
echo [INFO] Проверка зависимостей...
.venv\Scripts\pip.exe install -q -r requirements.txt
if errorlevel 1 (
    echo [ОШИБКА] Не удалось установить зависимости
    pause
    exit /b 1
)
echo [OK] Зависимости установлены

:: Проверка .env файла
if not exist "config\.env" (
    echo.
    echo ============================================================
    echo [ВНИМАНИЕ] Файл config\.env не найден!
    echo ============================================================
    echo.
    echo Необходимо настроить файл конфигурации:
    echo   1. Откройте файл config\.env.example в текстовом редакторе
    echo   2. Заполните все необходимые поля:
    echo      - TELEGRAM_API_ID и TELEGRAM_API_HASH (получить на https://my.telegram.org)
    echo      - TELEGRAM_SESSION (имя файла сессии)
    echo      - TELEGRAM_SOURCES (два канала через запятую)
    echo      - TELEGRAM_TARGET (куда пересылать сообщения)
    echo   3. Сохраните файл как config\.env
    echo.
    echo После этого запустите скрипт снова.
    echo.
    pause
    exit /b 1
) else (
    echo [OK] Файл config\.env найден
)

:: Проверка заполненности обязательных полей в .env
echo.
echo [INFO] Проверка настроек в config\.env...
findstr /B "^TELEGRAM_API_ID=" config\.env >nul
if errorlevel 1 (
    echo [ОШИБКА] В config\.env не заполнено TELEGRAM_API_ID
    pause
    exit /b 1
)

findstr /B "^TELEGRAM_API_HASH=" config\.env >nul
if errorlevel 1 (
    echo [ОШИБКА] В config\.env не заполнено TELEGRAM_API_HASH
    pause
    exit /b 1
)

findstr /B "^TELEGRAM_SOURCES=" config\.env >nul
if errorlevel 1 (
    echo [ОШИБКА] В config\.env не заполнено TELEGRAM_SOURCES
    pause
    exit /b 1
)

findstr /B "^TELEGRAM_TARGET=" config\.env >nul
if errorlevel 1 (
    echo [ОШИБКА] В config\.env не заполнено TELEGRAM_TARGET
    pause
    exit /b 1
)

echo [OK] Все обязательные настройки заполнены

:: Запуск режима history
echo.
echo ============================================================
echo [ЗАПУСК] Режим HISTORY - анализ истории сообщений
echo ============================================================
echo.
echo Будет проанализировано последних 500 сообщений из каждого источника.
echo Релевантные сообщения будут показаны в начале вывода.
echo.
echo Для остановки нажмите Ctrl+C
echo.

.venv\Scripts\python.exe monitor.py history --limit 500

if errorlevel 1 (
    echo.
    echo [ОШИБКА] Произошла ошибка при выполнении
    pause
    exit /b 1
)

echo.
echo ============================================================
echo [ЗАВЕРШЕНО] Анализ истории завершён
echo ============================================================
pause
