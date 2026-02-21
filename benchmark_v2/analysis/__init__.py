"""
Modulo de analise estatistica, graficos e relatorio.
"""

from .statistics import (
    mean_and_std,
    confidence_interval_95,
    cohens_kappa,
    pearson_correlation,
    stability_score,
)
from .graphs import generate_all_graphs
from .report import generate_report

__all__ = [
    "mean_and_std",
    "confidence_interval_95",
    "cohens_kappa",
    "pearson_correlation",
    "stability_score",
    "generate_all_graphs",
    "generate_report",
]
