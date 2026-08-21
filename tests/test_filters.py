import json
import unittest
from pathlib import Path

from app.filters import evaluate


CONFIG = json.loads((Path(__file__).parents[1] / "config" / "filters.json").read_text(encoding="utf-8"))


class FilterTests(unittest.TestCase):
    def test_relevant_ijs(self):
        result = evaluate("Ищу эксперта по перспективам развития ИЖС в РФ", CONFIG)
        self.assertTrue(result.is_relevant)

    def test_relevant_rieltor_accreditive(self):
        result = evaluate("Ищу риелтора, который работает с аккредитивами. Крупное деловое СМИ", CONFIG)
        self.assertTrue(result.is_relevant)

    def test_relevant_construction(self):
        result = evaluate("Для статьи нужны эксперты по современным строительным технологиям", CONFIG)
        self.assertTrue(result.is_relevant)

    def test_external_politics_rejected(self):
        result = evaluate("Ищу эксперта в области внешней политики", CONFIG)
        self.assertFalse(result.is_relevant)
        self.assertTrue(result.request_match)
        self.assertFalse(result.topic_match)

    def test_internal_communication_rejected(self):
        result = evaluate("Коллеги, кто у нас отвечает за запросы в АРСС?", CONFIG)
        self.assertFalse(result.is_relevant)

    def test_non_media_question_rejected(self):
        result = evaluate("Какие растения лучше посадить возле дома?", CONFIG)
        self.assertFalse(result.is_relevant)


if __name__ == "__main__":
    unittest.main()
