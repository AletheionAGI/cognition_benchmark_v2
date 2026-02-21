"""
Provider para Claude (Anthropic API).
Modelo: claude-sonnet-4-20250514
"""

import os
import time
import logging
from typing import Optional

from .base_provider import BaseProvider, ProviderResponse

logger = logging.getLogger(__name__)

# Constantes
MODEL = "claude-sonnet-4-20250514"
MAX_RETRIES = 3
RETRY_CODES = (429, 529)


class ClaudeProvider(BaseProvider):
    """Provider Claude via Anthropic SDK."""

    provider_id = "claude"
    display_name = "Claude Sonnet 4"

    def __init__(self):
        self._client = None

    def _get_client(self):
        """Lazy init do client Anthropic."""
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(
                api_key=os.environ.get("ANTHROPIC_API_KEY", "")
            )
        return self._client

    def query(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.3,
    ) -> ProviderResponse:
        """Envia prompt para Claude com retry em 429/529."""
        import anthropic

        client = self._get_client()
        messages = [{"role": "user", "content": prompt}]
        kwargs = {
            "model": MODEL,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                start = time.perf_counter()
                response = client.messages.create(**kwargs)
                elapsed = time.perf_counter() - start

                text = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        text += block.text

                return ProviderResponse(
                    text=text,
                    model=response.model,
                    elapsed_seconds=round(elapsed, 2),
                    input_tokens=getattr(response.usage, "input_tokens", 0),
                    output_tokens=getattr(response.usage, "output_tokens", 0),
                )

            except anthropic.RateLimitError as e:
                last_error = str(e)
                wait = 2 ** (attempt + 1)
                logger.warning(
                    "[RETRY] Claude rate limit, aguardando %ds (tentativa %d/%d)",
                    wait, attempt + 1, MAX_RETRIES
                )
                time.sleep(wait)

            except anthropic.APIStatusError as e:
                if e.status_code in RETRY_CODES:
                    last_error = str(e)
                    wait = 2 ** (attempt + 1)
                    logger.warning(
                        "[RETRY] Claude status %d, aguardando %ds (tentativa %d/%d)",
                        e.status_code, wait, attempt + 1, MAX_RETRIES
                    )
                    time.sleep(wait)
                else:
                    return ProviderResponse(
                        text="", model=MODEL, error=f"Claude API error: {e}"
                    )

            except Exception as e:
                return ProviderResponse(
                    text="", model=MODEL, error=f"Claude error: {e}"
                )

        return ProviderResponse(
            text="", model=MODEL,
            error=f"Claude falhou apos {MAX_RETRIES} tentativas: {last_error}"
        )

    def is_available(self) -> bool:
        """Verifica se ANTHROPIC_API_KEY esta definida."""
        return bool(os.environ.get("ANTHROPIC_API_KEY"))
