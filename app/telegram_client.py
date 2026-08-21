from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, RPCError

from .models import MessageData
from .settings import Settings

logger = logging.getLogger(__name__)
MessageHandler = Callable[[MessageData], Awaitable[None]]


class TelegramService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = TelegramClient(settings.session_name, settings.api_id, settings.api_hash, proxy=("socks5", "127.0.0.1", 10808))
        self.source_entities: dict[str, object] = {}
        self.target_entity: object | None = None

    async def connect(self) -> None:
        await self.client.start()
        if not await self.client.is_user_authorized():
            raise RuntimeError("Telegram-сессия не авторизована. Запустите программу вручную и пройдите авторизацию.")

        for source in self.settings.sources:
            self.source_entities[source] = await self._with_retries(lambda s=source: self.client.get_entity(s))
            logger.info("Источник доступен: %s", source)

        self.target_entity = await self._with_retries(lambda: self.client.get_entity(self.settings.target))
        logger.info("Целевая группа доступна: %s", self.settings.target)

    async def disconnect(self) -> None:
        await self.client.disconnect()

    async def history(self, source: str, limit: int) -> list[MessageData]:
        entity = self.source_entities[source]

        async def collect() -> list[MessageData]:
            result: list[MessageData] = []
            async for message in self.client.iter_messages(entity, limit=limit):
                data = self.to_message_data(source, entity, message)
                if data is not None:
                    result.append(data)
            return result

        return await self._with_retries(collect)

    def watch(self, handler: MessageHandler) -> None:
        entities = list(self.source_entities.values())

        @self.client.on(events.NewMessage(chats=entities))
        async def new_message(event):
            source_key = self._source_key_from_event(event)
            data = self.to_message_data(source_key, event.chat, event.message)
            if data is None:
                return
            try:
                await handler(data)
            except Exception:
                logger.exception("Ошибка обработки сообщения %s:%s", data.source_key, data.message_id)

    async def send(self, text: str) -> None:
        if self.target_entity is None:
            raise RuntimeError("Целевая группа не инициализирована")
        await self._with_retries(lambda: self.client.send_message(self.target_entity, text, link_preview=False))

    async def run_until_disconnected(self) -> None:
        await self.client.run_until_disconnected()

    def to_message_data(self, source_key: str, entity: object, message: object) -> MessageData | None:
        text = (getattr(message, "message", None) or "").strip()
        if not text:
            return None

        source_name = getattr(entity, "title", None) or getattr(entity, "username", None) or str(source_key)
        link = self._message_link(entity, getattr(message, "id", None))
        is_forwarded = getattr(message, "fwd_from", None) is not None
        forwarded_from = self._forwarded_source(message) if is_forwarded else None
        return MessageData(
            source_key=str(source_key),
            source_name=str(source_name),
            message_id=int(message.id),
            text=text,
            date=message.date,
            link=link,
            is_forwarded=is_forwarded,
            forwarded_from=forwarded_from,
        )

    @staticmethod
    def _forwarded_source(message: object) -> str | None:
        fwd = getattr(message, "fwd_from", None)
        if fwd is None:
            return None
        title = getattr(fwd, "from_name", None)
        if title:
            return str(title)
        chat = getattr(fwd, "from_id", None)
        return str(chat) if chat else "неизвестный источник"

    @staticmethod
    def _message_link(entity: object, message_id: int | None) -> str | None:
        if not message_id:
            return None
        username = getattr(entity, "username", None)
        if username:
            return f"https://t.me/{username}/{message_id}"
        channel_id = getattr(entity, "id", None)
        if channel_id:
            # Telegram private channel links use -100 + numeric id without the -100 prefix.
            value = str(channel_id).replace("-100", "", 1) if str(channel_id).startswith("-100") else str(channel_id)
            return f"https://t.me/c/{value}/{message_id}"
        return None

    def _source_key_from_event(self, event: object) -> str:
        chat = getattr(event, "chat", None)
        username = getattr(chat, "username", None)
        if username:
            candidate = f"@{username}"
            if candidate in self.source_entities:
                return candidate
        chat_id = getattr(chat, "id", None)
        for key, entity in self.source_entities.items():
            if getattr(entity, "id", None) == chat_id:
                return key
        return str(chat_id)

    async def _with_retries(self, func):
        for attempt in range(1, self.settings.network_retries + 1):
            try:
                return await func()
            except FloodWaitError as exc:
                wait_for = int(exc.seconds) + 1
                logger.warning("FloodWait: Telegram попросил подождать %s сек.", wait_for)
                await asyncio.sleep(wait_for)
            except (OSError, RPCError) as exc:
                if attempt >= self.settings.network_retries:
                    raise
                delay = self.settings.retry_base_seconds * attempt
                logger.warning("Сетевая/RPC ошибка: %s. Повтор через %.1f сек.", exc, delay)
                await asyncio.sleep(delay)
        raise RuntimeError("Операция не выполнена после всех повторов")
