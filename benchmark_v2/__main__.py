"""
AGI Grounding Benchmark v2.0
CLI principal + main loop.

Uso:
  python -m benchmark_v2                              # completo (3 seeds)
  python -m benchmark_v2 --fast                       # 1 seed, sem tiebreak
  python -m benchmark_v2 --models claude gpt          # so esses providers
  python -m benchmark_v2 --categories "self-correction" "factual-grounding"
  python -m benchmark_v2 --seeds 5                    # mais seeds
  python -m benchmark_v2 --no-graphs                  # pula graficos
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Garante que o diretorio pai (atic_consulting) esta no path
# para que imports do ATIC e do benchmark_v2 funcionem
_BENCHMARK_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT_DIR = os.path.dirname(_BENCHMARK_DIR)
if _PARENT_DIR not in sys.path:
    sys.path.insert(0, _PARENT_DIR)

# Carrega .env do diretorio pai (atic_consulting/.env)
_ENV_FILE = os.path.join(_PARENT_DIR, ".env")
if os.path.exists(_ENV_FILE):
    with open(_ENV_FILE, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _, _val = _line.partition("=")
                _key = _key.strip()
                _val = _val.strip().strip('"').strip("'")
                if _key and _key not in os.environ:
                    os.environ[_key] = _val

from benchmark_v2.providers import detect_and_create_providers, BaseProvider
from benchmark_v2.tests import get_all_tests, get_categories, TestDef
from benchmark_v2.evaluators import (
    evaluate_structural, evaluate_reference, evaluate_judge,
)
from benchmark_v2.analysis.statistics import (
    compute_model_statistics, compute_category_statistics,
)
from benchmark_v2.analysis.graphs import generate_all_graphs
from benchmark_v2.analysis.report import generate_report

logger = logging.getLogger("benchmark_v2")

# Defaults
DEFAULT_SEEDS = 3
DEFAULT_OUTPUT_DIR = os.path.join(_BENCHMARK_DIR, "results")


def parse_args():
    """Parse argumentos CLI."""
    parser = argparse.ArgumentParser(
        description="AGI Grounding Benchmark v2.0"
    )
    parser.add_argument(
        "--fast", action="store_true",
        help="Modo rapido: 1 seed, sem tiebreak, pula graficos 4/5"
    )
    parser.add_argument(
        "--seeds", type=int, default=DEFAULT_SEEDS,
        help=f"Numero de seeds (default: {DEFAULT_SEEDS})"
    )
    parser.add_argument(
        "--models", nargs="+", default=None,
        help="Lista de providers (claude gpt gemini atic_on atic_off)"
    )
    parser.add_argument(
        "--categories", nargs="+", default=None,
        help="Filtrar categorias"
    )
    parser.add_argument(
        "--no-graphs", action="store_true",
        help="Pular geracao de graficos"
    )
    parser.add_argument(
        "--output-dir", default=DEFAULT_OUTPUT_DIR,
        help="Diretorio de saida"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Log detalhado"
    )
    return parser.parse_args()


def setup_logging(verbose: bool = False):
    """Configura logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def filter_tests(
    all_tests: Dict[str, TestDef],
    categories: Optional[List[str]] = None,
) -> Dict[str, TestDef]:
    """Filtra testes por categoria se especificado."""
    if not categories:
        return all_tests

    categories_lower = [c.lower() for c in categories]
    return {
        tid: t for tid, t in all_tests.items()
        if t.category.lower() in categories_lower
    }


def estimate_runtime(
    n_tests: int, n_providers: int, n_seeds: int, enable_tiebreak: bool
) -> str:
    """Estima tempo de execucao."""
    # ~10s por query, ~2 prompts/teste em media, + 5s judge
    calls_per_test = 2  # media de prompts
    judge_time = 5
    base = n_tests * n_providers * n_seeds * (calls_per_test * 10 + judge_time)
    if enable_tiebreak:
        base *= 1.2  # 20% extra para tiebreaks
    minutes = base / 60
    return f"~{minutes:.0f} min"


