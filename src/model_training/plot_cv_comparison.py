"""Create a dissertation-ready comparison of candidate-model CV performance."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[2]
METRICS_PATH = PROJECT_ROOT / "models" / "metrics.json"
OUTPUT_PATH = (
    PROJECT_ROOT
    / "visualizations"
    / "chart images"
    / "Figure_6_5_cv_r2_comparison.png"
)


def main() -> None:
    metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    rows = sorted(
        (
            {
                "model": model,
                "mean": values["cv_mean_r2"],
                "std": values["cv_std_r2"],
            }
            for model, values in metrics.items()
        ),
        key=lambda row: row["mean"],
    )

    models = [row["model"] for row in rows]
    means = [row["mean"] for row in rows]
    standard_deviations = [row["std"] for row in rows]
    colors = ["#7c3aed" if model == "Gradient Boosting" else "#94a3b8" for model in models]

    fig, ax = plt.subplots(figsize=(10, 5.8))
    bars = ax.barh(
        models,
        means,
        xerr=standard_deviations,
        color=colors,
        edgecolor="white",
        height=0.62,
        capsize=4,
        error_kw={"ecolor": "#334155", "elinewidth": 1.2, "capthick": 1.2},
    )

    ax.set_title("Candidate Model Cross-Validation Performance", fontsize=16, pad=16, weight="bold")
    ax.set_xlabel("Mean cross-validation $R^2$ (error bars: ±1 SD)", fontsize=11, labelpad=10)
    ax.set_ylabel("")
    ax.set_xlim(0, 0.70)
    ax.xaxis.grid(True, linestyle="--", alpha=0.28)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0, labelsize=10)

    for bar, mean, standard_deviation, model in zip(
        bars, means, standard_deviations, models
    ):
        ax.text(
            mean + standard_deviation + 0.007,
            bar.get_y() + bar.get_height() / 2,
            f"{mean:.4f}",
            va="center",
            ha="left",
            fontsize=10,
            weight="bold" if model == "Gradient Boosting" else "normal",
            color="#4c1d95" if model == "Gradient Boosting" else "#334155",
        )

    ax.text(
        0.99,
        0.02,
        "5-fold cross-validation on the training set",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=9,
        color="#64748b",
    )

    fig.tight_layout()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved chart to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
