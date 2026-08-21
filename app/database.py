from __future__ import annotations
import logging
from pathlib import Path
from datetime import datetime
import pytz

from .easydata import create_database, is_id_exist, give_id_data, get_ids_by_item

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

        self.f_name = str(self.path).removesuffix('.db')

        create_database(self.f_name)

    def is_processed(self, source_key: str, message_id: int, message_text: str, check_message_text: bool) -> bool:
        """Проверяет, было ли сообщение уже обработано.

        В live режиме (check_message_text=True) также проверяет на повтор текста сообщения.
        """
        record_id = f"{source_key}:{message_id}"

        id_exists = is_id_exist(self.f_name, record_id)

        if not check_message_text: return id_exists

        # Логика live режима
        if id_exists: return True

        # Проверяем, есть ли сообщения с таким же текстом
        same_messages_exist = get_ids_by_item(self.f_name, 'message_text', message_text) != {}
        return same_messages_exist

    def mark_processed(self, source_key: str, message_id: int, message_text: str, sent: bool) -> None:
        record_id = f"{source_key}:{message_id}"

        value = datetime.now(pytz.timezone("Europe/Moscow")).strftime('%H:%M %d.%m') if sent else None
        message_data = {
            "message_text": message_text,
            "sent_at": value,
            "source": source_key,
        }

        give_id_data(self.f_name, record_id, message_data)
