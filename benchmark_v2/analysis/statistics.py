"""
Funcoes estatisticas para o benchmark v2.
CI 95%, Cohen's kappa, Pearson, stability score.
"""

import math
from typing import Dict, List, Tuple

# Tabela t de Student para IC 95% (two-tailed, alpha=0.05)
# df -> t_critical
T_TABLE = {
    1: 12.706,
    2: 4.303,
    3: 3.182,
    4: 2.776,
    5: 2.571,
    6: 2.447,
    7: 2.365,
    8: 2.306,
    9: 2.262,
    10: 2.228,
    15: 2.131,
    20: 2.086,
    25: 2.060,
    30: 2.042,
    50: 2.009,
    100: 1.984,
}

# Fallback para n grande
Z_95 = 1.96


def mean_and_std(values: List[float]) -> Tuple[float, float]:
    """Calcula media e desvio padrao amostral."""
    if not values:
        return 0.0, 0.0

    n = len(values)
    mean = sum(values) / n

    if n < 2:
        return mean, 0.0

    variance = sum((x - mean) ** 2 for x in values) / (n - 1)
    std = math.sqrt(variance)

    return round(mean, 4), round(std, 4)


def confidence_interval_95(values: List[float]) -> Tuple[float, float, float]:
    """
    Calcula intervalo de confianca 95% usando t de Student.
    Retorna (mean, ci_lower, ci_upper).
    """
    if not values:
        return 0.0, 0.0, 0.0

    n = len(values)
    mean, std = mean_and_std(values)

    if n < 2 or std == 0:
        return mean, mean, mean

    # Busca t_critical na tabela
    df = n - 1
    t_crit = _get_t_critical(df)

    margin = t_crit * (std / math.sqrt(n))

    return (
        round(mean, 4),
        round(mean - margin, 4),
        round(mean + margin, 4),
    )


def _get_t_critical(df: int) -> float:
    """Busca valor t critico para df graus de liberdade."""
    if df in T_TABLE:
        return T_TABLE[df]

    # Interpolacao para valores intermediarios
    keys = sorted(T_TABLE.keys())
    for i in range(len(keys) - 1):
        if keys[i] <= df < keys[i + 1]:
            # Interpolacao linear
            t1, t2 = T_TABLE[keys[i]], T_TABLE[keys[i + 1]]
            frac = (df - keys[i]) / (keys[i + 1] - keys[i])
            return t1 + frac * (t2 - t1)

    # df muito grande, usa z
    return Z_95


def cohens_kappa(
    ratings_a: List[int],
    ratings_b: List[int],
    num_categories: int = 4,
) -> float:
    """
    Calcula Cohen's kappa entre dois juizes.
    ratings_a, ratings_b: listas de scores (0-3).
    """
    if len(ratings_a) != len(ratings_b) or not ratings_a:
        return 0.0

    n = len(ratings_a)

    # Matriz de confusao
    matrix = [[0] * num_categories for _ in range(num_categories)]
    for a, b in zip(ratings_a, ratings_b):
        a_idx = max(0, min(a, num_categories - 1))
        b_idx = max(0, min(b, num_categories - 1))
        matrix[a_idx][b_idx] += 1

    # Concordancia observada
    p_observed = sum(matrix[i][i] for i in range(num_categories)) / n

    # Concordancia esperada por acaso
    p_expected = 0.0
    for i in range(num_categories):
        row_sum = sum(matrix[i])
        col_sum = sum(matrix[j][i] for j in range(num_categories))
        p_expected += (row_sum * col_sum) / (n * n)

    # Kappa
    if p_expected == 1.0:
        return 1.0 if p_observed == 1.0 else 0.0

    kappa = (p_observed - p_expected) / (1.0 - p_expected)
    return round(kappa, 4)


def pearson_correlation(x: List[float], y: List[float]) -> float:
    """Calcula correlacao de Pearson entre duas listas."""
    if len(x) != len(y) or len(x) < 2:
        return 0.0

    n = len(x)
    mean_x = sum(x) / n
    mean_y = sum(y) / n

    cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    std_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
    std_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))

    if std_x == 0 or std_y == 0:
        return 0.0

    return round(cov / (std_x * std_y), 4)


def stability_score(values: List[float]) -> Tuple[float, bool]:
    """
    Calcula score de estabilidade: 1 - (std/mean).
    Sinaliza instavel se std > 0.3.
    Retorna (stability, is_unstable).
    """
    mean, std = mean_and_std(values)

    if mean == 0:
        return 0.0, True

    stability = 1.0 - (std / abs(mean))
    stability = max(0.0, min(1.0, stability))
    is_unstable = std > 0.3

    return round(stability, 4), is_unstable


def compute_model_statistics(
    all_scores: Dict[str, Dict[str, List[float]]],
) -> Dict[str, Dict]:
    """
    Computa estatisticas completas por modelo.

    all_scores: {model_id: {test_id: [score_seed1, score_seed2, ...]}}

    Retorna: {model_id: {
        overall_mean, overall_ci, by_category, by_test,
        unstable_tests, unstable_pct
    }}
    """
    results = {}

    for model_id, test_scores in all_scores.items():
        # Flatten all scores for overall
        all_vals = []
        by_test = {}

        for test_id, scores in test_scores.items():
            mean, ci_lo, ci_hi = confidence_interval_95(scores)
            stab, unstable = stability_score(scores)
            by_test[test_id] = {
                "mean": mean,
                "std": mean_and_std(scores)[1],
                "ci_lower": ci_lo,
                "ci_upper": ci_hi,
                "stability": stab,
                "unstable": unstable,
                "n_seeds": len(scores),
            }
            all_vals.extend(scores)

        overall_mean, overall_lo, overall_hi = confidence_interval_95(all_vals)
        overall_std = mean_and_std(all_vals)[1]

        unstable_tests = [tid for tid, info in by_test.items() if info["unstable"]]
        unstable_pct = len(unstable_tests) / len(by_test) * 100 if by_test else 0

        results[model_id] = {
            "overall_mean": overall_mean,
            "overall_std": overall_std,
            "overall_ci_lower": overall_lo,
            "overall_ci_upper": overall_hi,
            "by_test": by_test,
            "unstable_tests": unstable_tests,
            "unstable_pct": round(unstable_pct, 1),
        }

    return results


def compute_category_statistics(
    all_scores: Dict[str, Dict[str, List[float]]],
    test_categories: Dict[str, str],
) -> Dict[str, Dict[str, Dict]]:
    """
    Computa estatisticas por modelo por categoria.

    test_categories: {test_id: category_name}
    Retorna: {model_id: {category: {mean, std, ci_lower, ci_upper}}}
    """
    results = {}

    for model_id, test_scores in all_scores.items():
        by_cat: Dict[str, List[float]] = {}
        for test_id, scores in test_scores.items():
            cat = test_categories.get(test_id, "unknown")
            if cat not in by_cat:
                by_cat[cat] = []
            by_cat[cat].extend(scores)

        cat_stats = {}
        for cat, vals in by_cat.items():
            mean, ci_lo, ci_hi = confidence_interval_95(vals)
            cat_stats[cat] = {
                "mean": mean,
                "std": mean_and_std(vals)[1],
                "ci_lower": ci_lo,
                "ci_upper": ci_hi,
            }

        results[model_id] = cat_stats

    return results
