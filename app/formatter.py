from __future__ import annotations

from datetime import timezone
from zoneinfo import ZoneInfo

from .models import MessageData

MSK = ZoneInfo("Europe/Moscow")


def format_notification(message: MessageData) -> str:
    date = message.date
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    date_msk = date.astimezone(MSK).strftime("%d.%m.%Y %H:%M")

    source_line = f"Источник: {message.source_name}"
    if message.is_forwarded and message.forwarded_from:
        source_line += f" (переслано из: {message.forwarded_from})"

    link_line = f"Ссылка: {message.link}" if message.link else "Ссылка: недоступна"
    return "\n".join(
        [
            "🔔 Новый запрос СМИ",
            message.text,
            source_line,
            f"Дата: {date_msk} (МСК)",
            link_line,
        ]
    )


def format_test_line(message: MessageData, result) -> str:
    status = "✅ РЕЛЕВАНТНО" if result.is_relevant else "⛔ НЕ РЕЛЕВАНТНО"
    preview = " ".join(message.text.split())
    if len(preview) > 180:
        preview = preview[:177] + "..."

    link_info = f" | {message.link}" if message.link and result.is_relevant else ""

    return (
        f"{status} | {message.source_name} | id={message.message_id}{link_info}\n"
        f"Почему: {result.reason}\n"
        f"Текст: {preview}\n"
    )
