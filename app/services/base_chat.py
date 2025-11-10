"""Base abstract class for chat implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List


class BaseChat(ABC):
    """Abstract base class for chat implementations."""

    def __init__(
        self,
        system_prompt: str = "",
        max_context_tokens: int = 30000,
        temperature: float = 0.2,
        max_output_tokens: int = 2000,
        history_file: str | None = None,
    ):
        self.system_prompt = system_prompt
        self.max_context_tokens = max_context_tokens
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.history_file = history_file
        self.history: List[Dict[str, str]] = []

    @abstractmethod
    def send_message(self, user_message: str) -> str:
        """Send a message and get a response."""
        pass

    @abstractmethod
    def _convert_to_model_format(self, history: List[Dict[str, str]]) -> any:
        """Convert unified history format to model-specific format."""
        pass

    @abstractmethod
    def _convert_from_model_format(self, model_history: any) -> List[Dict[str, str]]:
        """Convert model-specific format to unified history format."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the name of the model provider."""
        pass

    def add_message(self, role: str, content: str):
        """Add a message to history in unified format."""
        self.history.append({"role": role, "content": content})

    def _estimate_tokens(self, text: str) -> int:
        """Estimate tokens (1 token ≈ 4 characters for Russian/English)."""
        if text is None:
            return 0
        return len(str(text)) // 4

    def _trim_history(self):
        """Trim history if it exceeds context limit."""
        if not self.history:
            return

        system_tokens = self._estimate_tokens(self.system_prompt)
        history_tokens = sum(
            self._estimate_tokens(msg.get("content", "")) for msg in self.history
        )

        total_tokens = system_tokens + history_tokens

        while total_tokens > self.max_context_tokens and len(self.history) > 1:
            removed = self.history.pop(0)
            removed_tokens = self._estimate_tokens(removed.get("content", ""))
            total_tokens -= removed_tokens

    def clear_history(self):
        """Clear chat history."""
        self.history = []
        if self.history_file:
            self.save_history()

    def get_history_summary(self) -> Dict:
        """Get information about current history."""
        total_messages = len(self.history)
        system_tokens = self._estimate_tokens(self.system_prompt)
        history_tokens = sum(
            self._estimate_tokens(msg.get("content", "")) for msg in self.history
        )

        return {
            "total_messages": total_messages,
            "system_tokens": system_tokens,
            "history_tokens": history_tokens,
            "total_tokens": system_tokens + history_tokens,
            "max_context_tokens": self.max_context_tokens,
            "usage_percent": round(
                (system_tokens + history_tokens) / self.max_context_tokens * 100, 2
            ),
            "model": self.get_model_name(),
        }

    def save_history(self):
        """Save history to file in unified format."""
        if not self.history_file:
            return

        try:
            import json

            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  Ошибка при сохранении истории: {e}")

    def load_history(self):
        """Load history from file in unified format."""
        if not self.history_file:
            return

        import os
        import json

        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    # Ensure it's in unified format
                    if isinstance(loaded, list):
                        self.history = loaded
                    else:
                        self.history = []
            except Exception as e:
                print(f"⚠️  Ошибка при загрузке истории: {e}")
                self.history = []

