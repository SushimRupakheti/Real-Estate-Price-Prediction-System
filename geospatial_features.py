"""
Academic justification:
The dataset does not include coordinates, road-network distance, or direct
OSMnx accessibility measures. This script therefore adds geospatial proxy
features from the available LOCATION and LOCATION_ENCODED fields. CITY_TIER
captures Nepal's urban hierarchy, LOCATION_PRICE_TIER captures market-position
bands, and LOCATION_PREMIUM_RATIO captures how premium a location is relative
to the market median. These variables are consistent with hedonic pricing
theory because location attributes are treated as components of housing value.
"""

from pathlib import Path
import pickle
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler

try:
    from xgboost import XGBRegressor
except ImportError:
    XGBRegressor = None

try:
    from lightgbm import LGBMRegressor
except ImportError:
    LGBMRegressor = None


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "processed"
MODEL_DIR = ROOT / "models"
RANDOM_STATE = 42
TEST_SIZE = 0.2

BEFORE_RESULTS = {
    "Hedonic (OLS)": {"r2": 0.6593, "mae": 6819377},
    "Ridge Regression": {"r2": 0.6901, "mae": 6399840},
    "Linear Regression": {"r2": 0.6903, "mae": 6397621},
    "Gradient Boosting": {"r2": 0.7287, "mae": 6075427},
    "XGBoost": {"r2": 0.7041, "mae": 6257837},
    "LightGBM": {"r2": 0.7059, "mae": 6328997},
}

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
LOG_FEATURES = ["LAND AREA (sqft)", "AREA_PER_BEDROOM"]


def extract_city(location):
    parts = str(location).split(", ")
    return parts[1].strip() if len(parts) > 1 else "Unknown"


def city_tier(city):
    if city in {"Kathmandu", "Lalitpur"}:
        return 3
    if city in {"Bhaktapur", "Kaski"}:
        return 2
    return 1


def location_price_tier(location_encoded):
    if location_encoded >= 60_000_000:
        return 3
    if location_encoded >= 30_000_000:
        return 2
    return 1


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

    median_location_encoded = data["LOCATION_ENCODED"].median()
    data["CITY"] = data["LOCATION"].apply(extract_city)
    data["CITY_TIER"] = data["CITY"].apply(city_tier)
    data["LOCATION_PRICE_TIER"] = data["LOCATION_ENCODED"].apply(location_price_tier)
    data["LOCATION_PREMIUM_RATIO"] = (
        data["LOCATION_ENCODED"] / median_location_encoded
    )
    return data


def build_geo_splits():
    data = load_engineered_dataset()
    X = data[BASE_FEATURES]
    y = data["PRICE"]
    geo_features = data[["CITY_TIER", "LOCATION_PRICE_TIER", "LOCATION_PREMIUM_RATIO"]]

    X_train, X_test, y_train, y_test, geo_train, geo_test = train_test_split(
        X,
        y,
        geo_features,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
    )

    saved_X_train = pd.read_csv(DATA_DIR / "X_train.csv")
    saved_X_test = pd.read_csv(DATA_DIR / "X_test.csv")
    if not np.allclose(saved_X_train[BASE_FEATURES], X_train[BASE_FEATURES]):
        warnings.warn("Reconstructed X_train differs from saved X_train.csv.")
    if not np.allclose(saved_X_test[BASE_FEATURES], X_test[BASE_FEATURES]):
        warnings.warn("Reconstructed X_test differs from saved X_test.csv.")

    X_train_geo = saved_X_train.copy()
    X_test_geo = saved_X_test.copy()
    for column in geo_features.columns:
        X_train_geo[column] = geo_train[column].to_numpy()
        X_test_geo[column] = geo_test[column].to_numpy()

    X_train_geo.to_csv(DATA_DIR / "X_train_geo.csv", index=False)
    X_test_geo.to_csv(DATA_DIR / "X_test_geo.csv", index=False)
    return X_train_geo, X_test_geo, y_train.reset_index(drop=True), y_test.reset_index(drop=True)


def prepare_hedonic_features(X):
    X_model = X.copy()
    for column in LOG_FEATURES:
        if column in X_model.columns:
            X_model[column] = np.log1p(X_model[column])
    return sm.add_constant(X_model, has_constant="add")


def evaluate_predictions(y_true, y_pred):
    return {
        "r2": r2_score(y_true, y_pred),
        "mae": mean_absolute_error(y_true, y_pred),
        "rmse": np.sqrt(mean_squared_error(y_true, y_pred)),
    }


