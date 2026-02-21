"""
Provider para GPT (OpenAI API).
Modelo: gpt-4o
"""

import os
import time
import logging
from typing import Optional

from .base_provider import BaseProvider, ProviderResponse

logger = logging.getLogger(__name__)

# Constantes
MODEL = "gpt-4o"
MAX_RETRIES = 3


class GPTProvider(BaseProvider):
    """Provider GPT via OpenAI SDK."""

    provider_id = "gpt"
    display_name = "GPT-4o"

    def __init__(self):
        self._client = None

    def _get_client(self):
        """Lazy init do client OpenAI."""
        if self._client is None:
            import openai
            self._client = openai.OpenAI(
                api_key=os.environ.get("OPENAI_API_KEY", "")
            )
        return self._client

    def query(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.3,
    ) -> ProviderResponse:
        """Envia prompt para GPT-4o com retry em 429."""
        import openai

        client = self._get_client()
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                start = time.perf_counter()
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                elapsed = time.perf_counter() - start

                choice = response.choices[0] if response.choices else None
                text = choice.message.content if choice else ""
                usage = response.usage

                return ProviderResponse(
                    text=text or "",
                    model=response.model or MODEL,
                    elapsed_seconds=round(elapsed, 2),
                    input_tokens=getattr(usage, "prompt_tokens", 0) if usage else 0,
                    output_tokens=getattr(usage, "completion_tokens", 0) if usage else 0,
                )

            except openai.RateLimitError as e:
                last_error = str(e)
                wait = 2 ** (attempt + 1)
                logger.warning(
                    "[RETRY] GPT rate limit, aguardando %ds (tentativa %d/%d)",
                    wait, attempt + 1, MAX_RETRIES
                )
                time.sleep(wait)

            except Exception as e:
                return ProviderResponse(
                    text="", model=MODEL, error=f"GPT error: {e}"
                )

        return ProviderResponse(
            text="", model=MODEL,
            error=f"GPT falhou apos {MAX_RETRIES} tentativas: {last_error}"
        )

    def is_available(self) -> bool:
        """Verifica se OPENAI_API_KEY esta definida."""
        return bool(os.environ.get("OPENAI_API_KEY"))
