"""API routes for chat processing from Telegram bot."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.api.chat_models import (
    ChatRequest,
    ChatResponse,
    ClearHistoryRequest,
    ClearHistoryResponse,
)
from app.services.chat_manager import ChatManager

logger = logging.getLogger(__name__)


def create_chat_router(chat_manager: ChatManager) -> APIRouter:
    """Создать роутер для обработки чат-запросов от Telegram бота."""

    router = APIRouter(prefix="/chat", tags=["chat"])

    @router.post("/message", response_model=ChatResponse)
    async def process_message(request: ChatRequest) -> ChatResponse:
        """
        Обработать сообщение от пользователя Telegram бота.

        Telegram бот отправляет сюда запрос с сообщением пользователя,
        получает ответ от Gemini модели и отправляет его обратно пользователю.
        """
        try:
            logger.info(
                f"Processing message for user {request.user_id}, "
                f"role={request.role}, provider={request.provider or 'auto'}"
            )
            response_text, used_role, stats = chat_manager.process_message(
                user_id=request.user_id,
                message=request.message,
                role=request.role,
                provider=request.provider,
            )

            logger.info(
                f"Message processed successfully for user {request.user_id}, "
                f"model={stats.get('model', 'unknown')}"
            )

            return ChatResponse(
                response=response_text,
                role=used_role,
                stats=stats,
            )
        except Exception as e:
            logger.exception(f"Ошибка при обработке сообщения для user {request.user_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при обработке сообщения: {str(e)}",
            )

    @router.post("/clear", response_model=ClearHistoryResponse)
    async def clear_history(request: ClearHistoryRequest) -> ClearHistoryResponse:
        """
        Очистить историю чата для пользователя.

        Если роль не указана, очищается вся история пользователя.
        """
        try:
            success = chat_manager.clear_history(
                user_id=request.user_id,
                role=request.role,
            )

            if success:
                message = (
                    f"История для пользователя {request.user_id} "
                    f"{f'и роли {request.role}' if request.role else ''} очищена"
                )
            else:
                message = f"История для пользователя {request.user_id} не найдена"

            return ClearHistoryResponse(success=success, message=message)
        except Exception as e:
            logger.exception(f"Ошибка при очистке истории: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при очистке истории: {str(e)}",
            )

    @router.get("/stats/{user_id}")
    async def get_stats(user_id: int, role: str = None) -> dict:
        """
        Получить статистику использования для пользователя.

        Args:
            user_id: ID пользователя Telegram
            role: Роль для получения статистики (опционально)
        """
        try:
            stats = chat_manager.get_stats(user_id=user_id, role=role)
            return stats
        except Exception as e:
            logger.exception(f"Ошибка при получении статистики: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при получении статистики: {str(e)}",
            )

    return router

