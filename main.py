"""ASGI entry point for the ForteBank FX & investments bot MVP."""

from __future__ import annotations

import asyncio
import logging
from dotenv import load_dotenv

from app.application import create_app
from app.config import load_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загружаем переменные из .env файла
load_dotenv()

config = load_config()

# Проверяем наличие обязательных переменных перед созданием приложения
if not config.gemini_api_key:
    logger.error(
        "❌ GEMINI_API_KEY не найден!\n"
        "Создайте файл .env в корне проекта и добавьте:\n"
        "GEMINI_API_KEY=ваш_ключ\n\n"
        "Получить ключ можно здесь: https://aistudio.google.com/apikey\n"
        "Пример файла: .env.example"
    )
    raise ValueError("GEMINI_API_KEY is required")

app = create_app(config)


async def main() -> None:
    """Run the FastAPI app with Uvicorn when executed directly."""

    logger.info("Starting development server")
    import uvicorn  # Imported lazily to keep dependency optional for tests

    server_config = uvicorn.Config(app=app, host="0.0.0.0", port=8000, reload=True)
    server = uvicorn.Server(config=server_config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
