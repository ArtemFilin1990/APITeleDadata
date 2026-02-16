import unittest

from party_state import format_company_state


class PartyStateTests(unittest.TestCase):
    def test_returns_placeholder_without_state(self):
        self.assertEqual(format_company_state(None, "LEGAL"), "—")

    def test_returns_base_status_without_code(self):
        self.assertEqual(
            format_company_state({"status": "ACTIVE"}, "LEGAL"),
            "✅ Действующая",
        )

    def test_resolves_reason_code_from_party_state_csv(self):
        result = format_company_state(
            {"status": "LIQUIDATING", "code": "101"},
            "LEGAL",
        )
        self.assertIn("⚠️ Ликвидируется", result)
        self.assertIn("код 101", result)
        self.assertIn("Находится в стадии ликвидации", result)

    def test_uses_individual_mapping_for_same_code(self):
        result = format_company_state(
            {"status": "LIQUIDATED", "code": "101"},
            "INDIVIDUAL",
        )
        self.assertIn("❌ Ликвидирована", result)
        self.assertIn("код 101", result)
        self.assertIn("Отсутствует в связи со смертью", result)

    def test_unknown_code_falls_back_to_base_status(self):
        self.assertEqual(
            format_company_state({"status": "ACTIVE", "code": "999999"}, "LEGAL"),
            "✅ Действующая",
        )


if __name__ == "__main__":
    unittest.main()
