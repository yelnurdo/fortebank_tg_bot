"""Select which LLM provider implementation to use for digest generation."""

from __future__ import annotations

# Default to OpenAI GPT implementation. Swap the import below to switch providers.
from app.services.llm_gpt import GptDigestService as LlmDigestService

# Example for Gemini:
# from app.services.llm_gemini import GeminiDigestService as LlmDigestService
