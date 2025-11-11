"""Base abstract class for chat implementations."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from app.repositories.chat_history import ChatHistoryRepository


class BaseChat(ABC):
    """Abstract base class for chat implementations."""

    def __init__(
        self,
        system_prompt: str = "",
        max_context_tokens: int = 30000,
        temperature: float = 0.2,
        max_output_tokens: int = 2000,
        history_file: str | None = None,
        history_repository: Optional[ChatHistoryRepository] = None,
        user_id: Optional[int] = None,
        role: Optional[str] = None,
    ):
        self.system_prompt = system_prompt
        self.max_context_tokens = max_context_tokens
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.history_file = history_file
        self.history_repository = history_repository
        self.user_id = user_id
        self.role = role
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
        if self.history_repository and self.user_id and self.role:
            # Use async method in sync context
            try:
                # Try to get running loop
                try:
                    loop = asyncio.get_running_loop()
                    # If loop is running, schedule coroutine in the main loop
                    future = asyncio.run_coroutine_threadsafe(
                        self._clear_history_async(), loop
                    )
                    # Wait for completion with timeout
                    future.result(timeout=5)
                except RuntimeError:
                    # No running loop, can use asyncio.run()
                    asyncio.run(self._clear_history_async())
            except Exception as e:
                print(f"⚠️  Ошибка при очистке истории в БД: {e}")
        elif self.history_file:
            self.save_history()

    async def _clear_history_async(self):
        """Async method to clear history from database."""
        if self.history_repository and self.user_id and self.role:
            await self.history_repository.clear_history(self.user_id, self.role)

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
        """Save history to database or file."""
        print(f"🔍 save_history вызван: repository={self.history_repository is not None}, user_id={self.user_id}, role={self.role}, history_len={len(self.history)}")
        
        if self.history_repository and self.user_id and self.role:
            # Use async method in sync context
            try:
                # Try to get running loop
                try:
                    loop = asyncio.get_running_loop()
                    print(f"🔍 Event loop запущен, используем отдельный поток")
                    # If loop is running, we're in async context
                    # Create a task and wait for it using a different approach
                    # Use run_coroutine_threadsafe from a thread pool
                    import concurrent.futures
                    import threading
                    
                    result_container = {"done": False, "error": None}
                    
                    def run_async():
                        try:
                            # Create new event loop in this thread
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            try:
                                new_loop.run_until_complete(self._save_history_async())
                                result_container["done"] = True
                            finally:
                                new_loop.close()
                        except Exception as e:
                            result_container["error"] = e
                    
                    thread = threading.Thread(target=run_async, daemon=True)
                    thread.start()
                    thread.join(timeout=10)
                    
                    if result_container["error"]:
                        raise result_container["error"]
                    if not result_container["done"]:
                        raise TimeoutError("Save history operation timed out")
                    print(f"✅ save_history завершен успешно")
                except RuntimeError:
                    print(f"🔍 Event loop не запущен, используем asyncio.run()")
                    # No running loop, can use asyncio.run()
                    asyncio.run(self._save_history_async())
                    print(f"✅ save_history завершен успешно (asyncio.run)")
            except Exception as e:
                import traceback
                error_msg = f"⚠️  Ошибка при сохранении истории в БД: {e}\n{traceback.format_exc()}"
                print(error_msg)
        elif self.history_file:
            print(f"💾 Сохранение в файл: {self.history_file}")
            self._save_history_file()
        else:
            print(f"⚠️  Не могу сохранить: нет repository или user_id/role")

    async def _save_history_async(self):
        """Save history to database."""
        if not (self.history_repository and self.user_id and self.role):
            print(f"⚠️  Не могу сохранить: repository={self.history_repository is not None}, user_id={self.user_id}, role={self.role}")
            return

        try:
            # Always reinitialize to ensure we have a pool for the current event loop
            # This is necessary when running in a separate thread with new event loop
            await self.history_repository.initialize()
            
            print(f"💾 Сохранение истории: user_id={self.user_id}, role={self.role}, messages={len(self.history)}")
            
            # Clear existing history and save all messages (history is already trimmed)
            await self.history_repository.clear_history(self.user_id, self.role)
            
            saved_count = 0
            for msg in self.history:
                await self.history_repository.add_message(
                    self.user_id,
                    self.role,
                    msg.get("role", "user"),
                    msg.get("content", ""),
                )
                saved_count += 1
            
            print(f"✅ История сохранена: {saved_count} сообщений для user_id={self.user_id}, role={self.role}")
        except Exception as e:
            import traceback
            error_msg = f"⚠️  Ошибка при сохранении истории в БД (async): {e}\n{traceback.format_exc()}"
            print(error_msg)

    def _save_history_file(self):
        """Save history to file in unified format."""
        if not self.history_file:
            return

        try:
            import json

            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  Ошибка при сохранении истории в файл: {e}")

    def load_history(self):
        """Load history from database or file."""
        if self.history_repository and self.user_id and self.role:
            # Use async method in sync context
            try:
                # Try to get running loop
                try:
                    loop = asyncio.get_running_loop()
                    # If loop is running, we're in async context
                    # Create a task and wait for it using a different approach
                    import threading
                    
                    result_container = {"result": [], "error": None}
                    
                    def run_async():
                        try:
                            # Create new event loop in this thread
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            try:
                                result_container["result"] = new_loop.run_until_complete(
                                    self._load_history_async()
                                )
                            finally:
                                new_loop.close()
                        except Exception as e:
                            result_container["error"] = e
                    
                    thread = threading.Thread(target=run_async, daemon=True)
                    thread.start()
                    thread.join(timeout=10)
                    
                    if result_container["error"]:
                        raise result_container["error"]
                    self.history = result_container["result"]
                except RuntimeError:
                    # No running loop, can use asyncio.run()
                    self.history = asyncio.run(self._load_history_async())
            except Exception as e:
                import traceback
                error_msg = f"⚠️  Ошибка при загрузке истории из БД: {e}\n{traceback.format_exc()}"
                print(error_msg)
                self.history = []
        elif self.history_file:
            self._load_history_file()

    async def _load_history_async(self) -> List[Dict[str, str]]:
        """Load history from database."""
        if not (self.history_repository and self.user_id and self.role):
            print(f"⚠️  Не могу загрузить: repository={self.history_repository is not None}, user_id={self.user_id}, role={self.role}")
            return []

        try:
            # Always reinitialize to ensure we have a pool for the current event loop
            # This is necessary when running in a separate thread with new event loop
            await self.history_repository.initialize()
            
            print(f"📖 Загрузка истории: user_id={self.user_id}, role={self.role}")
            history = await self.history_repository.get_history(self.user_id, self.role)
            print(f"✅ История загружена: {len(history)} сообщений для user_id={self.user_id}, role={self.role}")
            return history
        except Exception as e:
            import traceback
            error_msg = f"⚠️  Ошибка при загрузке истории из БД (async): {e}\n{traceback.format_exc()}"
            print(error_msg)
            return []

    def _load_history_file(self):
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
                print(f"⚠️  Ошибка при загрузке истории из файла: {e}")
                self.history = []

