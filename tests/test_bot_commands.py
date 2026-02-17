import os
import unittest
from unittest.mock import AsyncMock

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("DADATA_API_KEY", "test-dadata-api-key")

from aiogram.types import BotCommand, BotCommandScopeDefault

import bot


class SetupCommandsTests(unittest.IsolatedAsyncioTestCase):
    async def test_setup_commands_registers_expected_ru_menu(self):
        mock_bot = AsyncMock()

        await bot.setup_commands(mock_bot)

        mock_bot.set_my_commands.assert_awaited_once()
        _, kwargs = mock_bot.set_my_commands.await_args

        self.assertEqual(
            kwargs["commands"],
            [
                BotCommand(command="start", description="Запуск"),
                BotCommand(command="help", description="Помощь/меню"),
                BotCommand(command="find", description="Найти компанию по ИНН (10/12 цифр)"),
            ],
        )
        self.assertEqual(kwargs["scope"], BotCommandScopeDefault())
        self.assertEqual(kwargs["language_code"], "ru")


if __name__ == "__main__":
    unittest.main()
