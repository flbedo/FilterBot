from __future__ import annotations

import argparse
import asyncio
import logging

from .monitor import Monitor
from .settings import load_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Мониторинг журналистских запросов в Telegram")
    parser.add_argument("mode", choices=["history", "live"], help="history = тестовая история, live = непрерывный мониторинг")
    parser.add_argument("--limit", type=int, default=None, help="Количество сообщений на источник в history")
    parser.add_argument("--env", default=None, help="Путь к .env")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    settings = load_settings(args.env)
    monitor = Monitor(settings)

    if args.mode == "history":
        asyncio.run(monitor.start_history(args.limit or settings.history_limit))
    else:
        try:
            asyncio.run(monitor.start_live())
        except KeyboardInterrupt:
            print("\nМониторинг остановлен пользователем.")


if __name__ == "__main__":
    main()
