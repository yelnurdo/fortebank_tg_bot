"""OpenAI GPT chat implementation with history management."""

from __future__ import annotations

import logging
from typing import Dict, List

from openai import OpenAI

from app.services.base_chat import BaseChat

logger = logging.getLogger(__name__)


class GPTChat(BaseChat):
    """OpenAI GPT chat implementation with shared history."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4.1-mini",
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
        self.client = OpenAI(api_key=api_key)
        self.model = model
        # Load history after initialization
        self.load_history()

    def _convert_to_model_format(self, history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Convert unified history format to OpenAI format."""
        # OpenAI format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        converted = []
        for msg in history:
            role = msg.get("role", "")
            # Map "model" to "assistant" for OpenAI
            if role == "model":
                role = "assistant"
            elif role not in ["user", "assistant", "system"]:
                role = "user"
            converted.append({"role": role, "content": msg.get("content", "")})
        return converted

    def _convert_from_model_format(self, model_history: any) -> List[Dict[str, str]]:
        """Convert OpenAI format to unified history format."""
        # This is not used since we maintain unified format
        return self.history

    def get_model_name(self) -> str:
        """Get the name of the model provider."""
        return "openai"

    def send_message(self, user_message: str) -> str:
        """Send a message and get a response."""
        # Add user message to history
        self.add_message("user", user_message)

        # Trim history if needed
        self._trim_history()

        # Convert to OpenAI format
        messages = self._convert_to_model_format(self.history)

        # Add system prompt if not already in history
        if self.system_prompt and not any(
            msg.get("role") == "system" for msg in messages
        ):
            messages.insert(0, {"role": "system", "content": self.system_prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_output_tokens,
            )

            assistant_message = response.choices[0].message.content
            if assistant_message is None:
                assistant_message = "Извините, не удалось получить ответ от модели."

            # Add assistant response to history
            self.add_message("model", assistant_message)
            self.save_history()
            return assistant_message

        except Exception as e:
            logger.error(f"Error calling GPT API: {e}")
            raise

