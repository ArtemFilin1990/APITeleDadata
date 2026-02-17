import os
import unittest

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("DADATA_API_KEY", "test-dadata-api-key")

from handlers import (
    ENTITY_TYPE_INDIVIDUAL,
    ENTITY_TYPE_LEGAL,
    _build_result_totals,
    _search_filters_from_choice,
)
from keyboards import CB_ACT_FIND_FL, CB_ACT_FIND_IP, CB_ACT_FIND_UL


class HandlerSummaryTests(unittest.TestCase):
    def test_build_result_totals_with_mixed_invalid_values(self):
        text = _build_result_totals(found=1, not_found=0, invalid=["12AB", "123"])
        self.assertIn("Итог: найдено 1, не найдено 0.", text)
        self.assertIn("не только цифры: 12AB", text)
        self.assertIn("неверная длина: 123", text)


class HandlerSearchFilterTests(unittest.TestCase):
    def test_legal_choice_maps_to_main_legal(self):
        self.assertEqual(
            _search_filters_from_choice(CB_ACT_FIND_UL),
            {"branch_type": "MAIN", "entity_type": ENTITY_TYPE_LEGAL},
        )

    def test_individual_choices_map_to_main_individual(self):
        expected = {"branch_type": "MAIN", "entity_type": ENTITY_TYPE_INDIVIDUAL}
        self.assertEqual(_search_filters_from_choice(CB_ACT_FIND_FL), expected)
        self.assertEqual(_search_filters_from_choice(CB_ACT_FIND_IP), expected)

    def test_default_choice_maps_to_main_only(self):
        self.assertEqual(_search_filters_from_choice(None), {"branch_type": "MAIN"})


if __name__ == "__main__":
    unittest.main()
