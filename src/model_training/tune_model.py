import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# -------------------------
# LOAD DATA
# -------------------------
X_train = pd.read_csv(r"C:\Users\ASUS\Desktop\prediction_model\data\processed\X_train.csv")
X_test  = pd.read_csv(r"C:\Users\ASUS\Desktop\prediction_model\data\processed\X_test.csv")
y_train = pd.read_csv(r"C:\Users\ASUS\Desktop\prediction_model\data\processed\y_train.csv").squeeze()
y_test  = pd.read_csv(r"C:\Users\ASUS\Desktop\prediction_model\data\processed\y_test.csv").squeeze()

# -------------------------
# HYPERPARAMETER GRID
# -------------------------
param_grid = {
    "n_estimators"  : [100, 200, 300],
    "learning_rate" : [0.05, 0.1, 0.2],
    "max_depth"     : [3, 4, 5],
}

gb = GradientBoostingRegressor(random_state=42)

grid_search = GridSearchCV(
    gb,
    param_grid,
    cv=5,
    scoring="r2",
    n_jobs=-1,
    verbose=1
)

print("Tuning... (this may take 2-3 minutes)")
grid_search.fit(X_train, y_train)

print("\nBest Parameters:", grid_search.best_params_)
print("Best CV R²     :", round(grid_search.best_score_, 4))

# -------------------------
# EVALUATE BEST MODEL
# -------------------------
best_model = grid_search.best_estimator_
y_pred = best_model.predict(X_test)

mae  = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2   = r2_score(y_test, y_pred)

print(f"\nTuned Model Results:")
print(f"  MAE  : {mae:,.0f}")
print(f"  RMSE : {rmse:,.0f}")
print(f"  R²   : {r2:.4f}")

from xgboost import XGBRegressor

xgb = XGBRegressor(
    n_estimators=300,
    learning_rate=0.05,
    max_depth=4,
    random_state=42,
    verbosity=0
)

xgb.fit(X_train, y_train)
y_pred_xgb = xgb.predict(X_test)

print("\nXGBoost Results:")
print(f"  MAE  : {mean_absolute_error(y_test, y_pred_xgb):,.0f}")
print(f"  RMSE : {np.sqrt(mean_squared_error(y_test, y_pred_xgb)):,.0f}")
print(f"  R²   : {r2_score(y_test, y_pred_xgb):.4f}")