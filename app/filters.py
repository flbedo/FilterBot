# from __future__ import annotations
# import re
# from typing import Iterable, List
# from .models import FilterResult
# import pymorphy3

# morph = pymorphy3.MorphAnalyzer()
# # Если кто-то это читает, то да, полиморф не такой уж и крутой, так еще и инициировать при импорте - такое себе решение
# # Но оно работает и работает нормально (он быстренький), а я ленивый, чтобы придумывать чет новое

# def normalize(text: str) -> str:
#     text = text.lower().replace("ё", "е")
#     text = re.sub(r"\s+", " ", text)
#     return text.strip()

# def get_lemmas(text: str) -> set[str]:
#     words = re.findall(r'\b\w+\b', text.lower().replace("ё", "е"))
#     return {morph.parse(word)[0].normal_form for word in words if word.isalpha()}

# def _check_keyword_in_text(keyword: str, text_lemmas: set[str]) -> bool:
#     keyword_lemmas = get_lemmas(keyword)

#     return keyword_lemmas.issubset(text_lemmas)

# def evaluate(text: str, config: dict) -> FilterResult:
#     text_lemmas = get_lemmas(text)
#     # normalized_text = normalize(text)
    
#     request_matches = [
#         kw for kw in config["request_keywords"] 
#         if _check_keyword_in_text(kw, text_lemmas)
#     ]
    
#     exclusion_matches = [
#         kw for kw in config.get("exclusions", []) 
#         if _check_keyword_in_text(kw, text_lemmas)
#     ]
    
#     matched_groups: list[str] = []
#     for group, keywords in config["topic_groups"].items():

#         # Тут мы проверяем, есть ли хотя бы одно ключевое слово из группы в тексте. Хз насколько эт эффективно, но пока так
#         if any(_check_keyword_in_text(kw, text_lemmas) for kw in keywords):
#             matched_groups.append(group)

#     request_match = bool(request_matches)
#     topic_match = bool(matched_groups)
#     excluded = bool(exclusion_matches)
    
#     relevant = request_match and topic_match and not excluded

#     if relevant:
#         reason = (
#             "Есть признаки журналистского запроса: " + ", ".join(request_matches[:4]) +
#             "; есть тематическое совпадение: " + ", ".join(matched_groups)
#         )
#     elif excluded:
#         reason = "Сообщение содержит исключающий признак: " + ", ".join(exclusion_matches)
#     elif not request_match and not topic_match:
#         reason = "Нет ни признака журналистского запроса, ни тематического совпадения"
#     elif not request_match:
#         reason = "Тема релевантна, но не найден признак журналистского запроса"
#     else:
#         reason = "Есть признак журналистского запроса, но тема не входит в заданные группы"

#     return FilterResult(
#         is_relevant=relevant,
#         request_match=request_match,
#         topic_match=topic_match,
#         excluded=excluded,
#         request_keywords=request_matches,
#         topic_groups=matched_groups,
#         exclusion_keywords=exclusion_matches,
#         reason=reason,
#     )

from __future__ import annotations
import re
from typing import Iterable, List
from .models import FilterResult
import pymorphy3

# Если кто-то это читает, то да, полиморф не такой уж и крутой, так еще и инициировать при импорте - такое себе решение
# Но оно работает и работает нормально (он быстренький), а я ленивый, чтобы придумывать чет новое
morph = pymorphy3.MorphAnalyzer()

# Кэш для лемматизированного конфига. Ключ - id объекта конфига.
# Это позволяет лемматизировать слова из JSON только один раз (при старте/первом вызове), 
# а не на каждом входящем сообщении. Если конфиг перезагрузится из файла, id изменится и кэш обновится.
_config_lemmas_cache = {}

