"""
Provider para ATIC (TautoCoordinator).
Dois modos: grounding ON e OFF.
"""

import os
import sys
import time
import logging
from typing import Dict, List, Optional

from .base_provider import BaseProvider, ProviderResponse

logger = logging.getLogger(__name__)

# Path do projeto ATIC
ATIC_PROJECT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "atic"
)


def _ensure_atic_path():
    """Adiciona path do ATIC ao sys.path se necessario."""
    if ATIC_PROJECT_PATH not in sys.path:
        sys.path.insert(0, ATIC_PROJECT_PATH)


class ATICProvider(BaseProvider):
    """Provider ATIC via TautoCoordinator."""

    def __init__(self, grounding_enabled: bool = True):
        self._grounding_enabled = grounding_enabled
        self._coordinator = None

        if grounding_enabled:
            self.provider_id = "atic_on"
            self.display_name = "ATIC (Grounding ON)"
        else:
            self.provider_id = "atic_off"
            self.display_name = "ATIC (Grounding OFF)"

    def _create_coordinator(self):
        """Cria instancia do TautoCoordinator com config adequada."""
        _ensure_atic_path()

        # Configura env vars antes de reload
        # IMPORTANTE: desabilita agents que escrevem no disco (CodeAgent, FileAgent)
        # e web search para evitar side-effects durante benchmark
        env_overrides = {
            "ENABLE_GROUNDING": str(self._grounding_enabled).lower(),
            "ENABLE_VERIFICATION_LOOP": str(self._grounding_enabled).lower(),
            "ENABLE_CONTRADICTION_DETECTION": str(self._grounding_enabled).lower(),
            "ENABLE_CITATION_TRACKING": str(self._grounding_enabled).lower(),
            "ENABLE_TRI_BRAIN": "false",
            "ENABLE_CONSCIOUSNESS": "false",
            "ENABLE_DOMAIN_TRACKING": "false",
            "ENABLE_STRATEGIC_PLANNING": "false",
            "ENABLE_CAUSAL_STATE": "false",
            "ENABLE_WORLD_MODEL": "false",
            "ENABLE_ADVANCED_MEMORY": "false",
            "ENABLE_CAUSAL_GRAPH": "false",
            "ENABLE_GOAL_STACK": "false",
            "ENABLE_INTENTIONALITY_VECTOR": "false",
            "ENABLE_EIDOS_DECAY": "false",
            "ENABLE_INTROSPECTION": "false",
            "ENABLE_CODE_EXECUTION": "false",
            "ENABLE_WEB_SEARCH": "false",
            "ENABLE_SESSION_RULES": "true",
            "ENABLE_CONTEXT_MANAGER": "true",
            "ENABLE_AGENCY_SCAFFOLD": "true",
            "ENABLE_ARBITRATION": "true",
        }
        for key, value in env_overrides.items():
            os.environ[key] = value

        from src.config.atic_config import reload_config
        reload_config()

        from src.core.tauto_coordinator import TautoCoordinator
        coordinator = TautoCoordinator(
            enable_epistemic=True,
            enable_consensus=False,
            enable_agents=True,
            enable_memory=False,
            enable_session_rules=True,
            enable_context_manager=True,
            enable_agency_scaffold=True,
            enable_arbitration=True,
        )

        # IMPORTANTE: desregistra agents que criam arquivos no disco
        # para evitar side-effects durante benchmark
        if coordinator.orchestrator:
            from src.agents.base_agent import AgentType
            coordinator.orchestrator.unregister_agent(AgentType.FILE)
            coordinator.orchestrator.unregister_agent(AgentType.CODE)
            logger.info(
                "[OK] FileAgent e CodeAgent desregistrados (benchmark mode)"
            )

        return coordinator

    def _get_coordinator(self):
        """Lazy init do coordinator."""
        if self._coordinator is None:
            self._coordinator = self._create_coordinator()
        return self._coordinator

    def query(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.3,
    ) -> ProviderResponse:
        """Envia prompt para ATIC."""
        try:
            coordinator = self._get_coordinator()
            coordinator.reset_session()

            # TautoCoordinator.process() espera context como string
            context_str = system if system else None

            start = time.perf_counter()
            result = coordinator.process(prompt, context=context_str)
            elapsed = time.perf_counter() - start

            text = result.text if hasattr(result, "text") else str(result)

            return ProviderResponse(
                text=text,
                model=f"atic_{'on' if self._grounding_enabled else 'off'}",
                elapsed_seconds=round(elapsed, 2),
            )

        except Exception as e:
            logger.error("[ERROR] ATIC provider falhou: %s", e)
            return ProviderResponse(
                text="",
                model=f"atic_{'on' if self._grounding_enabled else 'off'}",
                error=f"ATIC error: {e}",
            )

    def query_multi_round(
        self,
        prompts: List[str],
        system: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.3,
    ) -> List[Dict[str, str]]:
        """
        Multi-round com ATIC. Usa reset_session() no inicio
        e acumula contexto entre rounds.
        """
        try:
            coordinator = self._get_coordinator()
            coordinator.reset_session()
        except Exception as e:
            return [{"role": "system", "content": "", "error": str(e)}]

        conversation: List[Dict[str, str]] = []
        accumulated_context = ""

        for prompt_text in prompts:
            conversation.append({"role": "user", "content": prompt_text})

            full_prompt = prompt_text
            if accumulated_context:
                full_prompt = (
                    f"Contexto anterior:\n{accumulated_context}\n\n"
                    f"Nova pergunta: {prompt_text}"
                )

            # TautoCoordinator.process() espera context como string
            context_str = system if system else None

            try:
                start = time.perf_counter()
                result = coordinator.process(full_prompt, context=context_str)
                elapsed = time.perf_counter() - start

                text = result.text if hasattr(result, "text") else str(result)

                conversation.append({
                    "role": "assistant",
                    "content": text,
                    "elapsed": round(elapsed, 2),
                    "model": f"atic_{'on' if self._grounding_enabled else 'off'}",
                    "error": None,
                })

                accumulated_context += f"\nUser: {prompt_text}\nAssistant: {text}\n"

            except Exception as e:
                conversation.append({
                    "role": "assistant",
                    "content": "",
                    "elapsed": 0.0,
                    "model": f"atic_{'on' if self._grounding_enabled else 'off'}",
                    "error": str(e),
                })

        return conversation

    def is_available(self) -> bool:
        """Verifica se TautoCoordinator e importavel."""
        try:
            _ensure_atic_path()
            from src.core.tauto_coordinator import TautoCoordinator  # noqa: F401
            return True
        except ImportError:
            return False
