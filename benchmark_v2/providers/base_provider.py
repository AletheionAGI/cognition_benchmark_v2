"""
Classe base abstrata para providers do benchmark v2.
Define interface comum para todos os modelos testados.
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ProviderResponse:
    """Resposta padronizada de qualquer provider."""
    text: str
    model: str
    elapsed_seconds: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    error: Optional[str] = None


class BaseProvider(ABC):
    """Interface base para providers de LLM."""

    provider_id: str = ""
    display_name: str = ""

    @abstractmethod
    def query(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.3,
    ) -> ProviderResponse:
        """Envia prompt e retorna resposta."""
        ...

    def query_multi_round(
        self,
        prompts: List[str],
        system: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.3,
    ) -> List[Dict[str, str]]:
        """
        Conversa multi-turno. Acumula contexto entre rounds.
        Retorna lista de dicts com 'role' e 'content'.
        """
        conversation: List[Dict[str, str]] = []

        for prompt_text in prompts:
            conversation.append({"role": "user", "content": prompt_text})

            # Monta prompt completo com historico
            full_prompt = self._build_conversation_prompt(conversation)
            response = self.query(
                full_prompt,
                system=system,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            conversation.append({
                "role": "assistant",
                "content": response.text,
                "elapsed": response.elapsed_seconds,
                "model": response.model,
                "error": response.error,
            })

        return conversation

    def _build_conversation_prompt(
        self, conversation: List[Dict[str, str]]
    ) -> str:
        """Serializa historico de conversa em texto."""
        parts = []
        for msg in conversation:
            role = msg["role"]
            content = msg["content"]
            if role == "user":
                parts.append(f"User: {content}")
            elif role == "assistant":
                parts.append(f"Assistant: {content}")
        return "\n\n".join(parts)

    @abstractmethod
    def is_available(self) -> bool:
        """Verifica se o provider esta disponivel (API key, modelo, etc.)."""
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.provider_id}>"
