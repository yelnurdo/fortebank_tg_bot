"""Менеджер для управления чатами с поддержкой нескольких моделей и fallback стратегией."""

from __future__ import annotations

import logging
from typing import Dict, Optional

from google import genai

from app.repositories.chat_history import ChatHistoryRepository
from app.services.cohere_chat import CohereChat
from app.services.gemini_chat import GeminiChat
from app.services.gpt_chat import GPTChat
from app.services.roles import get_role_prompt, is_valid_role

logger = logging.getLogger(__name__)


class ChatManager:
    """Менеджер для управления множественными чатами с поддержкой нескольких моделей."""

    def __init__(
        self,
        gemini_client: Optional[genai.Client] = None,
        gemini_model: str = "models/gemini-2.5-flash",
        openai_api_key: Optional[str] = None,
        gpt_model: str = "gpt-4.1-mini",
        cohere_api_key: Optional[str] = None,
        cohere_model: str = "command-r-08-2024",
        default_role: str = "user",
        history_repository: Optional[ChatHistoryRepository] = None,
    ):
        self.gemini_client = gemini_client
        self.gemini_model = gemini_model
        self.openai_api_key = openai_api_key
        self.gpt_model = gpt_model
        self.cohere_api_key = cohere_api_key
        self.cohere_model = cohere_model
        self.default_role = default_role
        self.history_repository = history_repository

        # Хранилище чатов для каждого пользователя и роли
        # Структура: {user_id: {role: BaseChat}}
        self.user_chats: Dict[int, Dict[str, any]] = {}

        # Текущая выбранная роль для каждого пользователя
        # Структура: {user_id: role}
        self.user_roles: Dict[int, str] = {}

        # Порядок fallback: Cohere -> GPT -> Gemini
        self.fallback_order = ["cohere", "gpt", "gemini"]

    def _create_chat_instance(
        self, model_type: str, user_id: int, role: str, history_file: Optional[str] = None
    ) -> any:
        """Создать экземпляр чата для указанной модели."""
        system_prompt = get_role_prompt(role)
        common_params = {
            "system_prompt": system_prompt,
            "max_context_tokens": 30000,
            "temperature": 0.2,
            "max_output_tokens": 2000,
            "user_id": user_id,
            "role": role,
        }
        
        # Используем БД если репозиторий доступен, иначе файлы
        if self.history_repository:
            common_params["history_repository"] = self.history_repository
        else:
            common_params["history_file"] = history_file or f"chat_history_{user_id}_{role}.json"

        if model_type == "gemini":
            if not self.gemini_client:
                raise ValueError("Gemini client not initialized")
            return GeminiChat(
                client=self.gemini_client,
                model=self.gemini_model,
                **common_params,
            )
        elif model_type == "gpt":
            if not self.openai_api_key:
                raise ValueError("OpenAI API key not provided")
            return GPTChat(
                api_key=self.openai_api_key,
                model=self.gpt_model,
                **common_params,
            )
        elif model_type == "cohere":
            if not self.cohere_api_key:
                raise ValueError("Cohere API key not provided")
            return CohereChat(
                api_key=self.cohere_api_key,
                model=self.cohere_model,
                **common_params,
            )
        else:
            raise ValueError(f"Unknown model type: {model_type}")

    def get_chat(self, user_id: int, role: str = None) -> any:
        """Получить или создать чат для пользователя с указанной ролью."""
        if role is None:
            role = self.user_roles.get(user_id, self.default_role)

        if not is_valid_role(role):
            role = self.default_role

        if user_id not in self.user_chats:
            self.user_chats[user_id] = {}

        if role not in self.user_chats[user_id]:
            # Создаем новый чат для пользователя с указанной ролью
            # Используем БД если репозиторий доступен, иначе файлы
            history_file = None if self.history_repository else f"chat_history_{user_id}_{role}.json"
            
            # Пытаемся создать чат с первой доступной моделью
            chat = None
            for model_type in self.fallback_order:
                try:
                    chat = self._create_chat_instance(model_type, user_id, role, history_file)
                    logger.info(f"Created {model_type} chat for user {user_id}, role {role}")
                    # Загружаем историю после создания
                    chat.load_history()
                    break
                except (ValueError, Exception) as e:
                    logger.warning(f"Failed to create {model_type} chat: {e}")
                    continue

            if chat is None:
                raise RuntimeError("Failed to create chat with any available model")

            self.user_chats[user_id][role] = chat

        return self.user_chats[user_id][role]

    def _try_with_fallback(self, user_id: int, role: str, message: str) -> tuple[str, str]:
        """
        Попытаться отправить сообщение с fallback стратегией.
        
        Returns:
            tuple: (response_text, used_model)
        """
        history_file = None if self.history_repository else f"chat_history_{user_id}_{role}.json"
        system_prompt = get_role_prompt(role)

        last_error = None
        for model_type in self.fallback_order:
            try:
                # Создаем временный экземпляр чата для этой модели
                chat = self._create_chat_instance(model_type, user_id, role, history_file)
                
                # Загружаем общую историю
                chat.load_history()
                
                # Отправляем сообщение
                logger.info(f"Attempting to send message with {model_type} for user {user_id}, role {role}")
                response = chat.send_message(message)
                
                logger.info(f"Successfully used {model_type} for user {user_id}, role {role}")
                
                # Обновляем основной чат пользователя на успешную модель
                if user_id not in self.user_chats:
                    self.user_chats[user_id] = {}
                self.user_chats[user_id][role] = chat
                
                return response, model_type

            except Exception as e:
                logger.warning(f"Failed to use {model_type} for user {user_id}, role {role}: {e}")
                last_error = e
                continue

        # Если все модели не сработали
        error_msg = f"Все модели недоступны. Последняя ошибка: {str(last_error)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    def process_message(
        self, user_id: int, message: str, role: str = None, provider: Optional[str] = None
    ) -> tuple[str, str, dict]:
        """
        Обработать сообщение и вернуть ответ.

        Args:
            user_id: ID пользователя
            message: Текст сообщения
            role: Роль пользователя
            provider: Провайдер модели ("gemini", "gpt", "cohere" или None для fallback)

        Returns:
            tuple: (response_text, used_role, stats_dict)
        """
        # Если роль указана, сохраняем её для пользователя
        if role and is_valid_role(role):
            self.user_roles[user_id] = role

        # Получаем текущую роль
        used_role = self.user_roles.get(user_id, self.default_role)
        if not is_valid_role(used_role):
            used_role = self.default_role

        # Если указан провайдер, используем его, иначе используем fallback
        if provider:
            provider = provider.lower()
            if provider not in ["gemini", "gpt", "cohere", "openai"]:
                logger.warning(f"Unknown provider {provider}, using fallback")
                provider = None
            elif provider == "openai":
                provider = "gpt"  # Normalize openai to gpt

        if provider:
            # Используем указанный провайдер
            logger.info(f"Using provider {provider} for user {user_id}, role {used_role}")
            history_file = None if self.history_repository else f"chat_history_{user_id}_{used_role}.json"
            try:
                chat = self._create_chat_instance(provider, user_id, used_role, history_file)
                chat.load_history()
                response = chat.send_message(message)
                stats = chat.get_history_summary()
                
                # Сохраняем чат для будущего использования
                if user_id not in self.user_chats:
                    self.user_chats[user_id] = {}
                self.user_chats[user_id][used_role] = chat
                
                logger.info(f"Successfully processed message with {provider} for user {user_id}")
                return response, used_role, stats
            except Exception as e:
                logger.error(f"Failed to use provider {provider} for user {user_id}: {e}")
                # Fallback to automatic selection
                logger.info(f"Falling back to automatic provider selection for user {user_id}")
                provider = None

        # Автоматический выбор провайдера (fallback стратегия)
        # Пытаемся использовать существующий чат, если он есть
        try:
            chat = self.get_chat(user_id, used_role)
            model_name = chat.get_model_name()
            logger.info(f"Using existing {model_name} chat for user {user_id}, role {used_role}")
            response = chat.send_message(message)
            stats = chat.get_history_summary()
            logger.info(f"Successfully processed message with {model_name} for user {user_id}")
            return response, used_role, stats
        except Exception as e:
            logger.warning(f"Error with existing chat, trying fallback: {e}")
            # Если текущий чат не работает, пробуем fallback
            try:
                response, used_model = self._try_with_fallback(user_id, used_role, message)
                chat = self.get_chat(user_id, used_role)
                stats = chat.get_history_summary()
                logger.info(f"Successfully processed message with {used_model} (fallback) for user {user_id}")
                return response, used_role, stats
            except Exception as e2:
                logger.exception(f"All models failed for user {user_id}: {e2}")
                raise

    def clear_history(self, user_id: int, role: str = None) -> bool:
        """
        Очистить историю для пользователя.

        Args:
            user_id: ID пользователя
            role: Роль для очистки (если None, очищается вся история)

        Returns:
            bool: Успешность операции
        """
        # Очищаем из БД если репозиторий доступен
        if self.history_repository:
            import asyncio
            import nest_asyncio
            nest_asyncio.apply()
            try:
                asyncio.run(self.history_repository.clear_history(user_id, role))
            except Exception as e:
                logger.error(f"Error clearing history from DB: {e}")
                return False

        # Очищаем из памяти
        if user_id not in self.user_chats:
            return True

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
