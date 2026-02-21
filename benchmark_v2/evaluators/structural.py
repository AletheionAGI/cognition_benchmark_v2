"""
Camada 1 de avaliacao: checks estruturais deterministicos.
Sem LLM, baseado em regex, contagem de linhas/itens, ranges numericos.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..tests.test_defs import StructuralCheck

logger = logging.getLogger(__name__)


@dataclass
class CheckResult:
    """Resultado de um check individual."""
    check_id: str
    description: str
    passed: bool
    score: float  # 0.0, 0.5, 1.0
    detail: str = ""


@dataclass
class StructuralScore:
    """Score agregado da camada estrutural."""
    normalized: float  # 0.0 - 1.0
    details: List[CheckResult] = field(default_factory=list)
    total_weight: float = 0.0
    weighted_score: float = 0.0


def evaluate_structural(
    checks: List[StructuralCheck],
    rounds: List[Dict[str, str]],
) -> StructuralScore:
    """
    Avalia checks estruturais contra as respostas.
    rounds: lista de dicts com role/content de toda a conversa.
    """
    if not checks:
        return StructuralScore(normalized=1.0)

    # Extrai textos das respostas do assistente
    assistant_texts = _extract_assistant_texts(rounds)
    all_text = "\n".join(assistant_texts)

    results: List[CheckResult] = []
    total_weight = 0.0
    weighted_score = 0.0

    for check in checks:
        result = _evaluate_single_check(check, assistant_texts, all_text)
        results.append(result)

        total_weight += check.weight
        weighted_score += result.score * check.weight

    normalized = weighted_score / total_weight if total_weight > 0 else 0.0
    normalized = max(0.0, min(1.0, normalized))

    return StructuralScore(
        normalized=normalized,
        details=results,
        total_weight=total_weight,
        weighted_score=weighted_score,
    )


def _extract_assistant_texts(rounds: List[Dict[str, str]]) -> List[str]:
    """Extrai textos das respostas do assistente."""
    texts = []
    for msg in rounds:
        if msg.get("role") == "assistant":
            content = msg.get("content", "")
            texts.append(content)
    return texts


def _get_target_text(
    check: StructuralCheck,
    assistant_texts: List[str],
    all_text: str,
) -> str:
    """Retorna texto alvo baseado no target_round."""
    if check.target_round == -1:
        return all_text
    idx = check.target_round
    if 0 <= idx < len(assistant_texts):
        return assistant_texts[idx]
    return all_text


def _evaluate_single_check(
    check: StructuralCheck,
    assistant_texts: List[str],
    all_text: str,
) -> CheckResult:
    """Avalia um check individual."""
    target = _get_target_text(check, assistant_texts, all_text)

    evaluators = {
        "regex_present": _check_regex_present,
        "regex_absent": _check_regex_absent,
        "min_lines": _check_min_lines,
        "min_items": _check_min_items,
        "numeric_in_range": _check_numeric_in_range,
        "multi_round_consistency": _check_multi_round_consistency,
        "word_count_range": _check_word_count_range,
    }

    evaluator = evaluators.get(check.check_type)
    if not evaluator:
        logger.warning("[WARN] Tipo de check desconhecido: %s", check.check_type)
        return CheckResult(
            check_id=check.check_id,
            description=check.description,
            passed=False,
            score=0.0,
            detail=f"Tipo desconhecido: {check.check_type}",
        )

    # multi_round_consistency usa assistant_texts inteiro
    if check.check_type == "multi_round_consistency":
        return evaluator(check, assistant_texts)

    return evaluator(check, target)


# --- Implementacoes dos checks ---


def _check_regex_present(check: StructuralCheck, text: str) -> CheckResult:
    """Verifica se pattern esta presente no texto."""
    try:
        found = bool(re.search(check.pattern, text, re.IGNORECASE | re.DOTALL))
    except re.error as e:
        return CheckResult(
            check_id=check.check_id,
            description=check.description,
            passed=False, score=0.0,
            detail=f"Regex invalido: {e}",
        )

    return CheckResult(
        check_id=check.check_id,
        description=check.description,
        passed=found,
        score=1.0 if found else 0.0,
        detail=f"Pattern {'encontrado' if found else 'nao encontrado'}: {check.pattern[:60]}",
    )


def _check_regex_absent(check: StructuralCheck, text: str) -> CheckResult:
    """Verifica se pattern NAO esta presente no texto."""
    try:
        found = bool(re.search(check.pattern, text, re.IGNORECASE | re.DOTALL))
    except re.error as e:
        return CheckResult(
            check_id=check.check_id,
            description=check.description,
            passed=False, score=0.0,
            detail=f"Regex invalido: {e}",
        )

    return CheckResult(
        check_id=check.check_id,
        description=check.description,
        passed=not found,
        score=1.0 if not found else 0.0,
        detail=f"Pattern {'ausente (bom)' if not found else 'presente (ruim)'}: {check.pattern[:60]}",
    )


def _check_min_lines(check: StructuralCheck, text: str) -> CheckResult:
    """Verifica se texto tem minimo de linhas."""
    lines = [l for l in text.strip().split("\n") if l.strip()]
    count = len(lines)
    required = int(check.threshold)

    if count >= required:
        score = 1.0
    elif count >= required * 0.6:
        score = 0.5  # Parcial
    else:
        score = 0.0

    return CheckResult(
        check_id=check.check_id,
        description=check.description,
        passed=count >= required,
        score=score,
        detail=f"{count} linhas (minimo: {required})",
    )


def _check_min_items(check: StructuralCheck, text: str) -> CheckResult:
    """Verifica se texto tem minimo de itens de lista."""
    # Detecta bullets: -, *, numeros, letras seguidas de ponto/parentese
    item_patterns = [
        r"^\s*[-*]\s+",          # - item ou * item
        r"^\s*\d+[.)]\s+",      # 1. item ou 1) item
        r"^\s*[a-zA-Z][.)]\s+", # a. item ou a) item
        r"^\|.*\|",              # | table row |
    ]
    combined = "|".join(item_patterns)

    lines = text.strip().split("\n")
    items = sum(1 for l in lines if re.match(combined, l))

    required = int(check.threshold)

    if items >= required:
        score = 1.0
    elif items >= required * 0.6:
        score = 0.5
    else:
        score = 0.0

    return CheckResult(
        check_id=check.check_id,
        description=check.description,
        passed=items >= required,
        score=score,
        detail=f"{items} itens de lista (minimo: {required})",
    )


def _check_numeric_in_range(check: StructuralCheck, text: str) -> CheckResult:
    """Verifica se numeros no texto estao dentro do range."""
    # Extrai numeros do texto (inteiros e decimais)
    numbers = re.findall(r"[\d]+(?:[.,]\d+)?", text)
    parsed = []
    for n in numbers:
        try:
            cleaned = n.replace(",", ".")
            parsed.append(float(cleaned))
        except ValueError:
            continue

    low = check.threshold
    high = check.threshold_max if check.threshold_max > 0 else check.threshold * 1.1

    # Verifica se algum numero esta no range
    found_in_range = any(low <= n <= high for n in parsed)

    return CheckResult(
        check_id=check.check_id,
        description=check.description,
        passed=found_in_range,
        score=1.0 if found_in_range else 0.0,
        detail=f"Range [{low:.2f}, {high:.2f}], numeros encontrados: {len(parsed)}",
    )


def _check_multi_round_consistency(
    check: StructuralCheck,
    assistant_texts: List[str],
) -> CheckResult:
    """Verifica consistencia entre rounds (keywords compartilhados)."""
    if len(assistant_texts) < 2:
        return CheckResult(
            check_id=check.check_id,
            description=check.description,
            passed=True,
            score=1.0,
            detail="Apenas 1 round, consistencia nao aplicavel",
        )

    # Extrai palavras significativas (>3 chars) de cada round
    word_sets = []
    for text in assistant_texts:
        words = set(
            w.lower()
            for w in re.findall(r"\b\w+\b", text)
            if len(w) > 3
        )
        word_sets.append(words)

    # Calcula Jaccard medio entre rounds consecutivos
    similarities = []
    for i in range(len(word_sets) - 1):
        intersection = word_sets[i] & word_sets[i + 1]
        union = word_sets[i] | word_sets[i + 1]
        if union:
            similarities.append(len(intersection) / len(union))
        else:
            similarities.append(0.0)

    avg_sim = sum(similarities) / len(similarities) if similarities else 0.0

    # Threshold de consistencia
    threshold = check.threshold if check.threshold > 0 else 0.15

    if avg_sim >= threshold:
        score = 1.0
    elif avg_sim >= threshold * 0.5:
        score = 0.5
    else:
        score = 0.0

    return CheckResult(
        check_id=check.check_id,
        description=check.description,
        passed=avg_sim >= threshold,
        score=score,
        detail=f"Jaccard medio: {avg_sim:.3f} (threshold: {threshold:.3f})",
    )


def _check_word_count_range(check: StructuralCheck, text: str) -> CheckResult:
    """Verifica se contagem de palavras esta no range."""
    words = text.split()
    count = len(words)
    min_words = int(check.threshold)
    max_words = int(check.threshold_max) if check.threshold_max > 0 else 9999

    in_range = min_words <= count <= max_words

    if in_range:
        score = 1.0
    elif count < min_words and count >= min_words * 0.6:
        score = 0.5
    elif count > max_words and count <= max_words * 1.4:
        score = 0.5
    else:
        score = 0.0

    return CheckResult(
        check_id=check.check_id,
        description=check.description,
        passed=in_range,
        score=score,
        detail=f"{count} palavras (range: {min_words}-{max_words})",
    )
