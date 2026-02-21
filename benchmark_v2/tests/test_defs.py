"""
Definicoes de dados para testes do benchmark v2.
Registry pattern para auto-registro de categorias.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# Registry global de testes
_TEST_REGISTRY: Dict[str, "TestDef"] = {}


@dataclass
class StructuralCheck:
    """Check estrutural deterministico para avaliacao Layer 1."""
    check_id: str
    description: str
    check_type: str  # regex_present|regex_absent|min_lines|min_items|
                     # numeric_in_range|multi_round_consistency|word_count_range
    pattern: str = ""
    threshold: float = 0.0
    threshold_max: float = 0.0  # Para word_count_range: max palavras
    weight: float = 1.0
    target_round: int = -1  # -1=todas, 0=primeira, 1=segunda, etc.


@dataclass
class TestDef:
    """Definicao completa de um teste do benchmark."""
    test_id: str
    name: str
    category: str
    difficulty: str  # easy|medium|hard
    language: str    # pt|en|mixed
    prompts: List[str] = field(default_factory=list)
    structural_checks: List[StructuralCheck] = field(default_factory=list)
    ground_truth: Optional[str] = None
    reference_keywords: List[str] = field(default_factory=list)
    reference_anti_keywords: List[str] = field(default_factory=list)
    reference_numeric_ranges: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    judge_rubric: str = ""
    anti_hallucination: bool = False
    domain: str = "general"
    tags: List[str] = field(default_factory=list)


def register_test(test: TestDef) -> None:
    """Registra teste no registry global."""
    if test.test_id in _TEST_REGISTRY:
        raise ValueError(f"Teste duplicado: {test.test_id}")
    _TEST_REGISTRY[test.test_id] = test


def register_tests(tests: List[TestDef]) -> None:
    """Registra lista de testes."""
    for t in tests:
        register_test(t)


def get_test(test_id: str) -> TestDef:
    """Retorna teste por ID."""
    return _TEST_REGISTRY[test_id]


def get_all_tests() -> Dict[str, TestDef]:
    """Retorna todos os testes registrados."""
    return dict(_TEST_REGISTRY)


def get_tests_by_category(category: str) -> List[TestDef]:
    """Retorna testes filtrados por categoria."""
    return [t for t in _TEST_REGISTRY.values() if t.category == category]


def get_categories() -> List[str]:
    """Retorna lista de categorias unicas."""
    return sorted(set(t.category for t in _TEST_REGISTRY.values()))


# Rubrica padrao para judge (4 niveis, 0-3)
DEFAULT_RUBRIC = """Score the response on a 0-3 scale:

0 = FAIL: Response is incorrect, fabricated, or completely misses the task requirements.
1 = POOR: Response partially addresses the task but has significant errors or omissions.
2 = GOOD: Response is mostly correct with minor issues. Meets most requirements.
3 = EXCELLENT: Response is accurate, well-structured, and fully meets all requirements.

{specific_criteria}

IMPORTANT: Output EXACTLY in this format:
SCORE: N
REASON: Your explanation here (1-2 sentences)"""