def run_single_evaluation(
    test: TestDef,
    provider: BaseProvider,
    available_providers: Dict[str, BaseProvider],
    enable_tiebreak: bool = True,
) -> Dict:
    """
    Executa um teste com um provider e retorna resultado completo.
    """
    result = {
        "test_id": test.test_id,
        "model": provider.provider_id,
        "timestamp": datetime.now().isoformat(),
    }

    # --- Execucao ---
    start = time.perf_counter()
    if len(test.prompts) > 1:
        rounds = provider.query_multi_round(test.prompts)
    else:
        response = provider.query(test.prompts[0])
        rounds = [
            {"role": "user", "content": test.prompts[0]},
            {
                "role": "assistant",
                "content": response.text,
                "elapsed": response.elapsed_seconds,
                "model": response.model,
                "error": response.error,
            },
        ]
    exec_time = time.perf_counter() - start

    result["rounds"] = rounds
    result["exec_seconds"] = round(exec_time, 2)

    # Verifica erro
    has_error = any(
        msg.get("error") for msg in rounds if msg.get("role") == "assistant"
    )
    if has_error:
        result["error"] = True
        result["structural_score"] = 0.0
        result["reference_score"] = 0.0
        result["judge_score"] = 0.0
        result["final_score"] = 0.0
        return result

    # --- Layer 1: Structural ---
    structural = evaluate_structural(test.structural_checks, rounds)
    result["structural_score"] = structural.normalized
    result["structural_details"] = [
        {"id": d.check_id, "passed": d.passed, "score": d.score, "detail": d.detail}
        for d in structural.details
    ]

    # --- Layer 2: Reference ---
    reference = evaluate_reference(test, rounds)
    result["reference_score"] = reference.normalized
    result["reference_sub_scores"] = reference.sub_scores
    result["hallucination_flags"] = reference.hallucination_flags

    # --- Layer 3: Judge ---
    judge_result, judge_audit = evaluate_judge(
        test_name=test.name,
        category=test.category,
        prompts=test.prompts,
        rounds=rounds,
        rubric=test.judge_rubric,
        evaluated_provider_id=provider.provider_id,
        available_providers=available_providers,
        structural_normalized=structural.normalized,
        reference_normalized=reference.normalized,
        enable_tiebreak=enable_tiebreak,
    )
    result["judge_score"] = judge_result.normalized
    result["judge_raw"] = judge_result.score_raw
    result["judge_reason"] = judge_result.reason
    result["judge_provider"] = judge_result.judge_provider_id
    result["tiebreak_used"] = judge_result.tiebreak_used
    result["judge_audit"] = {
        "primary_judge": judge_audit.primary_judge,
        "primary_score": judge_audit.primary_score,
        "tiebreak_judge": judge_audit.tiebreak_judge,
        "tiebreak_score": judge_audit.tiebreak_score,
        "final_source": judge_audit.final_source,
    }

    # --- Score Final ---
    final = (
        structural.normalized * 1
        + reference.normalized * 1
        + judge_result.normalized * 2
    ) / 4.0
    result["final_score"] = round(final, 4)

    return result


