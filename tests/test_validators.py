import unittest

from validators import parse_inns, validate_inn


class ValidateInnTests(unittest.TestCase):
    def test_accepts_legal_entity_inn(self):
        self.assertEqual(validate_inn("7707083893"), (True, "юр. лицо"))

    def test_accepts_individual_inn(self):
        self.assertEqual(validate_inn("500100732259"), (True, "ИП"))

    def test_rejects_non_digit_values(self):
        valid, message = validate_inn("77070A3893")
        self.assertFalse(valid)
        self.assertIn("только цифры", message)

    def test_rejects_invalid_length(self):
        valid, message = validate_inn("123")
        self.assertFalse(valid)
        self.assertIn("10 (юр. лицо) или 12", message)


class ParseInnsTests(unittest.TestCase):
    def test_splits_by_whitespace_commas_and_semicolons(self):
        text = "7721581040, 4025456794\n500100732259; 7707083893"
        self.assertEqual(
            parse_inns(text),
            ["7721581040", "4025456794", "500100732259", "7707083893"],
        )


if __name__ == "__main__":
    unittest.main()
