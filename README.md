# Telegram Journalist Monitor

Локальная многомодульная Python-система для мониторинга двух Telegram-источников и пересылки только релевантных журналистских запросов в рабочую группу.

## Что реализовано

- Telethon и пользовательская Telegram-сессия.
- Два источника из `.env`.
- Одновременное условие фильтра: признак журналистского запроса **И** тематическая релевантность.
- Отдельный редактируемый `config/filters.json`.
- Текст обычных сообщений и caption у медиа обрабатываются одинаково.
- Форварды отмечаются в поле источника.
- Сообщения без текста не отправляются.
- Дедупликация по `(source_key, message_id)` в SQLite, переживающая перезапуск.
- `history` для анализа истории (по умолчанию 500 на источник) с пояснением, почему сообщение прошло/не прошло фильтр.
- Вывод 5-10 пограничных сообщений из реальной загруженной истории, если они есть.
- `live` для непрерывного мониторинга.
- FloodWait и временные сетевые/RPC-ошибки обрабатываются с ожиданием и повтором.
- Windows-запуск через `.bat`.
- Секреты и `.session` исключены из репозитория.

## Структура

```text
telegram_journalist_monitor/
  app/
    __init__.py
    cli.py
    easydata.py
    database.py
    filters.py
    formatter.py
    models.py
    monitor.py
    settings.py
    telegram_client.py
  config/
    filters.json
    .env.example
  data/
  logs/
  tests/
    __init__.py
    test_filters.py
  .gitignore
  monitor.py
  requirements.txt
  run_history.bat
  run_monitor.bat
  README.md
```

## Установка и авторизация

1. Установите Python 3.11+ на Windows.
2. Заполните `.env.example`, а затем переименуйте в `.env`.
3. Заполните `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_SOURCES` и `TELEGRAM_TARGET`.
4. Запустите `run_history.bat` или `run_monitor.bat`.
5. При первом запуске Telethon попросит номер телефона, код Telegram и при необходимости пароль 2FA.

Для диагностики можно использовать `python monitor.py live --log-level DEBUG`.

## Калибровка фильтра

Редактируйте только `config/filters.json`: `request_keywords`, `exclusions` и `topic_groups`. Основная логика кода при этом не меняется. Слова нужно вводить в именительном падеже - в системе предустмотрена лемматизация.
