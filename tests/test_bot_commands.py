import os
import unittest
from unittest.mock import AsyncMock

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("DADATA_API_KEY", "test-dadata-api-key")

import bot


class BotCommandsTests(unittest.IsolatedAsyncioTestCase):
    async def test_setup_commands_registers_required_menu_items(self):
        fake_bot = AsyncMock()

        await bot.setup_commands(fake_bot)

        fake_bot.set_my_commands.assert_awaited_once()
        call_kwargs = fake_bot.set_my_commands.await_args.kwargs
        commands = call_kwargs["commands"]
        self.assertEqual(len(commands), 3)

        self.assertEqual(commands[0].command, "start")
        self.assertEqual(commands[0].description, "Запуск")

        self.assertEqual(commands[1].command, "help")
        self.assertEqual(commands[1].description, "Помощь/меню")

        self.assertEqual(commands[2].command, "find")
        self.assertEqual(commands[2].description, "Найти компанию по ИНН (10/12 цифр)")


if __name__ == "__main__":
    unittest.main()
