# from __future__ import annotations

# import easydata as ed
# from pathlib import Path


# class Database:
#     def __init__(self, path: Path):
#         self.path = path
#         self.path.parent.mkdir(parents=True, exist_ok=True)
#         self.conn = sqlite3.connect(self.path)
#         self.conn.execute("PRAGMA journal_mode=WAL")
#         self.conn.execute("PRAGMA synchronous=NORMAL")
#         self._create_schema()

#     def _create_schema(self) -> None:
#         self.conn.execute(
#             """
#             CREATE TABLE IF NOT EXISTS processed_messages (
#                 source_key TEXT NOT NULL,
#                 message_id INTEGER NOT NULL,
#                 processed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
#                 sent_at TEXT,
#                 PRIMARY KEY (source_key, message_id)
#             )
#             """
#         )
#         self.conn.commit()

#     def is_processed(self, source_key: str, message_id: int) -> bool:
#         row = self.conn.execute(
#             "SELECT 1 FROM processed_messages WHERE source_key=? AND message_id=?",
#             (source_key, message_id),
#         ).fetchone()
#         return row is not None

#     def mark_processed(self, source_key: str, message_id: int, sent: bool) -> None:
#         self.conn.execute(
#             """
#             INSERT OR IGNORE INTO processed_messages(source_key, message_id, sent_at)
#             VALUES (?, ?, CASE WHEN ? THEN CURRENT_TIMESTAMP ELSE NULL END)
#             """,
#             (source_key, message_id, int(sent)),
#         )
#         self.conn.commit()

#     def close(self) -> None:
#         self.conn.close()

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
    def is_processed(self, source_key: str, message_id: int, message_text: str, check_message_text=True) -> bool:
        record_id = f"{source_key}:{message_id}"

        same_messages_exist = True
        if check_message_text:
            same_messages_exist = get_ids_by_item(self.f_name, 'message_text', message_text) != {}

        return is_id_exist(self.f_name, record_id) and same_messages_exist

    def mark_processed(self, source_key: str, message_id: int, message_text: str, sent: bool) -> None:
        record_id = f"{source_key}:{message_id}"
        
        value = datetime.now(pytz.timezone("Europe/Moscow")).strftime('%H:%M %d.%m') if sent else None
        message_data = {
            "message_text": message_text,
            "sent_at": value
        }

        give_id_data(self.f_name, record_id, message_data)