def main():
    """Loop principal do benchmark."""
    args = parse_args()
    setup_logging(args.verbose)

    if args.fast:
        args.seeds = 1
        logger.info("[FAST] Modo rapido: 1 seed, sem tiebreak")

    enable_tiebreak = not args.fast

    # --- 1. Detectar providers ---
    logger.info("[START] Detectando providers...")
    providers = detect_and_create_providers(requested=args.models)
    if not providers:
        logger.error("[ERROR] Nenhum provider disponivel!")
        sys.exit(1)
    logger.info(
        "[OK] %d providers: %s",
        len(providers), ", ".join(providers.keys())
    )

    # --- 2. Carregar testes ---
    all_tests = get_all_tests()
    tests = filter_tests(all_tests, args.categories)
    logger.info("[OK] %d testes carregados", len(tests))

    if not tests:
        logger.error("[ERROR] Nenhum teste encontrado!")
        sys.exit(1)

    # --- 3. Estimar runtime ---
    est = estimate_runtime(
        len(tests), len(providers), args.seeds, enable_tiebreak
    )
    logger.info("[INFO] Estimativa: %s", est)

    # --- 4. Main loop ---
    all_evaluations: List[Dict] = []
    # {model_id: {test_id: [final_scores per seed]}}
    score_matrix: Dict[str, Dict[str, List[float]]] = {}
    # Judge pairs para agreement: {"judge_a_vs_judge_b": [(score_a, score_b)]}
    judge_pairs: Dict[str, List[Tuple[int, int]]] = {}

    total_runs = len(tests) * len(providers) * args.seeds
    run_count = 0

    for seed in range(args.seeds):
        logger.info("--- Seed %d/%d ---", seed + 1, args.seeds)

        for test_id, test in tests.items():
            for provider_id, provider in providers.items():
                run_count += 1
                logger.info(
                    "[%d/%d] %s | %s (seed %d)",
                    run_count, total_runs, test_id, provider_id, seed + 1
                )

                result = run_single_evaluation(
                    test=test,
                    provider=provider,
                    available_providers=providers,
                    enable_tiebreak=enable_tiebreak,
                )
                result["seed"] = seed

                all_evaluations.append(result)

                # Acumula scores
                if provider_id not in score_matrix:
                    score_matrix[provider_id] = {}
                if test_id not in score_matrix[provider_id]:
                    score_matrix[provider_id][test_id] = []
                score_matrix[provider_id][test_id].append(result["final_score"])

                # Acumula judge pairs
                judge_id = result.get("judge_provider", "")
                if judge_id and judge_id != provider_id:
                    pair_key = f"{provider_id}_vs_{judge_id}"
                    if pair_key not in judge_pairs:
                        judge_pairs[pair_key] = []
                    judge_pairs[pair_key].append(
                        (result.get("judge_raw", 0), result.get("judge_raw", 0))
                    )

    # --- 5. Estatisticas ---
    logger.info("[STATS] Computando estatisticas...")
    model_stats = compute_model_statistics(score_matrix)

    test_categories = {tid: t.category for tid, t in tests.items()}
    category_stats = compute_category_statistics(score_matrix, test_categories)

    # --- 6. Preparar audit data ---
    tests_with_gt = sum(1 for t in tests.values() if t.ground_truth)
    self_evals = sum(
        1 for ev in all_evaluations
        if ev.get("judge_provider", "") == ev.get("model", "")
    )

    audit_data = {
        "timestamp": datetime.now().isoformat(),
        "seeds": args.seeds,
        "total_tests": len(tests),
        "total_providers": len(providers),
        "total_evaluations": len(all_evaluations),
        "tests_with_ground_truth": tests_with_gt,
        "self_evaluations": self_evals,
        "evaluations": all_evaluations,
        "judge_pairs": {k: v for k, v in judge_pairs.items()},
    }

    # --- 7. Salvar results ---
    os.makedirs(args.output_dir, exist_ok=True)

    results_path = os.path.join(args.output_dir, "results_v2.json")
    _save_json(results_path, {
        "timestamp": datetime.now().isoformat(),
        "model_stats": model_stats,
        "category_stats": category_stats,
        "score_matrix": score_matrix,
    })
    logger.info("[OK] Resultados salvos: %s", results_path)

    audit_path = os.path.join(args.output_dir, "benchmark_audit.json")
    _save_json(audit_path, audit_data)
    logger.info("[OK] Audit salvo: %s", audit_path)

    # --- 8. Relatorio ---
    report_path = os.path.join(args.output_dir, "report_v2.md")
    generate_report(model_stats, category_stats, audit_data, report_path)

    # --- 9. Graficos ---
    if not args.no_graphs:
        graphs_dir = os.path.join(args.output_dir, "graphs")
        saved_graphs = generate_all_graphs(
            model_stats, category_stats, judge_pairs,
            output_dir=graphs_dir, fast_mode=args.fast,
        )
        logger.info("[OK] %d graficos gerados", len(saved_graphs))

    # --- 10. Resumo final ---
    _print_summary(model_stats, category_stats, audit_data)


def _save_json(path: str, data: Dict):
    """Salva dados em JSON."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def _print_summary(
    model_stats: Dict, category_stats: Dict, audit_data: Dict
):
    """Imprime resumo final no terminal."""
    print("\n" + "=" * 60)
    print("  AGI GROUNDING BENCHMARK v2.0 - RESULTS")
    print("=" * 60)

    # Ranking
    sorted_models = sorted(
        model_stats.keys(),
        key=lambda m: model_stats[m].get("overall_mean", 0),
        reverse=True,
    )

    labels = {
        "atic_on": "ATIC (ON)",
        "atic_off": "ATIC (OFF)",
        "claude": "Claude",
        "gpt": "GPT-4o",
        "gemini": "Gemini",
    }

    print("\n  RANKING:")
    for rank, model in enumerate(sorted_models, 1):
        stats = model_stats[model]
        mean = stats["overall_mean"]
        ci_lo = stats["overall_ci_lower"]
        ci_hi = stats["overall_ci_upper"]
        label = labels.get(model, model)
        print(f"  {rank}. {label:15s}  {mean:.3f}  [{ci_lo:.3f}, {ci_hi:.3f}]")

    # Qualidade
    self_evals = audit_data.get("self_evaluations", 0)
    print(f"\n  Self-evaluations: {self_evals}")
    print(f"  Total evaluations: {audit_data.get('total_evaluations', 0)}")
    print(f"  Tests with ground_truth: {audit_data.get('tests_with_ground_truth', 0)}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
