"""Generate current-pipeline city segment performance and SHAP figures."""
from __future__ import annotations

from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from sklearn.metrics import mean_absolute_error, r2_score


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = PROJECT_ROOT / "models" / "best_model.joblib"
TEST_FEATURES_PATH = PROJECT_ROOT / "data" / "processed" / "X_test.csv"
TEST_TARGET_PATH = PROJECT_ROOT / "data" / "processed" / "y_test.csv"
OUTPUT_DIR = PROJECT_ROOT / "visualizations" / "chart images"
MIN_SEGMENT_SIZE = 15
MILLION = 1_000_000

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


def extract_city(location: object) -> str:
    parts = [part.strip() for part in str(location).split(",")]
    return parts[-1] if len(parts) > 1 and parts[-1] else "Unknown"


def feature_group(feature_name: str) -> str:
    if feature_name.startswith("LOCATION_"):
        return "Location"
    if feature_name.startswith("FACING_"):
        return "Facing direction"
    return DISPLAY_NAMES.get(feature_name, feature_name.replace("_", " ").title())


def evaluate_segments(
    pipeline: object, test_features: pd.DataFrame, actual: np.ndarray
) -> pd.DataFrame:
    working = test_features.copy()
    working["CITY"] = working["LOCATION"].map(extract_city)
    rows: list[dict[str, float | int | str]] = []
    for city, indexes in working.groupby("CITY").groups.items():
        if len(indexes) < MIN_SEGMENT_SIZE:
            continue
        positions = working.index.get_indexer(indexes)
        segment_features = test_features.loc[indexes]
        segment_actual = actual[positions]
        predicted = np.asarray(pipeline.predict(segment_features), dtype=float)
        rows.append(
            {
                "Segment": city,
                "Test n": len(indexes),
                "MAE (NPR)": mean_absolute_error(segment_actual, predicted),
                "R2": r2_score(segment_actual, predicted),
            }
        )
    return pd.DataFrame(rows).sort_values("R2", ascending=False).reset_index(drop=True)


def save_performance_plot(results: pd.DataFrame) -> None:
    plot_data = results.sort_values("R2")
    fig, ax = plt.subplots(figsize=(8.6, 5.2))
    colors = ["#7c3aed" if city == "Kathmandu" else "#64748b" for city in plot_data["Segment"]]
    bars = ax.barh(plot_data["Segment"], plot_data["R2"], color=colors, height=0.58)
    ax.axvline(0, color="#334155", linewidth=0.8)
    ax.set_title("Held-Out Performance by City Segment", fontsize=16, weight="bold", pad=15)
    ax.set_xlabel("$R^2$", fontsize=11)
    ax.set_ylabel("")
    ax.xaxis.grid(True, linestyle="--", alpha=0.25)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)

    label_offset = max(plot_data["R2"].max() * 0.025, 0.015)
    for bar, (_, row) in zip(bars, plot_data.iterrows()):
        ax.text(
            row["R2"] + label_offset,
            bar.get_y() + bar.get_height() / 2,
            f"$R^2$ = {row['R2']:.3f}  |  n = {int(row['Test n'])}",
            va="center",
            fontsize=10,
            color="#334155",
        )
    ax.set_xlim(min(0, plot_data["R2"].min() - 0.1), plot_data["R2"].max() * 1.32)
    fig.tight_layout()
    fig.savefig(
        OUTPUT_DIR / "Figure_6_11_segment_performance.png",
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(fig)


def grouped_segment_shap(
    pipeline: object, test_features: pd.DataFrame, segments: list[str]
) -> pd.DataFrame:
    preprocessor = pipeline.named_steps["preprocessing"]
    estimator = pipeline.named_steps["estimator"]
    transformed_names = np.asarray(preprocessor.get_feature_names_out(), dtype=str)
    explainer = shap.TreeExplainer(estimator)
    cities = test_features["LOCATION"].map(extract_city)
    rows: list[dict[str, float | str]] = []

    for city in segments:
        segment_features = test_features.loc[cities == city]
        transformed = preprocessor.transform(segment_features)
        shap_values = np.asarray(explainer(transformed).values)
        grouped: dict[str, np.ndarray] = {}
        for column_index, transformed_name in enumerate(transformed_names):
            group = feature_group(transformed_name)
            grouped.setdefault(group, np.zeros(shap_values.shape[0]))
            grouped[group] += shap_values[:, column_index]
        for group, values in grouped.items():
            rows.append(
                {
                    "Segment": city,
                    "Feature": group,
                    "Mean absolute SHAP (NPR)": np.mean(np.abs(values)),
                }
            )
    return pd.DataFrame(rows)


def save_segment_shap_plot(importance: pd.DataFrame) -> None:
    totals = (
        importance.groupby("Feature")["Mean absolute SHAP (NPR)"]
        .mean()
        .nlargest(7)
        .index
    )
    selected = importance[importance["Feature"].isin(totals)]
    pivot = selected.pivot(index="Feature", columns="Segment", values="Mean absolute SHAP (NPR)")
    pivot = pivot.loc[pivot.mean(axis=1).sort_values().index] / MILLION

    colors = ["#7c3aed", "#94a3b8", "#0f766e", "#d97706"][: len(pivot.columns)]
    ax = pivot.plot(kind="barh", figsize=(9.6, 6.3), width=0.76, color=colors)
    ax.set_title("Feature Contributions by City Segment", fontsize=16, weight="bold", pad=15)
    ax.set_xlabel("Mean absolute SHAP value (NPR millions)", fontsize=11, labelpad=9)
    ax.set_ylabel("")
    ax.xaxis.grid(True, linestyle="--", alpha=0.25)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.legend(title="City segment", frameon=False, loc="lower right")
    ax.figure.tight_layout()
    ax.figure.savefig(
        OUTPUT_DIR / "Figure_6_12_segment_shap.png",
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(ax.figure)


def main() -> None:
    pipeline = joblib.load(MODEL_PATH)
    test_features = pd.read_csv(TEST_FEATURES_PATH).reset_index(drop=True)
    actual = pd.read_csv(TEST_TARGET_PATH).squeeze("columns").to_numpy(dtype=float)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results = evaluate_segments(pipeline, test_features, actual)
    if results.empty:
        raise RuntimeError(f"No city segment met the minimum test size of {MIN_SEGMENT_SIZE}.")
    save_performance_plot(results)
    importance = grouped_segment_shap(pipeline, test_features, results["Segment"].tolist())
    save_segment_shap_plot(importance)
    results.to_csv(OUTPUT_DIR / "Table_6_2_city_segment_metrics.csv", index=False)

    display = results.copy()
    display["MAE (NPR)"] = display["MAE (NPR)"].map(lambda value: f"{value:,.0f}")
    display["R2"] = display["R2"].map(lambda value: f"{value:.4f}")
    print(display.to_string(index=False))


if __name__ == "__main__":
    main()
