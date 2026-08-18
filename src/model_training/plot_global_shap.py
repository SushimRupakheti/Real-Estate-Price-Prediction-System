"""Generate global SHAP importance for the current production pipeline."""
from __future__ import annotations

from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = PROJECT_ROOT / "models" / "best_model.joblib"
TRAIN_PATH = PROJECT_ROOT / "data" / "processed" / "X_train.csv"
OUTPUT_PATH = (
    PROJECT_ROOT
    / "visualizations"
    / "chart images"
    / "Figure_6_9_global_shap_importance.png"
)

DISPLAY_NAMES = {
    "LAND AREA (sqft)": "Land area",
    "AREA_PER_BEDROOM": "Area per bedroom",
    "TOTAL_ROOMS": "Total rooms",
    "PROPERTY AGE": "Property age",
    "ROAD ACCESS (ft)": "Road access",
    "HAS_PARKING": "Parking",
    "HAS_BALCONY": "Balcony",
    "HAS_GARDEN": "Garden",
    "HAS_MODULAR_KITCHEN": "Modular kitchen",
    "IS_NEW": "New property",
    "FLOOR": "Floors",
    "BEDROOM": "Bedrooms",
    "BATHROOM": "Bathrooms",
}


def feature_group(feature_name: str) -> str:
    if feature_name.startswith("LOCATION_"):
        return "Location"
    if feature_name.startswith("FACING_"):
        return "Facing direction"
    return DISPLAY_NAMES.get(feature_name, feature_name.replace("_", " ").title())


def main() -> None:
    pipeline = joblib.load(MODEL_PATH)
    training_data = pd.read_csv(TRAIN_PATH)
    preprocessor = pipeline.named_steps["preprocessing"]
    estimator = pipeline.named_steps["estimator"]

    transformed = preprocessor.transform(training_data)
    transformed_names = np.asarray(preprocessor.get_feature_names_out(), dtype=str)
    explanation = shap.TreeExplainer(estimator)(transformed)
    shap_values = np.asarray(explanation.values)

    grouped_signed_values: dict[str, np.ndarray] = {}
    for column_index, transformed_name in enumerate(transformed_names):
        group = feature_group(transformed_name)
        grouped_signed_values.setdefault(group, np.zeros(shap_values.shape[0]))
        grouped_signed_values[group] += shap_values[:, column_index]

    importance = pd.Series(
        {
            group: np.mean(np.abs(values)) / 1_000_000
            for group, values in grouped_signed_values.items()
        }
    ).sort_values(ascending=False).head(12).sort_values()

    colors = ["#7c3aed" if name in {"Location", "Land area"} else "#94a3b8" for name in importance.index]
    fig, ax = plt.subplots(figsize=(9.5, 6.4))
    bars = ax.barh(importance.index, importance.values, color=colors, height=0.66)
    ax.set_title("Global SHAP Feature Importance", fontsize=16, weight="bold", pad=16)
    ax.set_xlabel("Mean absolute SHAP value (NPR millions)", fontsize=11, labelpad=10)
    ax.set_ylabel("")
    ax.xaxis.grid(True, linestyle="--", alpha=0.25)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0, labelsize=10)

    offset = max(importance.max() * 0.015, 0.01)
    for bar, value in zip(bars, importance.values):
        ax.text(
            value + offset,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.2f}M",
            va="center",
            fontsize=9.5,
            color="#334155",
        )
    ax.set_xlim(0, importance.max() * 1.16)
    ax.text(
        0.99,
        0.02,
        "One-hot location and facing contributions aggregated by feature group",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=8.5,
        color="#64748b",
    )

    fig.tight_layout()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved chart to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
