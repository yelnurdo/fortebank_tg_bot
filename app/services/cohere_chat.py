"""Cohere chat implementation with history management."""

from __future__ import annotations

import logging
from typing import Dict, List

import cohere

from app.services.base_chat import BaseChat

logger = logging.getLogger(__name__)


class CohereChat(BaseChat):
    """Cohere chat implementation with shared history."""

    def __init__(
        self,
        api_key: str,
        model: str = "command-r-08-2024",
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
        self.client = cohere.Client(api_key=api_key)
        self.model = model
        # Load history after initialization
        self.load_history()

    def _convert_to_model_format(self, history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Convert unified history format to Cohere format."""
        # Cohere format: [{"role": "USER", "message": "..."}, {"role": "CHATBOT", "message": "..."}]
        # Note: Cohere API requires "message" field, not "content"
        converted = []
        for msg in history:
            content = msg.get("content", "").strip()
            # Skip empty messages as Cohere requires all elements to have a message
            if not content:
                continue
                
            role = msg.get("role", "").upper()
            # Map "model" to "CHATBOT" for Cohere
            if role == "MODEL" or role == "ASSISTANT":
                role = "CHATBOT"
            elif role != "USER":
                role = "USER"
            converted.append({"role": role, "message": content})
        return converted

    def _convert_from_model_format(self, model_history: any) -> List[Dict[str, str]]:
        """Convert Cohere format to unified history format."""
        # This is not used since we maintain unified format
        return self.history

    def get_model_name(self) -> str:
        """Get the name of the model provider."""
        return "cohere"

    def send_message(self, user_message: str) -> str:
        """Send a message and get a response."""
        # Add user message to history
        self.add_message("user", user_message)

        # Trim history if needed
        self._trim_history()

        # Convert to Cohere format
        chat_history = self._convert_to_model_format(self.history[:-1])  # Exclude the last user message

        try:
            response = self.client.chat(
                model=self.model,
                message=user_message,
                chat_history=chat_history,
                preamble=self.system_prompt if self.system_prompt else None,
                temperature=self.temperature,
                max_tokens=self.max_output_tokens,
            )

            assistant_message = response.text
            if assistant_message is None:
                assistant_message = "Извините, не удалось получить ответ от модели."

            # Add assistant response to history
            self.add_message("model", assistant_message)
            self.save_history()
            return assistant_message

        except Exception as e:
            logger.error(f"Error calling Cohere API: {e}")
            raise

