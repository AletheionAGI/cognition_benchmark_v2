"""
Geracao de graficos para o benchmark v2.
5 graficos com dark theme.
"""

import os
import math
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Cores por modelo
MODEL_COLORS = {
    "atic_on": "#00e676",
    "atic_off": "#ff5252",
    "claude": "#42a5f5",
    "gpt": "#ffa726",
    "gemini": "#ab47bc",
}

MODEL_LABELS = {
    "atic_on": "ATIC (ON)",
    "atic_off": "ATIC (OFF)",
    "claude": "Claude",
    "gpt": "GPT-4o",
    "gemini": "Gemini",
}

# Dark theme
DARK_BG = "#1e1e1e"
DARK_FG = "#e0e0e0"
DARK_GRID = "#333333"
DPI = 150


def generate_all_graphs(
    model_stats: Dict[str, Dict],
    category_stats: Dict[str, Dict[str, Dict]],
    judge_pairs: Optional[Dict[str, List[Tuple[int, int]]]] = None,
    output_dir: str = "results/graphs",
    fast_mode: bool = False,
) -> List[str]:
    """
    Gera todos os graficos e retorna lista de paths salvos.
    fast_mode: pula graficos 4 e 5.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        logger.error("[ERROR] matplotlib nao disponivel")
        return []

    os.makedirs(output_dir, exist_ok=True)
    saved = []

    # Filtra modelos com dados
    models = [m for m in model_stats if model_stats[m].get("overall_mean", 0) > 0]
    if not models:
        logger.warning("[WARN] Nenhum modelo com dados para graficos")
        return []

    # 1. Ranking com IC 95%
    path = _graph_ranking_ci(plt, models, model_stats, output_dir)
    if path:
        saved.append(path)

    # 2. Heatmap categorias
    categories = sorted(set(
        cat for m in models
        for cat in category_stats.get(m, {})
    ))
    if categories:
        path = _graph_heatmap(plt, models, categories, category_stats, output_dir)
        if path:
            saved.append(path)

    # 3. Radar
    if categories:
        path = _graph_radar(plt, models, categories, category_stats, output_dir)
        if path:
            saved.append(path)

    if not fast_mode:
        # 4. Stability analysis
        path = _graph_stability(plt, models, model_stats, output_dir)
        if path:
            saved.append(path)

        # 5. Judge agreement
        if judge_pairs:
            path = _graph_judge_agreement(plt, judge_pairs, output_dir)
            if path:
                saved.append(path)

    return saved


def _setup_dark_theme(plt, fig, ax):
    """Aplica dark theme."""
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(DARK_BG)
    ax.tick_params(colors=DARK_FG)
    ax.xaxis.label.set_color(DARK_FG)
    ax.yaxis.label.set_color(DARK_FG)
    ax.title.set_color(DARK_FG)
    for spine in ax.spines.values():
        spine.set_color(DARK_GRID)
    ax.grid(True, color=DARK_GRID, alpha=0.3)


def _graph_ranking_ci(plt, models, model_stats, output_dir) -> Optional[str]:
    """01: Barras horizontais com error bars (IC 95%)."""
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        _setup_dark_theme(plt, fig, ax)

        # Ordena por score
        sorted_models = sorted(
            models, key=lambda m: model_stats[m]["overall_mean"], reverse=True
        )

        y_pos = range(len(sorted_models))
        means = [model_stats[m]["overall_mean"] for m in sorted_models]
        ci_lowers = [model_stats[m]["overall_ci_lower"] for m in sorted_models]
        ci_uppers = [model_stats[m]["overall_ci_upper"] for m in sorted_models]

        errors_low = [means[i] - ci_lowers[i] for i in range(len(means))]
        errors_high = [ci_uppers[i] - means[i] for i in range(len(means))]
        errors = [errors_low, errors_high]

        colors = [MODEL_COLORS.get(m, "#888888") for m in sorted_models]
        labels = [MODEL_LABELS.get(m, m) for m in sorted_models]

        bars = ax.barh(y_pos, means, xerr=errors, color=colors, height=0.6,
                       capsize=5, ecolor=DARK_FG, alpha=0.9)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels)
        ax.set_xlabel("Score (0-1)")
        ax.set_title("Benchmark v2 - Ranking with 95% CI")
        ax.set_xlim(0, 1.05)

        # Adiciona valores nas barras
        for i, (bar, mean) in enumerate(zip(bars, means)):
            ax.text(mean + 0.02, bar.get_y() + bar.get_height() / 2,
                    f"{mean:.3f}", va="center", color=DARK_FG, fontsize=9)

        plt.tight_layout()
        path = os.path.join(output_dir, "01_ranking_with_ci.png")
        fig.savefig(path, dpi=DPI, facecolor=DARK_BG)
        plt.close(fig)
        return path
    except Exception as e:
        logger.error("[ERROR] Grafico ranking: %s", e)
        return None


def _graph_heatmap(plt, models, categories, category_stats, output_dir) -> Optional[str]:
    """02: Heatmap modelos x categorias."""
    try:
        import numpy as np

        fig, ax = plt.subplots(figsize=(12, 6))
        _setup_dark_theme(plt, fig, ax)

        data = []
        for m in models:
            row = []
            for cat in categories:
                val = category_stats.get(m, {}).get(cat, {}).get("mean", 0.0)
                row.append(val)
            data.append(row)

        data_np = np.array(data)
        im = ax.imshow(data_np, cmap="RdYlGn", aspect="auto", vmin=0, vmax=1)

        ax.set_xticks(range(len(categories)))
        ax.set_xticklabels(categories, rotation=45, ha="right", fontsize=8)
        ax.set_yticks(range(len(models)))
        ax.set_yticklabels([MODEL_LABELS.get(m, m) for m in models])

        # Anota valores
        for i in range(len(models)):
            for j in range(len(categories)):
                val = data_np[i, j]
                color = "black" if val > 0.5 else "white"
                ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                        color=color, fontsize=9)

        cbar = fig.colorbar(im, ax=ax)
        cbar.ax.yaxis.set_tick_params(color=DARK_FG)
        cbar.outline.set_edgecolor(DARK_GRID)
        plt.setp(plt.getp(cbar.ax.axes, "yticklabels"), color=DARK_FG)

        ax.set_title("Score by Model x Category")
        plt.tight_layout()
        path = os.path.join(output_dir, "02_heatmap_categories.png")
        fig.savefig(path, dpi=DPI, facecolor=DARK_BG)
        plt.close(fig)
        return path
    except Exception as e:
        logger.error("[ERROR] Grafico heatmap: %s", e)
        return None


def _graph_radar(plt, models, categories, category_stats, output_dir) -> Optional[str]:
    """03: Radar chart com 6 eixos."""
    try:
        import numpy as np

        n_cats = len(categories)
        angles = [n / float(n_cats) * 2 * math.pi for n in range(n_cats)]
        angles += angles[:1]  # Fecha o poligono

        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        fig.patch.set_facecolor(DARK_BG)
        ax.set_facecolor(DARK_BG)
        ax.tick_params(colors=DARK_FG)
        ax.xaxis.label.set_color(DARK_FG)

        for m in models:
            values = []
            for cat in categories:
                val = category_stats.get(m, {}).get(cat, {}).get("mean", 0.0)
                values.append(val)
            values += values[:1]

            color = MODEL_COLORS.get(m, "#888888")
            label = MODEL_LABELS.get(m, m)
            ax.plot(angles, values, "o-", color=color, linewidth=2, label=label)
            ax.fill(angles, values, color=color, alpha=0.1)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=8, color=DARK_FG)
        ax.set_ylim(0, 1)
        ax.set_yticks([0.25, 0.5, 0.75, 1.0])
        ax.set_yticklabels(["0.25", "0.50", "0.75", "1.00"],
                           color=DARK_FG, fontsize=7)
        ax.grid(True, color=DARK_GRID, alpha=0.3)

        legend = ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
        legend.get_frame().set_facecolor(DARK_BG)
        legend.get_frame().set_edgecolor(DARK_GRID)
        for text in legend.get_texts():
            text.set_color(DARK_FG)

        ax.set_title("Radar - All Models", color=DARK_FG, pad=20)
        plt.tight_layout()
        path = os.path.join(output_dir, "03_radar_all_models.png")
        fig.savefig(path, dpi=DPI, facecolor=DARK_BG, bbox_inches="tight")
        plt.close(fig)
        return path
    except Exception as e:
        logger.error("[ERROR] Grafico radar: %s", e)
        return None


def _graph_stability(plt, models, model_stats, output_dir) -> Optional[str]:
    """04: Scatter score medio x desvio padrao por teste."""
    try:
        fig, ax = plt.subplots(figsize=(10, 7))
        _setup_dark_theme(plt, fig, ax)

        for m in models:
            by_test = model_stats[m].get("by_test", {})
            x_vals = [info["mean"] for info in by_test.values()]
            y_vals = [info["std"] for info in by_test.values()]
            color = MODEL_COLORS.get(m, "#888888")
            label = MODEL_LABELS.get(m, m)
            ax.scatter(x_vals, y_vals, c=color, label=label, alpha=0.7, s=50)

        # Linha de instabilidade (std=0.3)
        ax.axhline(y=0.3, color="#ff5252", linestyle="--", alpha=0.5,
                    label="Instability threshold (std=0.3)")

        ax.set_xlabel("Mean Score")
        ax.set_ylabel("Standard Deviation")
        ax.set_title("Stability Analysis - Score vs Variability")
        ax.set_xlim(-0.05, 1.05)
        ax.set_ylim(-0.02, 0.6)

        legend = ax.legend(loc="upper left")
        legend.get_frame().set_facecolor(DARK_BG)
        legend.get_frame().set_edgecolor(DARK_GRID)
        for text in legend.get_texts():
            text.set_color(DARK_FG)

        plt.tight_layout()
        path = os.path.join(output_dir, "04_stability_analysis.png")
        fig.savefig(path, dpi=DPI, facecolor=DARK_BG)
        plt.close(fig)
        return path
    except Exception as e:
        logger.error("[ERROR] Grafico stability: %s", e)
        return None


def _graph_judge_agreement(plt, judge_pairs, output_dir) -> Optional[str]:
    """05: Heatmap de concordancia entre pares de juizes."""
    try:
        import numpy as np
        from .statistics import cohens_kappa

        # judge_pairs: {f"{judge_a}_{judge_b}": [(score_a, score_b), ...]}
        # Extrai juizes unicos
        judges = set()
        for pair_key in judge_pairs:
            parts = pair_key.split("_vs_")
            if len(parts) == 2:
                judges.add(parts[0])
                judges.add(parts[1])
        judges = sorted(judges)

        if len(judges) < 2:
            return None

        n = len(judges)
        matrix = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

        for pair_key, pairs in judge_pairs.items():
            parts = pair_key.split("_vs_")
            if len(parts) != 2:
                continue
            j_a, j_b = parts
            if j_a in judges and j_b in judges:
                i = judges.index(j_a)
                j = judges.index(j_b)
                ratings_a = [p[0] for p in pairs]
                ratings_b = [p[1] for p in pairs]
                kappa = cohens_kappa(ratings_a, ratings_b)
                matrix[i][j] = kappa
                matrix[j][i] = kappa

        data_np = np.array(matrix)

        fig, ax = plt.subplots(figsize=(8, 6))
        _setup_dark_theme(plt, fig, ax)

        im = ax.imshow(data_np, cmap="RdYlGn", aspect="auto", vmin=-0.2, vmax=1.0)

        judge_labels = [MODEL_LABELS.get(j, j) for j in judges]
        ax.set_xticks(range(n))
        ax.set_xticklabels(judge_labels, rotation=45, ha="right")
        ax.set_yticks(range(n))
        ax.set_yticklabels(judge_labels)

        for i in range(n):
            for j in range(n):
                val = data_np[i, j]
                color = "black" if val > 0.5 else "white"
                ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                        color=color, fontsize=10)

        cbar = fig.colorbar(im, ax=ax)
        cbar.ax.yaxis.set_tick_params(color=DARK_FG)
        cbar.outline.set_edgecolor(DARK_GRID)
        plt.setp(plt.getp(cbar.ax.axes, "yticklabels"), color=DARK_FG)

        ax.set_title("Judge Agreement (Cohen's Kappa)")
        plt.tight_layout()
        path = os.path.join(output_dir, "05_judge_agreement.png")
        fig.savefig(path, dpi=DPI, facecolor=DARK_BG)
        plt.close(fig)
        return path
    except Exception as e:
        logger.error("[ERROR] Grafico judge agreement: %s", e)
        return None
