"""
Factory para detectar e criar providers disponiveis.
"""

import logging
from typing import Dict, List, Optional

from .base_provider import BaseProvider, ProviderResponse
from .claude_provider import ClaudeProvider
from .gpt_provider import GPTProvider
from .gemini_provider import GeminiProvider
from .atic_provider import ATICProvider

logger = logging.getLogger(__name__)

# Todos os providers possiveis
ALL_PROVIDERS = {
    "claude": ClaudeProvider,
    "gpt": GPTProvider,
    "gemini": GeminiProvider,
    "atic_on": lambda: ATICProvider(grounding_enabled=True),
    "atic_off": lambda: ATICProvider(grounding_enabled=False),
}


def detect_and_create_providers(
    requested: Optional[List[str]] = None,
) -> Dict[str, BaseProvider]:
    """
    Detecta providers disponiveis e retorna dict.
    Se requested != None, filtra so os pedidos.
    """
    providers: Dict[str, BaseProvider] = {}

    targets = requested if requested else list(ALL_PROVIDERS.keys())

    for provider_id in targets:
        if provider_id not in ALL_PROVIDERS:
            logger.warning("[WARN] Provider desconhecido: %s", provider_id)
            continue

        factory = ALL_PROVIDERS[provider_id]
        try:
            instance = factory() if callable(factory) and not isinstance(factory, type) else factory()
            if instance.is_available():
                providers[provider_id] = instance
                logger.info(
                    "[OK] Provider disponivel: %s (%s)",
                    provider_id, instance.display_name
                )
            else:
                logger.info(
                    "[SKIP] Provider indisponivel: %s", provider_id
                )
        except Exception as e:
            logger.warning(
                "[WARN] Erro ao criar provider %s: %s", provider_id, e
            )

    return providers


__all__ = [
    "BaseProvider",
    "ProviderResponse",
    "ClaudeProvider",
    "GPTProvider",
    "GeminiProvider",
    "ATICProvider",
    "detect_and_create_providers",
]
