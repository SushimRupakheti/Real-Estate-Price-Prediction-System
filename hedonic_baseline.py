from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from lightgbm import LGBMRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "processed"
COEFFICIENT_PLOT_PATH = ROOT / "hedonic_coefficients.png"

LOG_FEATURES = ["LAND AREA (sqft)", "AREA_PER_BEDROOM"]


def load_split():
    X_train = pd.read_csv(DATA_DIR / "X_train.csv")
    X_test = pd.read_csv(DATA_DIR / "X_test.csv")
    y_train = pd.read_csv(DATA_DIR / "y_train.csv").squeeze("columns")
    y_test = pd.read_csv(DATA_DIR / "y_test.csv").squeeze("columns")
    return X_train, X_test, y_train, y_test


def prepare_hedonic_features(X):
    X_model = X.copy()
    for column in LOG_FEATURES:
        if column in X_model.columns:
            X_model[column] = np.log1p(X_model[column])
    return sm.add_constant(X_model, has_constant="add")


def fit_hedonic_ols(X_train, X_test, y_train, y_test):
    # Hedonic regression estimates house prices from property attributes
    # such as land area, rooms, access, age, amenities, and encoded location.
    # Following standard hedonic practice, the target price and size/area
    # features are modeled on the log scale.
    X_train_ols = prepare_hedonic_features(X_train)
    X_test_ols = prepare_hedonic_features(X_test)
    y_train_log = np.log1p(y_train)

    model = sm.OLS(y_train_log, X_train_ols).fit()
    y_pred = np.expm1(model.predict(X_test_ols))

    metrics = {
        "r2": r2_score(y_test, y_pred),
        "mae": mean_absolute_error(y_test, y_pred),
        "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
    }
    return model, metrics


def save_significant_coefficient_plot(model):
    coefficients = pd.DataFrame(
        {
            "feature": model.params.index,
            "coefficient": model.params.values,
            "p_value": model.pvalues.values,
        }
    )
    coefficients = coefficients[coefficients["feature"] != "const"]
    significant = coefficients[coefficients["p_value"] < 0.05].copy()

    if significant.empty:
        significant = coefficients.reindex(
            coefficients["coefficient"].abs().sort_values(ascending=False).index
        ).head(10)

    significant = significant.sort_values("coefficient")

    plt.figure(figsize=(10, max(5, 0.4 * len(significant))))
    colors = np.where(significant["coefficient"] >= 0, "#2563eb", "#dc2626")
    plt.barh(significant["feature"], significant["coefficient"], color=colors)
    plt.axvline(0, color="#111827", linewidth=0.8)
    plt.xlabel("Coefficient on log price")
    plt.title("Significant Hedonic Regression Coefficients (p < 0.05)")
    plt.tight_layout()
    plt.savefig(COEFFICIENT_PLOT_PATH, dpi=200)
    plt.close()


def compare_models(X_train, X_test, y_train, y_test, hedonic_metrics):
    models = {
        "Hedonic (OLS)": None,
        "Ridge Regression": Pipeline(
            [("scaler", StandardScaler()), ("ridge", Ridge(alpha=1.0))]
        ),
        "Linear Regression": LinearRegression(),
        "Gradient Boosting": GradientBoostingRegressor(
            learning_rate=0.05, max_depth=3, n_estimators=200, random_state=42
        ),
        "XGBoost": XGBRegressor(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=4,
            random_state=42,
            verbosity=0,
        ),
        "LightGBM": LGBMRegressor(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=4,
            random_state=42,
            verbose=-1,
        ),
    }

    rows = [
        {
            "Model": "Hedonic (OLS)",
            "R2": hedonic_metrics["r2"],
            "MAE": hedonic_metrics["mae"],
            "RMSE": hedonic_metrics["rmse"],
        }
    ]

    for name, model in models.items():
        if model is None:
            continue
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        rows.append(
            {
                "Model": name,
                "R2": r2_score(y_test, y_pred),
                "MAE": mean_absolute_error(y_test, y_pred),
                "RMSE": np.sqrt(mean_squared_error(y_test, y_pred)),
            }
        )

    return pd.DataFrame(rows)


def print_comparison_table(comparison):
    display = comparison.copy()
    display["R2"] = display["R2"].map(lambda value: f"{value:.4f}")
    display["MAE"] = display["MAE"].map(lambda value: f"{value:,.0f}")
    display["RMSE"] = display["RMSE"].map(lambda value: f"{value:,.0f}")

    print("\nModel Comparison")
    print(display.to_string(index=False))


def main():
    X_train, X_test, y_train, y_test = load_split()

    hedonic_model, hedonic_metrics = fit_hedonic_ols(
        X_train, X_test, y_train, y_test
    )

    print("\nHedonic Regression OLS Summary")
    print(hedonic_model.summary())

    print("\nHedonic Test Metrics")
    print(f"R2   : {hedonic_metrics['r2']:.4f}")
    print(f"MAE  : {hedonic_metrics['mae']:,.0f}")
    print(f"RMSE : {hedonic_metrics['rmse']:,.0f}")

    save_significant_coefficient_plot(hedonic_model)
    print(f"\nSaved coefficient plot to: {COEFFICIENT_PLOT_PATH}")

    comparison = compare_models(X_train, X_test, y_train, y_test, hedonic_metrics)
    print_comparison_table(comparison)


if __name__ == "__main__":
    main()
