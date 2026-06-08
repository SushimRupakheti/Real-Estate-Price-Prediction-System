import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
import pickle
from pathlib import Path
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler




# -------------------------
# LOAD DATA
# -------------------------
X_train = pd.read_csv(r"C:\Users\ASUS\Desktop\prediction_model\data\processed\X_train.csv")
X_test  = pd.read_csv(r"C:\Users\ASUS\Desktop\prediction_model\data\processed\X_test.csv")
y_train = pd.read_csv(r"C:\Users\ASUS\Desktop\prediction_model\data\processed\y_train.csv").squeeze()
y_test  = pd.read_csv(r"C:\Users\ASUS\Desktop\prediction_model\data\processed\y_test.csv").squeeze()

# -------------------------
# MODELS
# -------------------------
models = {
    "Linear Regression"  : LinearRegression(),
    
    "Ridge Regression": Pipeline([
    ("scaler", StandardScaler()),
    ("ridge", Ridge(alpha=1.0))
      ]),
    "Gradient Boosting"  : GradientBoostingRegressor(
                              learning_rate=0.05,
                              max_depth=3,
                              n_estimators=200,
                              random_state=42
                          ),
    "XGBoost"            : XGBRegressor(
                              n_estimators=300,
                              learning_rate=0.05,
                              max_depth=4,
                              random_state=42,
                              verbosity=0
                          ),
    "LightGBM"           : LGBMRegressor(
                              n_estimators=300,
                              learning_rate=0.05,
                              max_depth=4,
                              random_state=42,
                              verbose=-1
                          ),
}

# -------------------------
# COMPARE
# -------------------------
print(f"\n{'Model':<25} {'MAE':>15} {'RMSE':>15} {'R²':>8}")
print("-" * 65)

results = {}
for name, m in models.items():
    m.fit(X_train, y_train)
    pred = m.predict(X_test)
    mae  = mean_absolute_error(y_test, pred)
    rmse = np.sqrt(mean_squared_error(y_test, pred))
    r2   = r2_score(y_test, pred)
    results[name] = {"mae": mae, "rmse": rmse, "r2": r2, "model": m}
    print(f"{name:<25} {mae:>15,.0f} {rmse:>15,.0f} {r2:>8.4f}")

# -------------------------
# SAVE BEST MODEL (untuned XGBoost)
# -------------------------
best_model = results["XGBoost"]["model"]

model_path = Path(r"C:\Users\ASUS\Desktop\prediction_model\models\best_model.pkl")
with open(model_path, "wb") as f:
    pickle.dump(best_model, f)

print(f"\n✅ XGBoost saved to: {model_path}")