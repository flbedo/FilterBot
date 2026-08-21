from __future__ import annotations

import asyncio
import logging

from .database import Database
from .filters import evaluate
from .formatter import format_notification, format_test_line
from .models import MessageData
from .settings import Settings, load_filters
from .telegram_client import TelegramService

logger = logging.getLogger(__name__)


class Monitor:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.filters = load_filters(settings.filters_path)
        self.db = Database(settings.db_path)
        self.telegram = TelegramService(settings)

    async def close(self) -> None:
        await self.telegram.disconnect()

    async def start_history(self, limit: int) -> None:
        await self.telegram.connect()
        total = relevant = 0
        borderline: list[tuple[MessageData, object]] = []
        relevant_messages: list[tuple[MessageData, object]] = []

        try:
            for source in self.settings.sources:
                messages = await self.telegram.history(source, limit)
                logger.info("%s: загружено %s сообщений", source, len(messages))
                for message in messages:
                    total += 1
                    result = evaluate(message.text, self.filters)
                    if result.is_relevant:
                        relevant += 1
                        relevant_messages.append((message, result))

                    elif self._is_borderline(result) and len(borderline) < self.settings.borderline_limit:
                        # Это пограничные примеры по желанию заказчика. Тут нет никакого скрытого смысла
                        borderline.append((message, result))

            # Сначала выводим только релевантные сообщения
            print(f"\n=== РЕЛЕВАНТНЫЕ СООБЩЕНИЯ ({len(relevant_messages)}) ===", flush=True)
            if relevant_messages:
                for message, result in relevant_messages:
                    print(format_test_line(message, result), flush=True)
            else:
                print("Релевантных сообщений не найдено в выбранной истории.", flush=True)

            # Затем пограничные примеры
            print(f"\n=== ПОГРАНИЧНЫЕ ПРИМЕРЫ ({len(borderline)}) ===", flush=True)
            if borderline:
                for message, result in borderline:
                    print(format_test_line(message, result), flush=True)
            else:
                print("Пограничных примеров не найдено в выбранной истории.", flush=True)

            # Итоговая статистика
            print(f"\nИТОГО: проверено {total}, релевантных {relevant}", flush=True)
        finally:
            await self.close()

    async def start_live(self) -> None:
        handler_registered = False
        try:
            while True:
                try:
                    await self.telegram.connect()
                    if not handler_registered:
                        self.telegram.watch(self.process_message)
                        handler_registered = True
                    logger.info("Live-мониторинг запущен")
                    await self.telegram.run_until_disconnected()
                    logger.warning("Соединение Telegram завершилось. Попытка переподключения...")
                except asyncio.CancelledError:
                    raise
                except Exception:
                    logger.exception("Live-цикл получил ошибку; мониторинг не будет завершён")
                await asyncio.sleep(self.settings.retry_base_seconds)
        finally:
            await self.telegram.disconnect()

    async def process_message(self, message: MessageData) -> None:
        if self.db.is_processed(message.source_key, message.message_id, message.text, self.settings.check_text_repeats):
            logger.debug("Дубль пропущен: %s:%s", message.source_key, message.message_id)
            return

        result = evaluate(message.text, self.filters)
        if result.is_relevant:
            await self.telegram.send(format_notification(message))
            self.db.mark_processed(message.source_key, message.message_id, message.text, sent=True)
            logger.info("Отправлено в целевую группу: %s:%s", message.source_key, message.message_id)
        else:
            # Фиксируем даже нерелевантные сообщения, чтобы повторная доставка события
            # после реконнекта не прогоняла их заново.
            self.db.mark_processed(message.source_key, message.message_id, message.text, sent=False)

    @staticmethod
    def _is_borderline(result) -> bool:
        return (result.request_match != result.topic_match) and not result.excluded
