"""Tune Gradient Boosting while keeping preprocessing inside every CV fold."""
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import GridSearchCV
from compare_model import build_pipeline, load_clean_data, split_data

if __name__ == "__main__":
    X_train, X_test, y_train, y_test = split_data(load_clean_data())
    pipeline = build_pipeline(X_train, GradientBoostingRegressor(random_state=42))
    search = GridSearchCV(pipeline, {
        "estimator__n_estimators": [100, 200, 300],
        "estimator__learning_rate": [.05, .1, .2],
        "estimator__max_depth": [3, 4, 5],
    }, cv=5, scoring="r2", n_jobs=-1)
    search.fit(X_train, y_train)
    print("Best parameters:", search.best_params_)
    print("Best CV R2:", round(search.best_score_, 4))
    print("Test R2:", round(search.score(X_test, y_test), 4))
