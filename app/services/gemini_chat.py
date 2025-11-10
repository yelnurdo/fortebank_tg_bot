"""Google Gemini chat implementation with history management."""

from __future__ import annotations

import logging
from typing import Dict, List

from google import genai

from app.services.base_chat import BaseChat

logger = logging.getLogger(__name__)


class GeminiChat(BaseChat):
    """Класс для управления чатом с Gemini API с сохранением истории."""

    def __init__(
        self,
        client: genai.Client,
        model: str = "models/gemini-2.5-flash",
        system_prompt: str = "",
        max_context_tokens: int = 30000,
        temperature: float = 0.2,
        max_output_tokens: int = 2000,
        history_file: str | None = None,
    ):
        super().__init__(
            system_prompt=system_prompt,
            max_context_tokens=max_context_tokens,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            history_file=history_file,
        )
        self.client = client
        self.model = model
        # Load history after initialization
        self.load_history()

    def _convert_to_model_format(self, history: List[Dict[str, str]]) -> List[Dict]:
        """Convert unified history format to Gemini format."""
        # Gemini format: [{"role": "user", "parts": [{"text": "..."}]}, ...]
        contents = []
        for msg in history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            # Map "model" to "model" for Gemini
            if role not in ["user", "model"]:
                role = "user"
            contents.append({"role": role, "parts": [{"text": content}]})
        return contents

    def _convert_from_model_format(self, model_history: any) -> List[Dict[str, str]]:
        """Convert Gemini format to unified history format."""
        # Convert from old Gemini format if needed
        unified = []
        for msg in model_history:
            if isinstance(msg, dict):
                if "parts" in msg:
                    # Old Gemini format
                    content = msg.get("parts", [{}])[0].get("text", "")
                else:
                    # Already unified format
                    content = msg.get("content", "")
                role = msg.get("role", "user")
                if role == "model":
                    role = "model"
                unified.append({"role": role, "content": content})
        return unified


    def send_message(self, user_message: str) -> str:
        """Отправить сообщение и получить ответ."""
        # Add user message to history
        self.add_message("user", user_message)

        # Trim history if needed
        self._trim_history()

        # Convert to Gemini format
        contents = self._convert_to_model_format(self.history)

        # Form configuration
        config = {
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
        }

        # Отправляем запрос с системным промптом и историей
        # Пробуем разные варианты передачи system_instruction
        try:
            # Вариант 1: system_instruction как отдельный параметр (новый API)
            if self.system_prompt:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    system_instruction=self.system_prompt,
                    config=config,
                )
            else:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=config,
                )
        except (TypeError, ValueError) as e:
            # Вариант 2: если не поддерживается, пробуем без system_instruction
            # и добавляем его в начало истории
            if self.system_prompt:
                # Добавляем системный промпт как первое сообщение в истории
                system_message = {"role": "user", "parts": [{"text": str(self.system_prompt)}]}
                contents_with_system = [system_message] + contents
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=contents_with_system,
                    config=config,
                )
            else:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=config,
                )

        # Get response
        assistant_message = response.text
        if assistant_message is None:
            assistant_message = "Извините, не удалось получить ответ от модели."

        # Add assistant response to history
        self.add_message("model", assistant_message)
        self.save_history()
        return assistant_message

    def get_model_name(self) -> str:
        """Get the name of the model provider."""
        return "gemini"

    def load_history(self):
        """Load history from file and convert to unified format if needed."""
        super().load_history()
        # Convert old Gemini format to unified format if needed
        if (
            self.history
            and len(self.history) > 0
            and isinstance(self.history[0], dict)
            and "parts" in self.history[0]
        ):
            # Old format detected, convert it
            self.history = self._convert_from_model_format(self.history)
            self.save_history()  # Save in new format

