from __future__ import annotations

import re
from typing import Iterable

from .models import FilterResult


def normalize(text: str) -> str:
    text = text.lower().replace("ё", "е")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _matched_keywords(text: str, keywords: Iterable[str]) -> list[str]:
    return [kw for kw in keywords if normalize(kw) in text]


def evaluate(text: str, config: dict) -> FilterResult:
    normalized = normalize(text)
    request_matches = _matched_keywords(normalized, config["request_keywords"])
    exclusion_matches = _matched_keywords(normalized, config.get("exclusions", []))

    matched_groups: list[str] = []
    for group, keywords in config["topic_groups"].items():
        if _matched_keywords(normalized, keywords):
            matched_groups.append(group)

    request_match = bool(request_matches)
    topic_match = bool(matched_groups)
    excluded = bool(exclusion_matches)
    relevant = request_match and topic_match and not excluded

    if relevant:
        reason = (
            "Есть признаки журналистского запроса: " + ", ".join(request_matches[:4]) +
            "; есть тематическое совпадение: " + ", ".join(matched_groups)
        )
    elif excluded:
        reason = "Сообщение содержит исключающий признак: " + ", ".join(exclusion_matches)
    elif not request_match and not topic_match:
        reason = "Нет ни признака журналистского запроса, ни тематического совпадения"
    elif not request_match:
        reason = "Тема релевантна, но не найден признак журналистского запроса"
    else:
        reason = "Есть признак журналистского запроса, но тема не входит в заданные группы"

    return FilterResult(
        is_relevant=relevant,
        request_match=request_match,
        topic_match=topic_match,
        excluded=excluded,
        request_keywords=request_matches,
        topic_groups=matched_groups,
        exclusion_keywords=exclusion_matches,
        reason=reason,
    )
