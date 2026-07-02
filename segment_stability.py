"""
Academic justification:
This script evaluates whether the trained Gradient Boosting model behaves
consistently across city segments. The analysis directly supports the project
question about relationship stability across locations. Because the original
data has LOCATION but no coordinates, CITY is used only as a segmentation
variable and is not added to the prediction input. Segment-level performance
and feature-importance shifts reveal whether learned price relationships are
stable or city-specific.
"""

from pathlib import Path
import pickle
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

try:
    import shap
except ImportError:
    shap = None


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "processed"
MODEL_DIR = ROOT / "models"
RANDOM_STATE = 42
TEST_SIZE = 0.2
MIN_SEGMENT_SIZE = 15

BASE_FEATURES = [
    "FLOOR",
    "BEDROOM",
    "BATHROOM",
    "LAND AREA (sqft)",
    "ROAD ACCESS (ft)",
    "PROPERTY AGE",
    "HAS_PARKING",
    "HAS_BALCONY",
    "HAS_GARDEN",
    "HAS_MODULAR_KITCHEN",
    "LOCATION_ENCODED",
    "FACING_ENCODED",
    "AREA_PER_BEDROOM",
    "TOTAL_ROOMS",
    "IS_NEW",
]


def extract_city(location):
    parts = str(location).split(", ")
    return parts[1].strip() if len(parts) > 1 else "Unknown"


def load_engineered_dataset():
    data = pd.read_csv(DATA_DIR / "cleaned_house_data.csv")
    data = data[(data["BEDROOM"] <= 10) & (data["BATHROOM"] <= 10)].copy()
    data = data[data["PRICE"] <= 100_000_000].copy()

    data["FACING"] = data["FACING"].str.strip().str.lower()
    data["FACING"] = data["FACING"].str.replace(" ", "-", regex=False)
    data["FACING"] = data["FACING"].replace("west-/-north", "north-west")

    encoder = LabelEncoder()
    data["FACING_ENCODED"] = encoder.fit_transform(data["FACING"].astype(str))
    data["AREA_PER_BEDROOM"] = data["LAND AREA (sqft)"] / data["BEDROOM"]
    data["TOTAL_ROOMS"] = data["BEDROOM"] + data["BATHROOM"]
    data["IS_NEW"] = (data["PROPERTY AGE"] <= 2).astype(int)
    data["CITY"] = data["LOCATION"].apply(extract_city)
    return data


def load_test_data_with_city():
    data = load_engineered_dataset()
    X = data[BASE_FEATURES]
    y = data["PRICE"]
    meta = data[["CITY"]]

    _, X_test, _, y_test, _, meta_test = train_test_split(
        X,
        y,
        meta,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
    )

    saved_X_test = pd.read_csv(DATA_DIR / "X_test.csv")
    saved_y_test = pd.read_csv(DATA_DIR / "y_test.csv").squeeze("columns")
    if not np.allclose(saved_X_test[BASE_FEATURES], X_test[BASE_FEATURES]):
        warnings.warn("Reconstructed X_test differs from saved X_test.csv.")
    if not np.allclose(saved_y_test, y_test):
        warnings.warn("Reconstructed y_test differs from saved y_test.csv.")

    X_test = saved_X_test.copy()
    X_test["CITY"] = meta_test["CITY"].to_numpy()
    return X_test, saved_y_test


def load_gradient_boosting_model():
    preferred_paths = [
        MODEL_DIR / "best_model.pkl",
        MODEL_DIR / "gradient_boosting_model.pkl",
    ]
    for path in preferred_paths:
        if path.exists():
            with path.open("rb") as file_handle:
                return pickle.load(file_handle), path
    raise FileNotFoundError("No trained Gradient Boosting model found in models/.")


def evaluate_segments(model, X_test_with_city, y_test):
    rows = []
    feature_X = X_test_with_city[BASE_FEATURES]

    for city, group in X_test_with_city.groupby("CITY"):
        if len(group) < MIN_SEGMENT_SIZE:
            continue
        idx = group.index
        y_true = y_test.loc[idx] if hasattr(y_test, "loc") else y_test.iloc[idx]
        y_pred = model.predict(feature_X.loc[idx])
        rows.append(
            {
                "CITY": city,
                "Samples": len(group),
                "R2": r2_score(y_true, y_pred),
                "MAE": mean_absolute_error(y_true, y_pred),
                "RMSE": np.sqrt(mean_squared_error(y_true, y_pred)),
            }
        )

    table = pd.DataFrame(rows).sort_values("R2", ascending=False)
    print("\nSegment Performance")
    if table.empty:
        print(f"No city segment has at least {MIN_SEGMENT_SIZE} test samples.")
    else:
        display = table.copy()
        display["R2"] = display["R2"].map(lambda value: f"{value:.4f}")
        display["MAE"] = display["MAE"].map(lambda value: f"{value:,.0f}")
        display["RMSE"] = display["RMSE"].map(lambda value: f"{value:,.0f}")
        print(display.to_string(index=False))
    return table


