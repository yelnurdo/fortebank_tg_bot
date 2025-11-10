"""Google Gemini chat implementation with history management."""

from __future__ import annotations

import json
import os
from typing import Dict, List

from google import genai


class GeminiChat:
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
        self.client = client
        self.model = model
        self.system_prompt = system_prompt
        self.max_context_tokens = max_context_tokens
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.history: List[Dict[str, str]] = []
        self.history_file = history_file

    def add_message(self, role: str, content: str):
        """Добавить сообщение в историю."""
        self.history.append({"role": role, "parts": [{"text": content}]})

    def _estimate_tokens(self, text: str) -> int:
        """Примерная оценка токенов (1 токен ≈ 4 символа для русского/английского)."""
        if text is None:
            return 0
        return len(str(text)) // 4

    def _trim_history(self):
        """Обрезать историю, если она превышает лимит контекста."""
        if not self.history:
            return

        # Подсчитываем токены в системном промпте
        system_tokens = self._estimate_tokens(self.system_prompt)

        # Подсчитываем токены в истории
        history_tokens = sum(
            self._estimate_tokens(msg.get("parts", [{}])[0].get("text")) for msg in self.history
        )

        total_tokens = system_tokens + history_tokens

        # Если превышаем лимит, удаляем самые старые сообщения
        # Оставляем минимум последнее сообщение
        while total_tokens > self.max_context_tokens and len(self.history) > 1:
            # Удаляем самое старое сообщение
            removed = self.history.pop(0)
            removed_tokens = self._estimate_tokens(removed.get("parts", [{}])[0].get("text"))
            total_tokens -= removed_tokens

    def send_message(self, user_message: str) -> str:
        """Отправить сообщение и получить ответ."""
        # Добавляем сообщение пользователя в историю
        self.add_message("user", user_message)

        # Обрезаем историю при необходимости
        self._trim_history()

        # Формируем конфигурацию
        config = {
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
        }

        # Валидируем историю перед отправкой
        self._clean_history()
        
        # Создаем копию истории с правильной структурой
        contents = []
        for msg in self.history:
            if self._validate_message(msg):
                # Создаем правильную структуру для Gemini API
                validated_msg = {
                    "role": msg["role"],
                    "parts": []
                }
                for part in msg["parts"]:
                    if isinstance(part, dict):
                        if "text" in part and part["text"] is not None:
                            validated_msg["parts"].append({"text": str(part["text"])})
                        elif "data" in part:
                            validated_msg["parts"].append({"data": part["data"]})
                if validated_msg["parts"]:
                    contents.append(validated_msg)

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

        # Получаем ответ
        assistant_message = response.text
        if assistant_message is None:
            assistant_message = "Извините, не удалось получить ответ от модели."

        # Добавляем ответ ассистента в историю
        self.add_message("model", assistant_message)
        self.save_history()
        return assistant_message

    def clear_history(self):
        """Очистить историю чата."""
        self.history = []
        if self.history_file:
            self.save_history()

    def get_history_summary(self) -> Dict:
        """Получить информацию о текущей истории."""
        total_messages = len(self.history)
        system_tokens = self._estimate_tokens(self.system_prompt)
        history_tokens = sum(
            self._estimate_tokens(msg.get("parts", [{}])[0].get("text")) for msg in self.history
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
        }

    def save_history(self):
        """Сохранить историю в файл."""
        if not self.history_file:
            return

        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  Ошибка при сохранении истории: {e}")

    def _validate_message(self, msg: dict) -> bool:
        """Проверить и исправить структуру сообщения."""
        if not isinstance(msg, dict):
            return False
        
        if "role" not in msg:
            return False
        
        if "parts" not in msg or not isinstance(msg["parts"], list) or len(msg["parts"]) == 0:
            return False
        
        # Проверяем, что в parts есть text
        part = msg["parts"][0]
        if not isinstance(part, dict):
            return False
        
        # Должно быть либо text, либо data, но не оба
        if "text" not in part and "data" not in part:
            return False
        
        # Если text есть, но он None или пустой, исправляем
        if "text" in part:
            if part["text"] is None:
                part["text"] = ""
        
        return True
    
    def _clean_history(self):
        """Очистить историю от некорректных сообщений."""
        self.history = [msg for msg in self.history if self._validate_message(msg)]
    
    def load_history(self):
        """Загрузить историю из файла (если есть)."""
        if not self.history_file:
            return

        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
                    # Валидируем и очищаем историю
                    self._clean_history()
            except Exception as e:
                print(f"⚠️  Ошибка при загрузке истории: {e}")
                self.history = []

