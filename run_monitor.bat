@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo           ЗАПУСК РЕЖИМА LIVE (НЕПРЕРЫВНЫЙ МОНИТОРИНГ)
echo ============================================================
echo.

:: Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден!
    pause
    exit /b 1
)
echo [OK] Python найден

:: Venv
if not exist ".venv" (
    echo [INFO] Создание виртуального окружения...
    python -m venv .venv
)
call .venv\Scripts\activate.bat

:: Зависимости
echo [INFO] Установка зависимостей...
.venv\Scripts\pip.exe install -q -r requirements.txt
echo [OK] Зависимости установлены
echo.

:: Поиск .env (без вложенных if, чтобы cmd не падал)
echo [INFO] Поиск файла конфигурации...
set "ENV_FILE="
if exist ".env" set "ENV_FILE=.env"
if exist "config\.env" set "ENV_FILE=config\.env"

if "%ENV_FILE%"=="" (
    echo [ОШИБКА] Файл .env не найден ни в корне, ни в папке config!
    echo Создайте файл .env и заполните его.
    pause
    exit /b 1
)
echo [OK] Найден файл конфигурации: %ENV_FILE%

:: Проверка ключей (без символа ^, чтобы не бояться BOM и пробелов)
echo [INFO] Проверка настроек...
findstr "TELEGRAM_API_ID=" "%ENV_FILE%" >nul || (echo [ОШИБКА] Нет TELEGRAM_API_ID & pause & exit /b 1)
findstr "TELEGRAM_API_HASH=" "%ENV_FILE%" >nul || (echo [ОШИБКА] Нет TELEGRAM_API_HASH & pause & exit /b 1)
findstr "TELEGRAM_SOURCES=" "%ENV_FILE%" >nul || (echo [ОШИБКА] Нет TELEGRAM_SOURCES & pause & exit /b 1)
findstr "TELEGRAM_TARGET=" "%ENV_FILE%" >nul || (echo [ОШИБКА] Нет TELEGRAM_TARGET & pause & exit /b 1)
echo [OK] Все настройки найдены
echo.

:: Запуск
echo ============================================================
echo [ЗАПУСК] Режим LIVE - непрерывный мониторинг
echo ============================================================
echo.

.venv\Scripts\python.exe monitor.py live

if errorlevel 1 (
    echo.
    echo [ОШИБКА] Скрипт завершился с ошибкой
    pause
    exit /b 1
)

echo.
echo [ЗАВЕРШЕНО]
pause