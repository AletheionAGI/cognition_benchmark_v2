"""
Provider para Gemini (Google GenAI API).
Modelo: gemini-2.5-flash
"""

import os
import re
import time
import logging
from typing import Optional

from .base_provider import BaseProvider, ProviderResponse

logger = logging.getLogger(__name__)

# Constantes
MODEL = "gemini-2.5-flash"
MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 30


class GeminiProvider(BaseProvider):
    """Provider Gemini via Google GenAI SDK."""

    provider_id = "gemini"
    display_name = "Gemini 2.5 Flash"

    def __init__(self):
        self._client = None

    def _get_client(self):
        """Lazy init do client Google GenAI."""
        if self._client is None:
            from google import genai
            self._client = genai.Client(
                api_key=os.environ.get("GOOGLE_API_KEY", "")
            )
        return self._client

    def _extract_retry_delay(self, error_msg: str) -> int:
        """Extrai delay do header de erro ou usa default."""
        # Tenta extrair "retry after X seconds" ou similar
        match = re.search(r"retry\s+after\s+(\d+)", str(error_msg), re.IGNORECASE)
        if match:
            return int(match.group(1))
        return DEFAULT_RETRY_DELAY

    def query(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.3,
    ) -> ProviderResponse:
        """Envia prompt para Gemini com retry em 429/RESOURCE_EXHAUSTED."""
        from google.genai import types

        client = self._get_client()

        # Desabilita thinking para respostas deterministicas
        config = types.GenerateContentConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        )
        if system:
            config.system_instruction = system

        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                start = time.perf_counter()
                response = client.models.generate_content(
                    model=MODEL,
                    contents=prompt,
                    config=config,
                )
                elapsed = time.perf_counter() - start

                text = response.text or ""
                usage = getattr(response, "usage_metadata", None)

                return ProviderResponse(
                    text=text,
                    model=MODEL,
                    elapsed_seconds=round(elapsed, 2),
                    input_tokens=getattr(usage, "prompt_token_count", 0) if usage else 0,
                    output_tokens=getattr(usage, "candidates_token_count", 0) if usage else 0,
                )

            except Exception as e:
                error_str = str(e)
                is_rate_limit = (
                    "429" in error_str
                    or "RESOURCE_EXHAUSTED" in error_str
                    or "quota" in error_str.lower()
                )

                if is_rate_limit and attempt < MAX_RETRIES - 1:
                    last_error = error_str
                    wait = self._extract_retry_delay(error_str)
                    # Escalonamento por tentativa
                    wait = min(wait * (attempt + 1), 120)
                    logger.warning(
                        "[RETRY] Gemini rate limit, aguardando %ds (tentativa %d/%d)",
                        wait, attempt + 1, MAX_RETRIES
                    )
                    time.sleep(wait)
                elif is_rate_limit:
                    last_error = error_str
                else:
                    return ProviderResponse(
                        text="", model=MODEL, error=f"Gemini error: {e}"
                    )

        return ProviderResponse(
            text="", model=MODEL,
            error=f"Gemini falhou apos {MAX_RETRIES} tentativas: {last_error}"
        )

    def is_available(self) -> bool:
        """Verifica se GOOGLE_API_KEY esta definida e SDK instalado."""
        if not os.environ.get("GOOGLE_API_KEY"):
            return False
        try:
            from google import genai  # noqa: F401
            return True
        except ImportError:
            return False
