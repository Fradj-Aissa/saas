import asyncio
import logging
import os
from typing import List, Optional

import structlog

from app.ai.gemini.prompts import ARABIC_MARKDOWN_PROMPT
from app.ai.gemini.text_chunker import chunk_text

logger = structlog.get_logger()


class GeminiClient:
    def __init__(self) -> None:
        self.genai = None
        self.token_usage: List[int] = []
        api_key = os.getenv("GOOGLE_API_KEY")
        try:
            import google.generativeai as genai

            self.genai = genai
            if api_key:
                self.genai.configure(api_key=api_key)
        except ImportError:
            logger.warning("gemini_client_not_installed")

    async def _send_chunk(self, chunk: str) -> str:
        if self.genai is None:
            raise RuntimeError("Gemini client library is not available")

        for attempt in range(1, 4):
            try:
                response = await asyncio.to_thread(
                    lambda: self.genai.ChatCompletion.create(
                        model="gemini-pro",
                        messages=[
                            {"role": "user", "content": ARABIC_MARKDOWN_PROMPT.format(content=chunk)}
                        ],
                        temperature=0.2,
                    )
                )
                if response and getattr(response, "choices", None):
                    content = response.choices[0].message.get("content", "")
                    usage = getattr(response, "usage", None)
                    if usage is not None:
                        prompt_tokens = getattr(usage, "prompt_tokens", 0)
                        completion_tokens = getattr(usage, "completion_tokens", 0)
                        self.token_usage.append(prompt_tokens + completion_tokens)
                    return content
                raise RuntimeError("Gemini response missing content")
            except Exception as exc:
                logger.warning("gemini_chunk_failed", attempt=attempt, error=str(exc))
                if attempt == 3:
                    raise
                await asyncio.sleep(2 ** attempt)
        raise RuntimeError("Gemini failed after retries")

    async def format_text(self, text: str) -> str:
        chunks = chunk_text(text)
        if not chunks:
            return ""

        formatted_parts: List[str] = []
        for chunk in chunks:
            formatted_parts.append(await self._send_chunk(chunk))
        return "\n\n".join(part.strip() for part in formatted_parts if part.strip())

    def get_token_usage(self) -> int:
        return sum(self.token_usage)
