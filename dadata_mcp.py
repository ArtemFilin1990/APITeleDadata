"""Запрос к DaData через MCP-сервер с использованием OpenAI Responses API."""

import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

DADATA_API_KEY = "c893404a31a0a724da24a812677c7e6675542788"
DADATA_SECRET_KEY = "7abf14baf640935153f23b5e372b2ac5eab973b8"


async def fetch_company_via_mcp(inn: str) -> str:
    """Проверка компании через DaData MCP + OpenAI AI.
    
    Args:
        inn: ИНН компании для проверки
        
    Returns:
        Текстовый ответ от AI или сообщение об ошибке
    """
    try:
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url="https://api.openai.com/v1"
        )
        
        response = client.responses.create(
            model="gpt-4.1-mini",
            tools=[{
                "type": "mcp",
                "server_label": "dadata",
                "server_url": "https://mcp.dadata.ru/mcp",
                "headers": {
                    "authorization": f"Bearer {DADATA_API_KEY}:{DADATA_SECRET_KEY}"
                },
                "require_approval": "never"
            }],
            input=f"Проверь контрагента по ИНН {inn}. Надёжный ли он? Дай подробный анализ: реквизиты, статус, адрес, руководство, финансы."
        )
        
        # Извлекаем текстовый ответ
        result_text = ""
        for item in response.output:
            if hasattr(item, 'content'):
                for content_block in item.content:
                    if hasattr(content_block, 'text'):
                        result_text += content_block.text
        
        if not result_text:
            result_text = str(response.output)
        
        return result_text
        
    except Exception as e:
        logger.error(f"MCP error for INN {inn}: {e}")
        return f"❌ Ошибка MCP-запроса: {e}"
