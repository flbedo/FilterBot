from __future__ import annotations
import logging
from pathlib import Path
from datetime import datetime
import pytz
import functools

from .easydata import create_database, is_id_exist, give_id_data, get_ids_by_item

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

        self.f_name = str(self.path).removesuffix('.db')
            
        create_database(self.f_name)

    @functools.cache
    def is_processed(self, source_key: str, message_id: int, message_text: str, check_message_text: bool) -> bool:
        record_id = f"{source_key}:{message_id}"

        same_messages_exist = False
        if check_message_text:
            same_messages_exist = get_ids_by_item(self.f_name, 'message_text', message_text) != {}

        return is_id_exist(self.f_name, record_id) and not(same_messages_exist)

    def mark_processed(self, source_key: str, message_id: int, message_text: str, sent: bool) -> None:
        record_id = f"{source_key}:{message_id}"
        
        value = datetime.now(pytz.timezone("Europe/Moscow")).strftime('%H:%M %d.%m') if sent else None
        message_data = {
            "message_text": message_text,
            "sent_at": value,
            "source": source_key,
        }

        give_id_data(self.f_name, record_id, message_data)