def shap_or_permutation_importance(model, X_segment, y_segment):
    if shap is not None:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_segment)
        values = np.abs(shap_values).mean(axis=0)
        return pd.Series(values, index=X_segment.columns), "SHAP"

    result = permutation_importance(
        model,
        X_segment,
        y_segment,
        n_repeats=10,
        random_state=RANDOM_STATE,
        scoring="neg_mean_absolute_error",
    )
    values = np.maximum(result.importances_mean, 0)
    return pd.Series(values, index=X_segment.columns), "Permutation fallback"


def compute_segment_importance(model, X_test_with_city, y_test, segment_table):
    rows = []
    method_used = "SHAP" if shap is not None else "Permutation fallback"
    if shap is None:
        print(
            "\nSHAP is not installed in this environment; using permutation "
            "importance as a runnable fallback. Install shap to produce true "
            "segment-level SHAP values."
        )

    for city in segment_table["CITY"]:
        mask = X_test_with_city["CITY"] == city
        X_segment = X_test_with_city.loc[mask, BASE_FEATURES]
        y_segment = y_test.loc[X_segment.index]
        importance, method_used = shap_or_permutation_importance(
            model, X_segment, y_segment
        )
        top_features = importance.sort_values(ascending=False).head(3)
        for feature, value in top_features.items():
            rows.append(
                {
                    "CITY": city,
                    "Feature": feature,
                    "Importance": value,
                    "Method": method_used,
                }
            )

    table = pd.DataFrame(rows)
    print(f"\nTop 3 Segment Feature Importances ({method_used})")
    if table.empty:
        print("No segment importance table available.")
    else:
        display = table.copy()
        display["Importance"] = display["Importance"].map(lambda value: f"{value:,.2f}")
        print(display.to_string(index=False))
    return table


def save_segment_performance_plot(segment_table):
    if segment_table.empty:
        return

    plot_data = segment_table.sort_values("R2", ascending=True)
    plt.figure(figsize=(9, 5))
    plt.barh(plot_data["CITY"], plot_data["R2"], color="#2563eb")
    plt.axvline(0, color="#111827", linewidth=0.8)
    plt.xlabel("R2")
    plt.title("Gradient Boosting Performance by City Segment")
    plt.tight_layout()
    plt.savefig(ROOT / "segment_performance.png", dpi=200)
    plt.close()


def save_segment_importance_plot(importance_table):
    if importance_table.empty:
        return

    pivot = importance_table.pivot_table(
        index="CITY",
        columns="Feature",
        values="Importance",
        aggfunc="mean",
        fill_value=0,
    )
    pivot.plot(kind="bar", figsize=(11, 6), width=0.82)
    plt.ylabel("Mean absolute importance")
    plt.title("Top Feature Importance Shifts by City Segment")
    plt.xticks(rotation=30, ha="right")
    plt.legend(title="Feature", bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(ROOT / "segment_shap.png", dpi=200)
    plt.close()


def main():
    model, model_path = load_gradient_boosting_model()
    X_test_with_city, y_test = load_test_data_with_city()
    y_test = y_test.reset_index(drop=True)
    X_test_with_city = X_test_with_city.reset_index(drop=True)

    print(f"Loaded model: {model_path}")
    segment_table = evaluate_segments(model, X_test_with_city, y_test)
    save_segment_performance_plot(segment_table)

    importance_table = compute_segment_importance(
        model, X_test_with_city, y_test, segment_table
    )
    save_segment_importance_plot(importance_table)

    if not segment_table.empty:
        print(f"\nSaved: {ROOT / 'segment_performance.png'}")
    if not importance_table.empty:
        print(f"Saved: {ROOT / 'segment_shap.png'}")


if __name__ == "__main__":
    main()
