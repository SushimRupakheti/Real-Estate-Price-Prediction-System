"""Train and compare house-price models without target leakage."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBRegressor

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "cleaned_house_data.csv"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODEL_DIR = PROJECT_ROOT / "models"
TARGET, RANDOM_STATE = "PRICE", 42

def load_clean_data():
    data = pd.read_csv(DATA_PATH)
    data = data[(data["BEDROOM"] <= 10) & (data["BATHROOM"] <= 10)]
    data = data[data[TARGET] <= 100_000_000].copy()
    data = data.drop(columns=["LOCATION_ENCODED", "FACING_ENCODED"], errors="ignore")
    data["FACING"] = (data["FACING"].astype("string").str.strip().str.lower()
        .str.replace(" ", "-", regex=False).replace("west-/-north", "north-west"))
    data["AREA_PER_BEDROOM"] = data["LAND AREA (sqft)"] / data["BEDROOM"].replace(0, np.nan)
    data["TOTAL_ROOMS"] = data["BEDROOM"] + data["BATHROOM"]
    data["IS_NEW"] = (data["PROPERTY AGE"] <= 2).astype(int)
    return data

def split_data(data):
    return train_test_split(data.drop(columns=[TARGET]), data[TARGET], test_size=.2, random_state=RANDOM_STATE)

def make_preprocessor(X):
    categorical = X.select_dtypes(include=["object", "string", "category"]).columns.tolist()
    numeric = X.columns.difference(categorical, sort=False).tolist()
    return ColumnTransformer([
        ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median")),
                              ("scaler", StandardScaler())]), numeric),
        ("categorical", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")),
          ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]), categorical),
    ], verbose_feature_names_out=False)

def estimators():
    return {
      "Linear Regression": LinearRegression(), "Ridge Regression": Ridge(alpha=1.0),
      "Gradient Boosting": GradientBoostingRegressor(learning_rate=.05, max_depth=3, n_estimators=200, random_state=42),
      "XGBoost": XGBRegressor(n_estimators=300, learning_rate=.05, max_depth=4, random_state=42, verbosity=0, n_jobs=1),
      "LightGBM": LGBMRegressor(n_estimators=300, learning_rate=.05, max_depth=4, random_state=42, verbose=-1, n_jobs=1),
    }

def build_pipeline(X, estimator):
    return Pipeline([("preprocessing", make_preprocessor(X)), ("estimator", estimator)])

def train_and_evaluate():
    X_train, X_test, y_train, y_test = split_data(load_clean_data())
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True); MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for name, value in [("X_train", X_train), ("X_test", X_test), ("y_train", y_train), ("y_test", y_test)]:
        value.to_csv(PROCESSED_DIR / f"{name}.csv", index=False)
    cv, results, fitted = KFold(5, shuffle=True, random_state=42), {}, {}
    for name, estimator in estimators().items():
        pipeline = build_pipeline(X_train, estimator)
        scores = cross_val_score(pipeline, X_train, y_train, cv=cv, scoring="r2", n_jobs=1)
        pipeline.fit(X_train, y_train)
        prediction = pipeline.predict(X_test)
        results[name] = {"mae": float(mean_absolute_error(y_test, prediction)),
          "rmse": float(mean_squared_error(y_test, prediction) ** .5), "r2": float(r2_score(y_test, prediction)),
          "cv_mean_r2": float(scores.mean()), "cv_std_r2": float(scores.std())}
        fitted[name] = pipeline
    best_name = max(results, key=lambda name: results[name]["r2"])
    joblib.dump(fitted[best_name], MODEL_DIR / "best_model.joblib")
    joblib.dump(fitted[best_name], MODEL_DIR / "best_model.pkl")
    (MODEL_DIR / "metrics.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    categorical = X_train.select_dtypes(include=["object", "string", "category"]).columns.tolist()
    schema = {"target": TARGET, "features": [{"name": c, "dtype": str(X_train[c].dtype), "required": True} for c in X_train],
              "numeric_features": [c for c in X_train if c not in categorical], "categorical_features": categorical}
    (MODEL_DIR / "feature_schema.json").write_text(json.dumps(schema, indent=2), encoding="utf-8")
    metadata = {"best_model": best_name, "selection_metric": "test_r2", "trained_at_utc": datetime.now(timezone.utc).isoformat(),
      "random_state": 42, "test_size": .2, "train_rows": len(X_train), "test_rows": len(X_test),
      "cross_validation": "5-fold KFold on training data only", "artifact": "best_model.joblib",
      "preprocessing": "fitted inside sklearn Pipeline on training data only"}
    (MODEL_DIR / "model_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    frame = pd.DataFrame(results).T
    print(frame.to_string(float_format=lambda v: f"{v:,.4f}")); print(f"\nBest model: {best_name}")
    return frame, best_name

if __name__ == "__main__":
    train_and_evaluate()
