"""
Camada 3 de avaliacao: LLM judge com rotation e tiebreak.
Nenhum modelo avalia a si mesmo.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ..providers.base_provider import BaseProvider

logger = logging.getLogger(__name__)

# Rotacao de juizes: provider -> judge primario
JUDGE_ROTATION = {
    "claude": "gpt",
    "gpt": "claude",
    "gemini": "claude",
    "atic_on": "gpt",
    "atic_off": "gpt",
}

# Fallback: se judge primario indisponivel
JUDGE_FALLBACK = {
    "claude": "gemini",
    "gpt": "gemini",
    "gemini": "gpt",
    "atic_on": "claude",
    "atic_off": "claude",
}

# Terceiro juiz para tiebreak
TIEBREAK_JUDGE = {
    "claude": "gemini",
    "gpt": "gemini",
    "gemini": "gpt",
    "atic_on": "gemini",
    "atic_off": "gemini",
}

# Template do prompt de avaliacao
JUDGE_PROMPT_TEMPLATE = """You are an expert evaluator assessing an AI model's response quality.

## Task Description
Test: {test_name}
Category: {category}

## User Prompt(s)
{prompts}

## Model Response(s)
{responses}

## Evaluation Rubric
{rubric}

IMPORTANT: Score 0-3 ONLY. Output EXACTLY in this format (nothing else):
SCORE: N
REASON: Your explanation here (1-2 sentences)"""


@dataclass
class JudgeResult:
    """Resultado da avaliacao por LLM judge."""
    score_raw: int  # 0-3
    normalized: float  # 0.0-1.0
    reason: str = ""
    judge_model: str = ""
    judge_provider_id: str = ""
    tiebreak_used: bool = False
    tiebreak_details: str = ""


@dataclass
class JudgeAudit:
    """Informacoes de auditoria da avaliacao."""
    primary_judge: str
    primary_score: int
    primary_reason: str
    tiebreak_judge: Optional[str] = None
    tiebreak_score: Optional[int] = None
    tiebreak_reason: Optional[str] = None
    final_source: str = "primary"


def evaluate_judge(
    test_name: str,
    category: str,
    prompts: List[str],
    rounds: List[Dict[str, str]],
    rubric: str,
    evaluated_provider_id: str,
    available_providers: Dict[str, BaseProvider],
    structural_normalized: float = 0.0,
    reference_normalized: float = 0.0,
    enable_tiebreak: bool = True,
) -> Tuple[JudgeResult, JudgeAudit]:
    """
    Avalia resposta usando LLM judge com rotation.
    Retorna (JudgeResult, JudgeAudit).
    """
    # Seleciona judge primario
    judge_id = _select_judge(evaluated_provider_id, available_providers)
    if not judge_id:
        logger.warning("[WARN] Nenhum judge disponivel para %s", evaluated_provider_id)
        return _fallback_result(), JudgeAudit(
            primary_judge="none", primary_score=0, primary_reason="No judge available"
        )

    judge_provider = available_providers[judge_id]

    # Prepara prompt do judge
    prompt_text = _format_prompts(prompts)
    response_text = _format_responses(rounds)

    judge_prompt = JUDGE_PROMPT_TEMPLATE.format(
        test_name=test_name,
        category=category,
        prompts=prompt_text,
        responses=response_text,
        rubric=rubric,
    )

    # Avaliacao primaria
    primary_score, primary_reason = _call_judge(judge_provider, judge_prompt)

    audit = JudgeAudit(
        primary_judge=judge_id,
        primary_score=primary_score,
        primary_reason=primary_reason,
    )

    # Tiebreak: verifica divergencia entre layers
    if enable_tiebreak and _needs_tiebreak(
        primary_score, structural_normalized, reference_normalized
    ):
        tiebreak_id = _select_tiebreak_judge(
            evaluated_provider_id, judge_id, available_providers
        )
        if tiebreak_id:
            tiebreak_provider = available_providers[tiebreak_id]
            tb_score, tb_reason = _call_judge(tiebreak_provider, judge_prompt)

            audit.tiebreak_judge = tiebreak_id
            audit.tiebreak_score = tb_score
            audit.tiebreak_reason = tb_reason

            # Decisao: se tiebreak concorda com primario, mantem
            # Se concorda com layers 1+2, usa media
            layer_avg = (structural_normalized + reference_normalized) / 2.0
            layer_score_equiv = int(round(layer_avg * 3.0))

            if abs(tb_score - primary_score) <= 1:
                # Tiebreak concorda com primario
                final_score = primary_score
                audit.final_source = "primary (tiebreak confirmed)"
            elif abs(tb_score - layer_score_equiv) <= 1:
                # Tiebreak concorda com layers
                final_score = round((primary_score + tb_score) / 2.0)
                audit.final_source = "average (tiebreak sided with layers)"
            else:
                # Sem consenso, usa media
                final_score = round((primary_score + tb_score) / 2.0)
                audit.final_source = "average (no consensus)"

            return JudgeResult(
                score_raw=final_score,
                normalized=final_score / 3.0,
                reason=primary_reason,
                judge_model=judge_provider.display_name,
                judge_provider_id=judge_id,
                tiebreak_used=True,
                tiebreak_details=f"TB judge={tiebreak_id}, score={tb_score}",
            ), audit

    # Sem tiebreak
    return JudgeResult(
        score_raw=primary_score,
        normalized=primary_score / 3.0,
        reason=primary_reason,
        judge_model=judge_provider.display_name,
        judge_provider_id=judge_id,
    ), audit


def _select_judge(
    provider_id: str,
    available: Dict[str, BaseProvider],
) -> Optional[str]:
    """Seleciona judge primario (nunca o mesmo provider_id exato)."""
    # Tenta rotation padrao
    primary = JUDGE_ROTATION.get(provider_id)
    if primary and primary in available and primary != provider_id:
        return primary

    # Tenta fallback
    fallback = JUDGE_FALLBACK.get(provider_id)
    if fallback and fallback in available and fallback != provider_id:
        return fallback

    # Ultimo recurso: qualquer outro provider (atic_on pode julgar atic_off)
    for pid in available:
        if pid != provider_id:
            return pid

    return None


def _select_tiebreak_judge(
    provider_id: str,
    primary_judge_id: str,
    available: Dict[str, BaseProvider],
) -> Optional[str]:
    """Seleciona terceiro juiz para tiebreak."""
    # Tenta tiebreak padrao
    tb = TIEBREAK_JUDGE.get(provider_id)
    if tb and tb in available and tb != primary_judge_id and tb != provider_id:
        return tb

    # Qualquer outro que nao seja o provider nem o judge primario
    for pid in available:
        if pid != provider_id and pid != primary_judge_id:
            return pid

    return None


def _needs_tiebreak(
    judge_score: int,
    structural_norm: float,
    reference_norm: float,
) -> bool:
    """Verifica se precisa tiebreak (divergencia > 1.5 pontos normalizados)."""
    judge_norm = judge_score / 3.0
    layer_avg = (structural_norm + reference_norm) / 2.0
    divergence = abs(judge_norm - layer_avg)
    return divergence > 0.5  # Equivalente a ~1.5 pontos em escala 0-3


def _call_judge(
    provider: BaseProvider,
    prompt: str,
) -> Tuple[int, str]:
    """Chama judge e extrai score + reason."""
    try:
        response = provider.query(
            prompt=prompt,
            system="You are an expert AI evaluator. Be objective and fair.",
            max_tokens=200,
            temperature=0.1,
        )

        if response.error:
            logger.warning("[WARN] Judge error: %s", response.error)
            return 0, f"Judge error: {response.error}"

        score, reason = _parse_judge_response(response.text)
        return score, reason

    except Exception as e:
        logger.error("[ERROR] Judge call failed: %s", e)
        return 0, f"Judge exception: {e}"


def _parse_judge_response(text: str) -> Tuple[int, str]:
    """Extrai SCORE e REASON do output do judge."""
    # Busca SCORE: N
    score_match = re.search(r"SCORE:\s*(\d)", text)
    reason_match = re.search(r"REASON:\s*(.+)", text, re.DOTALL)

    score = 0
    if score_match:
        raw = int(score_match.group(1))
        score = max(0, min(3, raw))  # Clamp 0-3

    reason = ""
    if reason_match:
        reason = reason_match.group(1).strip()[:200]

    if not score_match:
        # Fallback: tenta extrair qualquer numero 0-3
        nums = re.findall(r"\b([0-3])\b", text)
        if nums:
            score = int(nums[0])
        reason = f"(parse fallback) {text[:150]}"

    return score, reason


def _format_prompts(prompts: List[str]) -> str:
    """Formata lista de prompts para o judge."""
    if len(prompts) == 1:
        return prompts[0]
    parts = []
    for i, p in enumerate(prompts, 1):
        parts.append(f"Round {i}: {p}")
    return "\n".join(parts)


def _format_responses(rounds: List[Dict[str, str]]) -> str:
    """Formata respostas do modelo para o judge."""
    parts = []
    round_num = 0
    for msg in rounds:
        if msg.get("role") == "assistant":
            round_num += 1
            content = msg.get("content", "")
            # Trunca respostas muito longas para o judge
            if len(content) > 2000:
                content = content[:2000] + "\n[... truncated]"
            parts.append(f"Response {round_num}:\n{content}")
    return "\n\n".join(parts)


def _fallback_result() -> JudgeResult:
    """Resultado fallback quando nenhum judge esta disponivel."""
    return JudgeResult(
        score_raw=0,
        normalized=0.0,
        reason="No judge available",
        judge_model="none",
        judge_provider_id="none",
    )
