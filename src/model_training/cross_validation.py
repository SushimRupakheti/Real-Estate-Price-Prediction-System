import pandas as pd
import numpy as np
from sklearn.model_selection import KFold, cross_val_score
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor

# -------------------------
# LOAD DATA
# -------------------------
X_train = pd.read_csv(r"C:\Users\ASUS\Desktop\prediction_model\data\processed\X_train.csv")
X_test  = pd.read_csv(r"C:\Users\ASUS\Desktop\prediction_model\data\processed\X_test.csv")
y_train = pd.read_csv(r"C:\Users\ASUS\Desktop\prediction_model\data\processed\y_train.csv").squeeze()
y_test  = pd.read_csv(r"C:\Users\ASUS\Desktop\prediction_model\data\processed\y_test.csv").squeeze()

X_full = pd.concat([X_train, X_test], ignore_index=True)
y_full = pd.concat([y_train, y_test], ignore_index=True)

# -------------------------
# MODELS
# -------------------------
models = {
    "Linear Regression" : LinearRegression(),
    "Ridge Regression"  : Pipeline([
                            ("scaler", StandardScaler()),
                            ("ridge", Ridge(alpha=1.0))
                          ]),
    "Gradient Boosting" : GradientBoostingRegressor(
                            learning_rate=0.05,
                            max_depth=3,
                            n_estimators=200,
                            random_state=42
                          ),
    "XGBoost"           : XGBRegressor(
                            n_estimators=300,
                            learning_rate=0.05,
                            max_depth=4,
                            random_state=42,
                            verbosity=0
                          ),
    "LightGBM"          : LGBMRegressor(
                            n_estimators=300,
                            learning_rate=0.05,
                            max_depth=4,
                            random_state=42,
                            verbose=-1
                          ),
}

# -------------------------
# 5-FOLD CROSS VALIDATION
# -------------------------
kf = KFold(n_splits=5, shuffle=True, random_state=42)

print("=" * 75)
print(f"{'Model':<25} {'CV R² Mean':>12} {'CV R² Std':>12} {'Test R²':>10}")
print("=" * 75)

for name, m in models.items():
    # Cross validation scores
    cv_scores = cross_val_score(
        m, X_full, y_full,
        cv=kf,
        scoring="r2",
        n_jobs=-1
    )

    # Train on full train set, evaluate on test set
    m.fit(X_train, y_train)
    y_pred = m.predict(X_test)
    test_r2 = r2_score(y_test, y_pred)

    print(f"{name:<25} {cv_scores.mean():>12.4f} {cv_scores.std():>12.4f} {test_r2:>10.4f}")

print("=" * 75)

# -------------------------
# DETAILED XGBOOST CV
# -------------------------
print("\n--- XGBoost Fold-by-Fold Results ---")
xgb = XGBRegressor(
    n_estimators=300,
    learning_rate=0.05,
    max_depth=4,
    random_state=42,
    verbosity=0
)

fold_results = []
for fold, (train_idx, val_idx) in enumerate(kf.split(X_full, y_full), 1):
    X_tr = X_full.iloc[train_idx]
    y_tr = y_full.iloc[train_idx]
    X_val = X_full.iloc[val_idx]
    y_val = y_full.iloc[val_idx]

    xgb.fit(X_tr, y_tr)
    pred = xgb.predict(X_val)

    mae  = mean_absolute_error(y_val, pred)
    rmse = np.sqrt(mean_squared_error(y_val, pred))
    r2   = r2_score(y_val, pred)
    fold_results.append(r2)

    print(f"  Fold {fold}: MAE={mae:>12,.0f}  RMSE={rmse:>12,.0f}  R²={r2:.4f}")

print(f"\n  Mean R²: {np.mean(fold_results):.4f}")
print(f"  Std  R²: {np.std(fold_results):.4f}")
print(f"  Min  R²: {np.min(fold_results):.4f}")
print(f"  Max  R²: {np.max(fold_results):.4f}")

# -------------------------
# INVESTIGATE FOLD 3
# -------------------------
print("\n--- Investigating Fold 3 ---")
folds = list(kf.split(X_full, y_full))
train_idx, val_idx = folds[2]  # Fold 3

X_fold3 = X_full.iloc[val_idx]
y_fold3 = y_full.iloc[val_idx]

print(f"Fold 3 size: {len(X_fold3)}")
print(f"\nPrice stats in Fold 3:")
print(f"  Mean  : {y_fold3.mean():,.0f}")
print(f"  Median: {y_fold3.median():,.0f}")
print(f"  Max   : {y_fold3.max():,.0f}")
print(f"  Min   : {y_fold3.min():,.0f}")
print(f"\nLocation encoded stats:")
print(f"  Mean  : {X_fold3['LOCATION_ENCODED'].mean():,.0f}")
print(f"  Max   : {X_fold3['LOCATION_ENCODED'].max():,.0f}")

# -------------------------
# CV WITHOUT EXTREME OUTLIERS
# -------------------------
print("\n--- CV Without Extreme Outliers (price <= 10 Cr) ---")

mask = y_full <= 100000000  # 10 Cr cap
X_clean = X_full[mask].reset_index(drop=True)
y_clean = y_full[mask].reset_index(drop=True)

print(f"Samples after capping: {len(X_clean)} (removed {len(X_full) - len(X_clean)})")

xgb_clean = XGBRegressor(
    n_estimators=300,
    learning_rate=0.05,
    max_depth=4,
    random_state=42,
    verbosity=0
)

cv_clean = cross_val_score(
    xgb_clean, X_clean, y_clean,
    cv=KFold(n_splits=5, shuffle=True, random_state=42),
    scoring="r2",
    n_jobs=-1
)

print(f"CV R² Mean : {cv_clean.mean():.4f}")
print(f"CV R² Std  : {cv_clean.std():.4f}")
print(f"Min R²     : {cv_clean.min():.4f}")
print(f"Max R²     : {cv_clean.max():.4f}")