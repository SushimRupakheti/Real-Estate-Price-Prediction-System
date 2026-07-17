"""Tune, retrain, and save the leakage-free Ridge Regression model."""
import json

import joblib
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, KFold

from compare_model import MODEL_DIR, build_pipeline, load_clean_data, split_data


def train_ridge_regression():
    X_train, X_test, y_train, y_test = split_data(load_clean_data())
    pipeline = build_pipeline(X_train, Ridge())
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    search = GridSearchCV(
        pipeline,
        {"estimator__alpha": [0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0, 300.0]},
        cv=cv,
        scoring="r2",
        n_jobs=1,
        refit=True,
    )
    search.fit(X_train, y_train)
    prediction = search.predict(X_test)
    best_alpha = float(search.best_params_["estimator__alpha"])
    best_index = search.best_index_
    metrics = {
        "model": "Ridge Regression",
        "parameters": {"alpha": best_alpha},
        "mae": float(mean_absolute_error(y_test, prediction)),
        "rmse": float(mean_squared_error(y_test, prediction) ** 0.5),
        "r2": float(r2_score(y_test, prediction)),
        "cv_mean_r2": float(search.best_score_),
        "cv_std_r2": float(search.cv_results_["std_test_score"][best_index]),
        "train_rows": len(X_train),
        "test_rows": len(X_test),
    }
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(search.best_estimator_, MODEL_DIR / "ridge_regression.joblib")
    (MODEL_DIR / "ridge_regression_metrics.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8"
    )
    print(json.dumps(metrics, indent=2))
    return search.best_estimator_, metrics


if __name__ == "__main__":
    train_ridge_regression()
