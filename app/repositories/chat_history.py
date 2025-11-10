"""Repository for storing chat history in PostgreSQL."""

from __future__ import annotations

import json
import logging
from typing import List, Optional

import asyncpg

logger = logging.getLogger(__name__)


class ChatHistoryRepository:
    """Repository for managing chat history in PostgreSQL."""

    def __init__(self, dsn: str):
        self._dsn = dsn
        self._pool: Optional[asyncpg.Pool] = None
        self._pools_by_loop = {}  # Store pools by event loop ID

    async def initialize(self) -> None:
        """Initialize database connection pool and create tables if needed."""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop_id = id(loop)
            
            # Check if we already have a pool for this loop
            if loop_id in self._pools_by_loop:
                self._pool = self._pools_by_loop[loop_id]
                return
            
            # Create new pool for this loop
            self._pool = await asyncpg.create_pool(
                self._dsn,
                min_size=1,
                max_size=10,
                command_timeout=60,
            )
            self._pools_by_loop[loop_id] = self._pool
            await self._create_tables()
        except RuntimeError:
            # No running loop, create pool anyway
            if self._pool is None:
                self._pool = await asyncpg.create_pool(
                    self._dsn,
                    min_size=1,
                    max_size=10,
                    command_timeout=60,
                )
                await self._create_tables()

    async def close(self) -> None:
        """Close database connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def _create_tables(self) -> None:
        """Create chat_history table if it doesn't exist."""
        async with self._pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    role VARCHAR(50) NOT NULL DEFAULT 'user',
                    message_role VARCHAR(50) NOT NULL,
                    message_content TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, role, id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_chat_history_user_role 
                ON chat_history(user_id, role);
                
                CREATE INDEX IF NOT EXISTS idx_chat_history_created_at 
                ON chat_history(created_at);
            """)
            logger.info("Chat history table created/verified")

    async def get_history(
        self, user_id: int, role: str = "user"
    ) -> List[dict[str, str]]:
        """
        Get chat history for a user and role.
        
        Returns:
            List of messages in format [{"role": "user", "content": "..."}, ...]
        """
        if self._pool is None:
            await self.initialize()

        async with self._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT message_role, message_content
                FROM chat_history
                WHERE user_id = $1 AND role = $2
                ORDER BY created_at ASC, id ASC
            """, user_id, role)

        return [
            {"role": row["message_role"], "content": row["message_content"]}
            for row in rows
        ]

    async def add_message(
        self, user_id: int, role: str, message_role: str, message_content: str
    ) -> None:
        """Add a message to chat history."""
        if self._pool is None:
            await self.initialize()

        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO chat_history (user_id, role, message_role, message_content)
                VALUES ($1, $2, $3, $4)
            """, user_id, role, message_role, message_content)
            logger.debug(f"Message added: user_id={user_id}, role={role}, message_role={message_role}, content_length={len(message_content)}")

    async def clear_history(self, user_id: int, role: Optional[str] = None) -> None:
        """
        Clear chat history for a user.
        
        Args:
            user_id: User ID
            role: If specified, clear only this role's history. Otherwise clear all.
        """
        if self._pool is None:
            await self.initialize()

        async with self._pool.acquire() as conn:
            if role:
                result = await conn.execute("""
                    DELETE FROM chat_history
                    WHERE user_id = $1 AND role = $2
                """, user_id, role)
                logger.info(f"Cleared history: user_id={user_id}, role={role}, result={result}")
            else:
                result = await conn.execute("""
                    DELETE FROM chat_history
                    WHERE user_id = $1
                """, user_id)
                logger.info(f"Cleared all history: user_id={user_id}, result={result}")

    async def get_message_count(self, user_id: int, role: str = "user") -> int:
        """Get total message count for a user and role."""
        if self._pool is None:
            await self.initialize()

        async with self._pool.acquire() as conn:
            count = await conn.fetchval("""
                SELECT COUNT(*)
                FROM chat_history
                WHERE user_id = $1 AND role = $2
            """, user_id, role)

        return count or 0

