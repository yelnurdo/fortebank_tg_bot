"""Менеджер для управления чатами с Gemini."""

from __future__ import annotations

import logging
from typing import Dict

from google import genai

from app.services.gemini_chat import GeminiChat
from app.services.roles import get_role_prompt, is_valid_role

logger = logging.getLogger(__name__)


class ChatManager:
    """Менеджер для управления множественными чатами с Gemini."""

    def __init__(
        self,
        gemini_client: genai.Client,
        model: str = "models/gemini-2.5-flash",
        default_role: str = "user",
    ):
        self.gemini_client = gemini_client
        self.model = model
        self.default_role = default_role

        # Хранилище чатов для каждого пользователя и роли
        # Структура: {user_id: {role: GeminiChat}}
        self.user_chats: Dict[int, Dict[str, GeminiChat]] = {}

        # Текущая выбранная роль для каждого пользователя
        # Структура: {user_id: role}
        self.user_roles: Dict[int, str] = {}

    def get_chat(self, user_id: int, role: str = None) -> GeminiChat:
        """Получить или создать чат для пользователя с указанной ролью."""
        if role is None:
            # Используем сохраненную роль пользователя или дефолтную
            role = self.user_roles.get(user_id, self.default_role)

        if not is_valid_role(role):
            role = self.default_role

        if user_id not in self.user_chats:
            self.user_chats[user_id] = {}

        if role not in self.user_chats[user_id]:
            # Создаем новый чат для пользователя с указанной ролью
            history_file = f"chat_history_{user_id}_{role}.json"
            chat = GeminiChat(
                client=self.gemini_client,
                model=self.model,
                system_prompt=get_role_prompt(role),
                max_context_tokens=30000,
                temperature=0.2,
                max_output_tokens=2000,
                history_file=history_file,
            )
            chat.load_history()
            self.user_chats[user_id][role] = chat

        return self.user_chats[user_id][role]

    def process_message(
        self, user_id: int, message: str, role: str = None
    ) -> tuple[str, str, dict]:
        """
        Обработать сообщение и вернуть ответ.

        Returns:
            tuple: (response_text, used_role, stats_dict)
        """
        # Если роль указана, сохраняем её для пользователя
        if role and is_valid_role(role):
            self.user_roles[user_id] = role

        # Получаем чат для пользователя
        chat = self.get_chat(user_id, role)

        # Отправляем сообщение
        response = chat.send_message(message)

        # Получаем статистику
        stats = chat.get_history_summary()

        # Получаем использованную роль
        used_role = self.user_roles.get(user_id, self.default_role)

        return response, used_role, stats

    def clear_history(self, user_id: int, role: str = None) -> bool:
        """
        Очистить историю для пользователя.

        Args:
            user_id: ID пользователя
            role: Роль для очистки (если None, очищается вся история)

        Returns:
            bool: Успешность операции
        """
        if user_id not in self.user_chats:
            return False

        if role:
            # Очищаем конкретную роль
            if role in self.user_chats[user_id]:
                self.user_chats[user_id][role].clear_history()
                return True
            return False
        else:
            # Очищаем всю историю пользователя
            for chat in self.user_chats[user_id].values():
                chat.clear_history()
            return True

    def get_stats(self, user_id: int, role: str = None) -> dict:
        """Получить статистику для пользователя."""
        chat = self.get_chat(user_id, role)
        return chat.get_history_summary()

