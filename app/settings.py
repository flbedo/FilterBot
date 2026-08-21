from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
FILTERS_PATH = CONFIG_DIR / "filters.json"
DB_PATH = DATA_DIR / "monitor.db"


@dataclass(frozen=True)
class Settings:
    api_id: int
    api_hash: str
    session_name: str
    sources: list[str]
    target: str
    history_limit: int
    network_retries: int
    retry_base_seconds: float
    borderline_limit: int
    check_text_repeats: bool
    filters_path: Path = FILTERS_PATH
    db_path: Path = DB_PATH


def load_settings(env_file: str | None = None) -> Settings:
    load_dotenv(CONFIG_DIR / ".env")

    required = ["TELEGRAM_API_ID", "TELEGRAM_API_HASH", "TELEGRAM_SESSION", "TELEGRAM_SOURCES", "TELEGRAM_TARGET"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise RuntimeError("Не заполнены переменные .env: " + ", ".join(missing))

    sources = [item.strip() for item in os.environ["TELEGRAM_SOURCES"].split(",") if item.strip()]

    # Следующую строчку можно закомментировать. Ограничение в 2 - чисто желание заказчика, это не архитекторное ограничение
    if len(sources) != 2: raise RuntimeError("TELEGRAM_SOURCES должен содержать ровно два источника через запятую")

    DATA_DIR.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)

    return Settings(
        api_id=int(os.environ["TELEGRAM_API_ID"]),
        api_hash=os.environ["TELEGRAM_API_HASH"],
        session_name=os.environ["TELEGRAM_SESSION"],
        sources=sources,
        target=os.environ["TELEGRAM_TARGET"],
        history_limit=int(os.getenv("HISTORY_LIMIT", "500")),
        network_retries=int(os.getenv("NETWORK_RETRIES", "5")),
        retry_base_seconds=float(os.getenv("NETWORK_RETRY_BASE_SECONDS", "3")),
        borderline_limit=int(os.getenv("BORDERLINE_LIMIT", "10")),
        check_text_repeats=bool(int(os.getenv("CHECK_TEXT_REPEATS", "0")))
    )


def load_filters(path: Path = FILTERS_PATH) -> dict:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    for key in ("request_keywords", "exclusions", "topic_groups"):
        if key not in data:
            raise ValueError(f"В filters.json отсутствует ключ: {key}")
    return data
