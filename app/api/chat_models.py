"""Pydantic models for chat API requests and responses."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Запрос на обработку сообщения от Telegram бота."""

    user_id: int = Field(..., description="ID пользователя Telegram")
    message: str = Field(..., description="Текст сообщения от пользователя")
    role: str = Field(
        default="user",
        description="Роль пользователя: user, employee, investor",
    )
    provider: Optional[str] = Field(
        default=None,
        description="Провайдер модели: gemini, gpt (или openai), cohere. Если не указан, используется автоматический fallback",
    )


class ChatResponse(BaseModel):
    """Ответ на запрос обработки сообщения."""

    response: str = Field(..., description="Ответ от Gemini модели")
    role: str = Field(..., description="Использованная роль")
    stats: dict = Field(
        default_factory=dict,
        description="Статистика использования токенов",
    )


class ClearHistoryRequest(BaseModel):
    """Запрос на очистку истории."""

    user_id: int = Field(..., description="ID пользователя Telegram")
    role: str = Field(
        default=None,
        description="Роль для очистки (если не указана, очищается вся история)",
    )


class ClearHistoryResponse(BaseModel):
    """Ответ на запрос очистки истории."""

    success: bool = Field(..., description="Успешность операции")
    message: str = Field(..., description="Сообщение о результате")

