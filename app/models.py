from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class FilterResult:
    is_relevant: bool
    request_match: bool
    topic_match: bool
    excluded: bool
    request_keywords: list[str]
    topic_groups: list[str]
    exclusion_keywords: list[str]
    reason: str


@dataclass(frozen=True)
class MessageData:
    source_key: str
    source_name: str
    message_id: int
    text: str
    date: datetime
    link: str | None
    is_forwarded: bool
    forwarded_from: str | None
