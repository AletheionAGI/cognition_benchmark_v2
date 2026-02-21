"""
Camada 2 de avaliacao: ground truth + anti-hallucination.
Compara resposta com keywords, ranges numericos e ground truth.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from ..tests.test_defs import TestDef

logger = logging.getLogger(__name__)

# Padroes suspeitos de citacoes fabricadas
FAKE_CITATION_PATTERNS = [
    # DOI com formato invalido
    r"doi:\s*10\.\d{4,}/[a-z]{2,}\.\d{4}\.\d{6,}",
    # URLs com dominios plausíveis mas possivelmente fabricados
    r"https?://(?:www\.)?(?:journal|research|science)\w+\.(?:com|org)/\w{8,}",
    # "Author et al. (YYYY)" sem contexto suficiente (isolado)
    r"(?<!\w)[A-Z][a-z]+\s+et\s+al\.\s*\(\d{4}\)(?!\s*[,;.]?\s*[\"'])",
    # Numeros de pagina fabricados com formato especifico demais
    r"pp?\.\s*\d{4,}-\d{4,}",
    # arXiv IDs com formato invalido (mais de 5 digitos apos ponto)
    r"arXiv:\d{4}\.\d{6,}",
]


@dataclass
class ReferenceScore:
    """Score agregado da camada de referencia."""
    normalized: float  # 0.0 - 1.0
    sub_scores: Dict[str, float] = field(default_factory=dict)
    hallucination_flags: List[str] = field(default_factory=list)


def evaluate_reference(
    test: TestDef,
    rounds: List[Dict[str, str]],
) -> ReferenceScore:
    """
    Avalia resposta contra ground truth, keywords e ranges.
    """
    # Extrai texto completo das respostas
    full_text = _extract_full_response(rounds)

    if not full_text.strip():
        return ReferenceScore(normalized=0.0)

    sub_scores: Dict[str, float] = {}
    active_scores = 0

    # 1. Keyword coverage
    if test.reference_keywords:
        kw_score = _keyword_coverage(full_text, test.reference_keywords)
        sub_scores["keyword_coverage"] = kw_score
        active_scores += 1

    # 2. Anti-keyword absence
    if test.reference_anti_keywords:
        anti_score = _anti_keyword_absence(full_text, test.reference_anti_keywords)
        sub_scores["anti_keyword_absence"] = anti_score
        active_scores += 1

    # 3. Numeric accuracy
    if test.reference_numeric_ranges:
        num_score = _numeric_accuracy(full_text, test.reference_numeric_ranges)
        sub_scores["numeric_accuracy"] = num_score
        active_scores += 1

    # 4. Text similarity com ground_truth
    if test.ground_truth:
        sim_score = _text_similarity(full_text, test.ground_truth)
        sub_scores["text_similarity"] = sim_score
        active_scores += 1

    # 5. Anti-hallucination
    hallucination_flags: List[str] = []
    if test.anti_hallucination:
        hal_score, flags = _anti_hallucination_check(full_text)
        sub_scores["anti_hallucination"] = hal_score
        hallucination_flags = flags
        active_scores += 1

    # Media dos sub-scores ativos
    if active_scores > 0:
        normalized = sum(sub_scores.values()) / active_scores
    else:
        normalized = 1.0  # Sem checks de referencia = pass

    normalized = max(0.0, min(1.0, normalized))

    return ReferenceScore(
        normalized=normalized,
        sub_scores=sub_scores,
        hallucination_flags=hallucination_flags,
    )


def _extract_full_response(rounds: List[Dict[str, str]]) -> str:
    """Extrai texto completo das respostas do assistente."""
    parts = []
    for msg in rounds:
        if msg.get("role") == "assistant":
            parts.append(msg.get("content", ""))
    return "\n".join(parts)


def _keyword_coverage(text: str, keywords: List[str]) -> float:
    """Calcula % de keywords presentes no texto."""
    if not keywords:
        return 1.0

    text_lower = text.lower()
    found = sum(1 for kw in keywords if kw.lower() in text_lower)
    return found / len(keywords)


def _anti_keyword_absence(text: str, anti_keywords: List[str]) -> float:
    """Penaliza presenca de anti-keywords. 1.0 = nenhum encontrado."""
    if not anti_keywords:
        return 1.0

    text_lower = text.lower()
    violations = 0
    for pattern in anti_keywords:
        try:
            if re.search(pattern, text_lower, re.IGNORECASE):
                violations += 1
        except re.error:
            # Trata como string literal
            if pattern.lower() in text_lower:
                violations += 1

    # Cada violacao reduz score proporcionalmente
    penalty = violations / len(anti_keywords)
    return max(0.0, 1.0 - penalty)


def _numeric_accuracy(
    text: str,
    ranges: Dict[str, Tuple[float, float]],
) -> float:
    """Verifica se numeros no texto satisfazem ranges esperados."""
    if not ranges:
        return 1.0

    # Extrai todos os numeros do texto
    numbers = _extract_numbers(text)

    satisfied = 0
    for range_name, (low, high) in ranges.items():
        # Verifica se algum numero no texto esta no range
        found = any(low <= n <= high for n in numbers)
        if found:
            satisfied += 1

    return satisfied / len(ranges) if ranges else 1.0


def _extract_numbers(text: str) -> List[float]:
    """Extrai numeros do texto, lidando com formatos variados."""
    numbers = []

    # Padroes: 149.6, 149,6, 3.2 billion, 37 trilhoes, etc.
    raw_matches = re.findall(
        r"(\d[\d.,]*\d|\d+)\s*(?:(bilh|trilh|milh|billion|trillion|million|thousand|mil))?",
        text,
        re.IGNORECASE,
    )

    multipliers = {
        "bilh": 1e9, "billion": 1e9,
        "trilh": 1e12, "trillion": 1e12,
        "milh": 1e6, "million": 1e6,
        "mil": 1e3, "thousand": 1e3,
    }

    for num_str, suffix in raw_matches:
        try:
            # Remove separadores de milhar e normaliza decimal
            cleaned = num_str.replace(" ", "")
            # Detecta formato: 1.000.000 vs 1,000,000 vs 1.5
            if "," in cleaned and "." in cleaned:
                # Formato misto: assume ultimo separador como decimal
                if cleaned.rindex(",") > cleaned.rindex("."):
                    cleaned = cleaned.replace(".", "").replace(",", ".")
                else:
                    cleaned = cleaned.replace(",", "")
            elif "," in cleaned:
                # Pode ser decimal (3,2) ou milhar (1,000)
                parts = cleaned.split(",")
                if len(parts[-1]) == 3 and len(parts) > 1:
                    cleaned = cleaned.replace(",", "")
                else:
                    cleaned = cleaned.replace(",", ".")
            # Ponto como milhar (1.000.000)
            elif "." in cleaned:
                parts = cleaned.split(".")
                if all(len(p) == 3 for p in parts[1:]) and len(parts) > 2:
                    cleaned = cleaned.replace(".", "")

            value = float(cleaned)

            # Aplica multiplicador
            suffix_lower = suffix.lower()[:4] if suffix else ""
            for key, mult in multipliers.items():
                if suffix_lower.startswith(key[:4]):
                    value *= mult
                    break

            numbers.append(value)
        except (ValueError, IndexError):
            continue

    return numbers


def _text_similarity(response: str, ground_truth: str) -> float:
    """Calcula similaridade Jaccard de trigrams."""
    resp_trigrams = _get_trigrams(response.lower())
    truth_trigrams = _get_trigrams(ground_truth.lower())

    if not resp_trigrams or not truth_trigrams:
        return 0.0

    intersection = resp_trigrams & truth_trigrams
    union = resp_trigrams | truth_trigrams

    return len(intersection) / len(union) if union else 0.0


def _get_trigrams(text: str) -> Set[str]:
    """Extrai trigrams (3-grams de caracteres) do texto."""
    words = re.findall(r"\w+", text)
    joined = " ".join(words)
    trigrams = set()
    for i in range(len(joined) - 2):
        trigrams.add(joined[i : i + 3])
    return trigrams


def _anti_hallucination_check(text: str) -> Tuple[float, List[str]]:
    """
    Verifica padroes suspeitos de alucinacao.
    Retorna (score, lista_de_flags).
    Score 1.0 = sem sinais de alucinacao.
    """
    flags: List[str] = []

    for pattern in FAKE_CITATION_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            flag_text = match if isinstance(match, str) else str(match)
            flags.append(f"Citacao suspeita: {flag_text[:80]}")

    # Penalidade proporcional ao numero de flags
    if not flags:
        return 1.0, []

    # Cada flag reduz 0.15 do score, minimo 0.0
    penalty = min(len(flags) * 0.15, 1.0)
    return max(0.0, 1.0 - penalty), flags
