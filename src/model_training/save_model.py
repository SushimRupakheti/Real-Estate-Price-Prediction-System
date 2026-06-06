import pandas as pd
import pickle
from sklearn.ensemble import GradientBoostingRegressor

# -------------------------
# LOAD DATA
# -------------------------
X_train = pd.read_csv(r"C:\Users\ASUS\Desktop\prediction_model\data\processed\X_train.csv")
X_test  = pd.read_csv(r"C:\Users\ASUS\Desktop\prediction_model\data\processed\X_test.csv")
y_train = pd.read_csv(r"C:\Users\ASUS\Desktop\prediction_model\data\processed\y_train.csv").squeeze()
y_test  = pd.read_csv(r"C:\Users\ASUS\Desktop\prediction_model\data\processed\y_test.csv").squeeze()

# -------------------------
# TRAIN BEST MODEL
# -------------------------
model = GradientBoostingRegressor(
    learning_rate=0.05,
    max_depth=3,
    n_estimators=200,
    random_state=42
)

model.fit(X_train, y_train)
print("Model Trained Successfully")

# -------------------------
# SAVE MODEL
# -------------------------
model_path = r"C:\Users\ASUS\Desktop\prediction_model\models\gradient_boosting_model.pkl"

with open(model_path, "wb") as f:
    pickle.dump(model, f)

print(f"Model Saved to: {model_path}")

# -------------------------
# VERIFY
# -------------------------
with open(model_path, "rb") as f:
    loaded_model = pickle.load(f)

print("Model Loaded Back Successfully")
print("Feature count:", len(X_train.columns))
print("Features:", X_train.columns.tolist())