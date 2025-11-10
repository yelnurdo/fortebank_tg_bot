"""Application factory wiring together all components."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from google import genai

from app.api.chat_routes import create_chat_router
from app.api.dependencies import DependencyProvider
from app.api.routes import create_router
from app.config import AppConfig
from app.core.scheduler import Scheduler
from app.data_sources.fx import FXRatesSource
from app.data_sources.investments import InvestmentsSource
from app.orchestrator import DigestOrchestrator
from app.repositories.chat_history import ChatHistoryRepository
from app.repositories.digests import DigestRepository
from app.services.chat_manager import ChatManager
from app.services.llm import LlmDigestService
from app.telegram.notifier import TelegramNotifier

logger = logging.getLogger(__name__)


def create_app(config: AppConfig) -> FastAPI:
    """Construct and configure the FastAPI application."""

    fx_source = FXRatesSource()
    investments_source = InvestmentsSource()
    generator_cls = LlmDigestService

    if generator_cls.__name__.lower().startswith("gemini"):
        if not config.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is missing. "
                "Please create a .env file with GEMINI_API_KEY=your_key"
            )

        generator = generator_cls(
            api_key=config.gemini_api_key,
            model=config.gemini_model,
        )
    else:
        generator = generator_cls(
            api_key=config.openai_api_key,
            model=config.gpt_model,
        )

    repository = DigestRepository(config.postgres_dsn)
    notifier = TelegramNotifier(config.telegram_bot_token)
    orchestrator = DigestOrchestrator(
        data_sources=(fx_source, investments_source),
        generator=generator,
        repository=repository,
        notifier=notifier,
    )
    scheduler = Scheduler(orchestrator, config.digest_dispatch_time)

    dependency_provider = DependencyProvider(orchestrator, repository)

    # Инициализация репозитория для истории чата (PostgreSQL)
    chat_history_repository = None
    if config.postgres_dsn:
        try:
            chat_history_repository = ChatHistoryRepository(config.postgres_dsn)
            logger.info("Chat history repository initialized with PostgreSQL")
        except Exception as e:
            logger.warning(f"Failed to initialize chat history repository: {e}. Will use file-based storage.")
    else:
        logger.warning("POSTGRES_DSN not provided, chat history will be stored in files")

    # Инициализация ChatManager для обработки запросов от Telegram бота
    # Поддержка нескольких моделей с fallback: Cohere -> GPT -> Gemini
    gemini_client = None
    if config.gemini_api_key:
        gemini_client = genai.Client(api_key=config.gemini_api_key)
    else:
        logger.warning("GEMINI_API_KEY not provided, Gemini will not be available")

    chat_manager = ChatManager(
        gemini_client=gemini_client,
        gemini_model=config.gemini_model,
        openai_api_key=config.openai_api_key if config.openai_api_key else None,
        gpt_model=config.gpt_model,
        cohere_api_key=config.cohere_api_key if config.cohere_api_key else None,
        cohere_model=config.cohere_model,
        default_role="user",
        history_repository=chat_history_repository,
    )

    fastapi_app = FastAPI(title="ForteBank FX & Investments Bot")
    fastapi_app.include_router(create_router(dependency_provider))
    fastapi_app.include_router(create_chat_router(chat_manager))

    @fastapi_app.on_event("startup")
    async def _start_scheduler() -> None:
        logger.info("Starting daily digest scheduler")
        await scheduler.start()
        # Инициализируем репозиторий истории чата при старте
        if chat_history_repository:
            await chat_history_repository.initialize()
            logger.info("Chat history repository initialized")

    @fastapi_app.on_event("shutdown")
    async def _shutdown() -> None:
        """Закрываем соединения с БД при остановке."""
        if chat_history_repository:
            await chat_history_repository.close()
            logger.info("Chat history repository closed")

    fastapi_app.state.config = config
    fastapi_app.state.scheduler = scheduler

    return fastapi_app
