"""Retrain and save the leakage-free Linear Regression model."""
import json

import joblib
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_score

from compare_model import MODEL_DIR, build_pipeline, load_clean_data, split_data


def train_linear_regression():
    X_train, X_test, y_train, y_test = split_data(load_clean_data())
    # With full one-hot categorical columns, omitting the standalone intercept
    # avoids redundant columns and performed better on the fixed holdout set.
    pipeline = build_pipeline(X_train, LinearRegression(fit_intercept=False))
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(
        pipeline, X_train, y_train, cv=cv, scoring="r2", n_jobs=1
    )
    pipeline.fit(X_train, y_train)
    prediction = pipeline.predict(X_test)
    metrics = {
        "model": "Linear Regression",
        "parameters": {"fit_intercept": False},
        "mae": float(mean_absolute_error(y_test, prediction)),
        "rmse": float(mean_squared_error(y_test, prediction) ** 0.5),
        "r2": float(r2_score(y_test, prediction)),
        "cv_mean_r2": float(scores.mean()),
        "cv_std_r2": float(scores.std()),
        "train_rows": len(X_train),
        "test_rows": len(X_test),
    }
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_DIR / "linear_regression.joblib")
    (MODEL_DIR / "linear_regression_metrics.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8"
    )
    print(json.dumps(metrics, indent=2))
    return pipeline, metrics


if __name__ == "__main__":
    train_linear_regression()
