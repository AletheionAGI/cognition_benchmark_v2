"""
Modulo de avaliacao: 3 camadas de scoring.
"""

from .structural import StructuralScore, CheckResult, evaluate_structural
from .reference import ReferenceScore, evaluate_reference
from .llm_judge import JudgeResult, JudgeAudit, evaluate_judge

__all__ = [
    "StructuralScore",
    "CheckResult",
    "evaluate_structural",
    "ReferenceScore",
    "evaluate_reference",
    "JudgeResult",
    "JudgeAudit",
    "evaluate_judge",
]
