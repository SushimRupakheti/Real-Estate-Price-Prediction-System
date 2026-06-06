import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np

# -------------------------
# LOAD SPLIT DATA
# -------------------------
X_train = pd.read_csv(r"C:\Users\ASUS\Desktop\prediction_model\data\processed\X_train.csv")
X_test  = pd.read_csv(r"C:\Users\ASUS\Desktop\prediction_model\data\processed\X_test.csv")
y_train = pd.read_csv(r"C:\Users\ASUS\Desktop\prediction_model\data\processed\y_train.csv").squeeze()
y_test  = pd.read_csv(r"C:\Users\ASUS\Desktop\prediction_model\data\processed\y_test.csv").squeeze()

print("Data Loaded Successfully")
print("X_train:", X_train.shape)

# -------------------------
# TRAIN MODEL
# -------------------------
model = LinearRegression()
model.fit(X_train, y_train)

print("\nModel Trained Successfully")

# -------------------------
# EVALUATE
# -------------------------
y_pred = model.predict(X_test)

mae  = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2   = r2_score(y_test, y_pred)

print(f"\nMAE  : {mae:,.0f}")
print(f"RMSE : {rmse:,.0f}")
print(f"R²   : {r2:.4f}")

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.tree import DecisionTreeRegressor

models = {
    "Linear Regression"   : LinearRegression(),
    "Decision Tree"       : DecisionTreeRegressor(random_state=42),
    "Random Forest"       : RandomForestRegressor(n_estimators=100, random_state=42),
    "Gradient Boosting"   : GradientBoostingRegressor(n_estimators=100, random_state=42),
}

print("\n--- MODEL COMPARISON ---")
for name, m in models.items():
    m.fit(X_train, y_train)
    pred = m.predict(X_test)
    mae  = mean_absolute_error(y_test, pred)
    rmse = np.sqrt(mean_squared_error(y_test, pred))
    r2   = r2_score(y_test, pred)
    print(f"\n{name}")
    print(f"  MAE  : {mae:,.0f}")
    print(f"  RMSE : {rmse:,.0f}")
    print(f"  R²   : {r2:.4f}")