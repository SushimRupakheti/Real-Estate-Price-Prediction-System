"""Generate held-out diagnostic plots for the selected production model."""
from __future__ import annotations

from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = PROJECT_ROOT / "models" / "best_model.joblib"
TEST_FEATURES_PATH = PROJECT_ROOT / "data" / "processed" / "X_test.csv"
TEST_TARGET_PATH = PROJECT_ROOT / "data" / "processed" / "y_test.csv"
OUTPUT_DIR = PROJECT_ROOT / "visualizations" / "chart images"
MILLION = 1_000_000


def style_axis(ax: plt.Axes) -> None:
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)


def save_actual_vs_predicted(actual: np.ndarray, predicted: np.ndarray) -> None:
    actual_m = actual / MILLION
    predicted_m = predicted / MILLION
    lower = min(actual_m.min(), predicted_m.min())
    upper = max(actual_m.max(), predicted_m.max())

    fig, ax = plt.subplots(figsize=(7.6, 6.2))
    ax.scatter(
        actual_m,
        predicted_m,
        s=34,
        color="#7c3aed",
        alpha=0.68,
        edgecolors="white",
        linewidths=0.45,
    )
    ax.plot(
        [lower, upper],
        [lower, upper],
        linestyle="--",
        color="#dc2626",
        linewidth=1.8,
        label="Perfect agreement",
    )
    ax.set_title("Actual vs Predicted Asking Prices", fontsize=15, weight="bold", pad=14)
    ax.set_xlabel("Actual asking price (NPR millions)", fontsize=11)
    ax.set_ylabel("Predicted asking price (NPR millions)", fontsize=11)
    ax.set_xlim(lower, upper)
    ax.set_ylim(lower, upper)
    ax.set_aspect("equal", adjustable="box")
    ax.legend(frameon=False, loc="upper left")
    style_axis(ax)
    fig.tight_layout()
    fig.savefig(
        OUTPUT_DIR / "Figure_6_6_actual_vs_predicted.png",
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(fig)


def save_residuals_vs_predicted(predicted: np.ndarray, residuals: np.ndarray) -> None:
    fig, ax = plt.subplots(figsize=(8.2, 5.6))
    ax.scatter(
        predicted / MILLION,
        residuals / MILLION,
        s=34,
        color="#2563eb",
        alpha=0.68,
        edgecolors="white",
        linewidths=0.45,
    )
    ax.axhline(0, linestyle="--", color="#dc2626", linewidth=1.8)
    ax.set_title("Residuals vs Predicted Asking Prices", fontsize=15, weight="bold", pad=14)
    ax.set_xlabel("Predicted asking price (NPR millions)", fontsize=11)
    ax.set_ylabel("Residual: actual − predicted (NPR millions)", fontsize=11)
    style_axis(ax)
    fig.tight_layout()
    fig.savefig(
        OUTPUT_DIR / "Figure_6_7_residuals_vs_predicted.png",
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(fig)


def save_residual_distribution(residuals: np.ndarray) -> None:
    residuals_m = residuals / MILLION
    fig, ax = plt.subplots(figsize=(8.2, 5.6))
    ax.hist(
        residuals_m,
        bins=24,
        color="#7c3aed",
        alpha=0.82,
        edgecolor="white",
        linewidth=0.8,
    )
    ax.axvline(0, linestyle="--", color="#dc2626", linewidth=1.8, label="Zero error")
    ax.axvline(
        residuals_m.mean(),
        color="#0f766e",
        linewidth=1.8,
        label=f"Mean residual: {residuals_m.mean():.2f}M",
    )
    ax.set_title("Distribution of Prediction Residuals", fontsize=15, weight="bold", pad=14)
    ax.set_xlabel("Residual: actual − predicted (NPR millions)", fontsize=11)
    ax.set_ylabel("Number of test observations", fontsize=11)
    ax.legend(frameon=False)
    style_axis(ax)
    fig.tight_layout()
    fig.savefig(
        OUTPUT_DIR / "Figure_6_8_residual_distribution.png",
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
    )
    fig.savefig(
        OUTPUT_DIR / "Figure_7_2_prediction_error_distribution.png",
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(fig)


def main() -> None:
    model = joblib.load(MODEL_PATH)
    test_features = pd.read_csv(TEST_FEATURES_PATH)
    actual = pd.read_csv(TEST_TARGET_PATH).squeeze("columns").to_numpy(dtype=float)
    predicted = np.asarray(model.predict(test_features), dtype=float)
    residuals = actual - predicted

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    save_actual_vs_predicted(actual, predicted)
    save_residuals_vs_predicted(predicted, residuals)
    save_residual_distribution(residuals)

    print(f"Generated 3 diagnostic figures in: {OUTPUT_DIR}")
    print(f"Test observations: {len(actual)}")
    print(f"Mean residual: NPR {residuals.mean():,.0f}")


if __name__ == "__main__":
    main()
