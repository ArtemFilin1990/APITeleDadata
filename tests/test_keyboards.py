import unittest

from keyboards import (
    CB_NAV_BACK,
    CB_NAV_HOME,
    BTN_CHECK_INN,
    BTN_HELLO,
    BTN_START,
    inline_actions_kb,
    reply_main_menu_kb,
)


class ReplyKeyboardTests(unittest.TestCase):
    def test_reply_menu_layout(self):
        kb = reply_main_menu_kb()
        self.assertEqual(kb.keyboard[0][0].text, BTN_START)
        self.assertEqual(kb.keyboard[0][1].text, BTN_HELLO)
        self.assertEqual(kb.keyboard[1][0].text, BTN_CHECK_INN)


class InlineKeyboardTests(unittest.TestCase):
    def test_last_row_is_fixed_nav(self):
        kb = inline_actions_kb()
        last_row = kb.inline_keyboard[-1]
        self.assertEqual(last_row[0].text, "назад")
        self.assertEqual(last_row[0].callback_data, CB_NAV_BACK)
        self.assertEqual(last_row[1].text, "домой")
        self.assertEqual(last_row[1].callback_data, CB_NAV_HOME)


if __name__ == "__main__":
    unittest.main()
