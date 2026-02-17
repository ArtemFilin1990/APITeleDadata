import unittest

from keyboards import (
    CB_ACT_CRM,
    CB_ACT_EXPORT,
    CB_NAV_BACK,
    CB_NAV_HOME,
    CB_PAGE_DETAILS,
    CB_PAGE_DOCUMENTS,
    CB_PAGE_FOUNDERS,
    CB_PAGE_MANAGEMENT,
    CB_PAGE_RELATIONS,
    CB_PAGE_SCORING,
    CB_PAGE_TAXES,
    BTN_CHECK_INN,
    inline_actions_kb,
    reply_main_menu_kb,
)


class ReplyKeyboardTests(unittest.TestCase):
    def test_reply_menu_layout(self):
        kb = reply_main_menu_kb()
        self.assertEqual(len(kb.keyboard), 1)
        self.assertEqual(kb.keyboard[0][0].text, BTN_CHECK_INN)


class InlineKeyboardTests(unittest.TestCase):
    def test_first_row_has_main_actions(self):
        kb = inline_actions_kb()
        first_row = kb.inline_keyboard[0]
        self.assertEqual(first_row[0].text, "📄 Подробнее")
        self.assertEqual(first_row[0].callback_data, CB_PAGE_DETAILS)
        self.assertEqual(first_row[1].text, "📤 Экспорт")
        self.assertEqual(first_row[1].callback_data, CB_ACT_EXPORT)
        self.assertEqual(first_row[2].text, "🧩 В CRM")
        self.assertEqual(first_row[2].callback_data, CB_ACT_CRM)

    def test_last_row_is_fixed_nav(self):
        kb = inline_actions_kb()
        last_row = kb.inline_keyboard[-1]
        self.assertEqual(last_row[0].text, "назад")
        self.assertEqual(last_row[0].callback_data, CB_NAV_BACK)
        self.assertEqual(last_row[1].text, "домой")
        self.assertEqual(last_row[1].callback_data, CB_NAV_HOME)

    def test_premium_rows_present(self):
        kb = inline_actions_kb()
        founders_row = kb.inline_keyboard[1]
        self.assertEqual(founders_row[0].callback_data, CB_PAGE_FOUNDERS)
        self.assertEqual(founders_row[1].callback_data, CB_PAGE_MANAGEMENT)

        taxes_row = kb.inline_keyboard[2]
        self.assertEqual(taxes_row[0].callback_data, CB_PAGE_TAXES)
        self.assertEqual(taxes_row[1].callback_data, CB_PAGE_DOCUMENTS)

        relation_row = kb.inline_keyboard[3]
        self.assertEqual(relation_row[0].callback_data, CB_PAGE_RELATIONS)
        self.assertEqual(relation_row[1].callback_data, CB_PAGE_SCORING)


if __name__ == "__main__":
    unittest.main()
