import unittest

from keyboards import (
    CB_ACT_CRM,
    CB_ACT_EXPORT,
    CB_ACT_FIND_FL,
    CB_ACT_FIND_IP,
    CB_ACT_FIND_UL,
    CB_NAV_BACK,
    CB_NAV_HOME,
    CB_PAGE_DETAILS,
    BTN_CHECK_INN,
    BTN_HELLO,
    BTN_START,
    inline_actions_kb,
    inline_find_type_kb,
    reply_main_menu_kb,
)


class ReplyKeyboardTests(unittest.TestCase):
    def test_reply_menu_layout(self):
        kb = reply_main_menu_kb()
        self.assertEqual(kb.keyboard[0][0].text, BTN_START)
        self.assertEqual(kb.keyboard[0][1].text, BTN_HELLO)
        self.assertEqual(kb.keyboard[1][0].text, BTN_CHECK_INN)


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


class InlineFindTypeKeyboardTests(unittest.TestCase):
    def test_contains_ul_fl_ip_buttons(self):
        kb = inline_find_type_kb()
        row = kb.inline_keyboard[0]
        self.assertEqual(row[0].text, "ИНН юр. лица")
        self.assertEqual(row[0].callback_data, CB_ACT_FIND_UL)
        self.assertEqual(row[1].text, "ИНН физ. лица")
        self.assertEqual(row[1].callback_data, CB_ACT_FIND_FL)
        self.assertEqual(row[2].text, "ИНН ИП")
        self.assertEqual(row[2].callback_data, CB_ACT_FIND_IP)


if __name__ == "__main__":
    unittest.main()