def fit_hedonic(X_train, X_test, y_train, y_test):
    model = sm.OLS(np.log1p(y_train), prepare_hedonic_features(X_train)).fit(
        cov_type="HC3"
    )
    y_pred = np.expm1(model.predict(prepare_hedonic_features(X_test)))
    return evaluate_predictions(y_test, y_pred), model


def get_models():
    models = {
        "Ridge Regression": Pipeline(
            [("scaler", StandardScaler()), ("ridge", Ridge(alpha=1.0))]
        ),
        "Linear Regression": LinearRegression(),
        "Gradient Boosting": GradientBoostingRegressor(
            learning_rate=0.05,
            max_depth=3,
            n_estimators=200,
            random_state=RANDOM_STATE,
        ),
    }
    if XGBRegressor is not None:
        models["XGBoost"] = XGBRegressor(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=4,
            random_state=RANDOM_STATE,
            verbosity=0,
        )
    else:
        print("Skipping XGBoost: xgboost is not installed in this environment.")

    if LGBMRegressor is not None:
        models["LightGBM"] = LGBMRegressor(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=4,
            random_state=RANDOM_STATE,
            verbose=-1,
        )
    else:
        print("Skipping LightGBM: lightgbm is not installed in this environment.")
    return models


def evaluate_geo_models(X_train_geo, X_test_geo, y_train, y_test):
    results = {}

    hedonic_metrics, _ = fit_hedonic(X_train_geo, X_test_geo, y_train, y_test)
    results["Hedonic (OLS)"] = {"metrics": hedonic_metrics, "model": None}

    for name, model in get_models().items():
        model.fit(X_train_geo, y_train)
        y_pred = model.predict(X_test_geo)
        results[name] = {
            "metrics": evaluate_predictions(y_test, y_pred),
            "model": model,
        }
    return results


def print_before_after_table(after_results):
    rows = []
    for name, before in BEFORE_RESULTS.items():
        after = after_results.get(name, {}).get("metrics")
        rows.append(
            {
                "Model": name,
                "R2 (before)": before["r2"],
                "R2 (after)": np.nan if after is None else after["r2"],
                "MAE (before)": before["mae"],
                "MAE (after)": np.nan if after is None else after["mae"],
            }
        )

    table = pd.DataFrame(rows)
    display = table.copy()
    display["R2 (before)"] = display["R2 (before)"].map(lambda value: f"{value:.4f}")
    display["R2 (after)"] = display["R2 (after)"].map(
        lambda value: "skipped" if pd.isna(value) else f"{value:.4f}"
    )
    display["MAE (before)"] = display["MAE (before)"].map(lambda value: f"{value:,.0f}")
    display["MAE (after)"] = display["MAE (after)"].map(
        lambda value: "skipped" if pd.isna(value) else f"{value:,.0f}"
    )

    print("\nBefore/After Model Comparison")
    print(display.to_string(index=False))
    return table


def maybe_save_geo_model(after_results):
    gb_result = after_results.get("Gradient Boosting")
    if gb_result is None:
        print("\nGradient Boosting was not trained; no geo model saved.")
        return

    before_r2 = BEFORE_RESULTS["Gradient Boosting"]["r2"]
    after_r2 = gb_result["metrics"]["r2"]
    if after_r2 > before_r2:
        output_path = MODEL_DIR / "gradient_boosting_geo.pkl"
        with output_path.open("wb") as file_handle:
            pickle.dump(gb_result["model"], file_handle)
        print(
            f"\nGeo features improved Gradient Boosting R2 "
            f"({before_r2:.4f} -> {after_r2:.4f})."
        )
        print(f"Saved improved model to: {output_path}")
    else:
        print(
            f"\nGeo features did not improve Gradient Boosting R2 "
            f"({before_r2:.4f} -> {after_r2:.4f}); keeping existing model."
        )


def main():
    X_train_geo, X_test_geo, y_train, y_test = build_geo_splits()
    print(f"Saved: {DATA_DIR / 'X_train_geo.csv'}")
    print(f"Saved: {DATA_DIR / 'X_test_geo.csv'}")

    after_results = evaluate_geo_models(X_train_geo, X_test_geo, y_train, y_test)
    print_before_after_table(after_results)
    maybe_save_geo_model(after_results)


if __name__ == "__main__":
    main()