def _prepare_config_lemmas(config: dict) -> dict:
    config_id = id(config)
    if config_id not in _config_lemmas_cache:
        _config_lemmas_cache[config_id] = {
            "request": {kw: get_lemmas(kw) for kw in config.get("request_keywords", [])},
            "exclusions": {kw: get_lemmas(kw) for kw in config.get("exclusions", [])},
            "topics": {
                group: {kw: get_lemmas(kw) for kw in keywords} 
                for group, keywords in config.get("topic_groups", {}).items()
            }
        }
    return _config_lemmas_cache[config_id]

def normalize(text: str) -> str:
    text = text.lower().replace("ё", "е")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def get_lemmas(text: str) -> set[str]:
    words = re.findall(r'\b\w+\b', text.lower().replace("ё", "е"))
    return {morph.parse(word)[0].normal_form for word in words if word.isalpha()}

def _check_keyword_in_text(keyword_lemmas: set[str], text_lemmas: set[str]) -> bool:
    return keyword_lemmas.issubset(text_lemmas)

def evaluate(text: str, config: dict) -> FilterResult:
    text_lemmas = get_lemmas(text)
    
    # Получаем заранее лемматизированный конфиг (сработает один раз при первом вызове)
    cfg_lemmas = _prepare_config_lemmas(config)
    
    # Словарь сохраняет связь: {оригинальная_строка_из_json: набор_ее_лемм}
    # Тут забираем оригинальные ключевые слова
    request_matches = [
        kw for kw, lemmas in cfg_lemmas["request"].items() 
        if _check_keyword_in_text(lemmas, text_lemmas)
    ]
    
    exclusion_matches = [
        kw for kw, lemmas in cfg_lemmas["exclusions"].items() 
        if _check_keyword_in_text(lemmas, text_lemmas)
    ]
    
    matched_groups: list[str] = []
    matched_topic_keywords: list[str] = []
    
    for group, topic_keywords_lemmas in cfg_lemmas["topics"].items():
        # Тут крч аналогично request_keywords_lemmas
        # Аналогично отбираем оригинальные ключевые слова
        group_matches = [
            kw for kw, lemmas in topic_keywords_lemmas.items() 
            if _check_keyword_in_text(lemmas, text_lemmas)
        ]
        if group_matches:
            matched_groups.append(group)
            matched_topic_keywords.extend(group_matches)
            
    request_match = bool(request_matches)
    topic_match = bool(matched_groups)
    excluded = bool(exclusion_matches)
    
    relevant = request_match and topic_match and not excluded
    
    if relevant:
        reason = (
            f"✅ РЕЛЕВАНТНО. "
            f"Признаки запроса: [{', '.join(request_matches)}]. "
            f"Тематические ключи: [{', '.join(matched_topic_keywords)}] (группы: {', '.join(matched_groups)})"
        )
    elif excluded:
        reason = (
            f"❌ ОТФИЛЬТРОВАНО (ИСКЛЮЧЕНИЕ). "
            f"Сработали слова-исключения: [{', '.join(exclusion_matches)}]. "
            f"При этом найдено признаков запроса: [{', '.join(request_matches) if request_matches else 'нет'}], "
            f"тематических ключей: [{', '.join(matched_topic_keywords) if matched_topic_keywords else 'нет'}]"
        )
    else:
        reasons_list = []
        if not request_match:
            reasons_list.append("❌ Не найден признак журналистского запроса")
        if not topic_match:
            reasons_list.append("❌ Не найдено тематическое совпадение")
            
        reason = ". ".join(reasons_list) + ". "
        if request_matches:
            reason += f"(Найденные признаки запроса: [{', '.join(request_matches)}]). "
        if matched_topic_keywords:
            reason += f"(Найденные тематические ключи: [{', '.join(matched_topic_keywords)}]). "
        if exclusion_matches:
            reason += f"(Найденные исключения: [{', '.join(exclusion_matches)}])."

    return FilterResult(
        is_relevant=relevant,
        request_match=request_match,
        topic_match=topic_match,
        excluded=excluded,
        request_keywords=request_matches,
        topic_groups=matched_groups, # Оставил так, чтоб была совместимость с models.py и потому что мне лень
        exclusion_keywords=exclusion_matches,
        reason=reason.strip(),
    )