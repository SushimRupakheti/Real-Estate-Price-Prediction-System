from pathlib import Path
import pickle

import numpy as np


MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "gradient_boosting_model.pkl"

with MODEL_PATH.open("rb") as file_handle:
    model = pickle.load(file_handle)


def predict_price(features: list) -> float:
    features = np.array(features).reshape(1, -1)
    price = model.predict(features)[0]
    return round(float(price), 2)
import pickle
import numpy as np

MODEL_PATH = r"C:\Users\ASUS\Desktop\prediction_model\models\gradient_boosting_model.pkl"

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

def predict_price(features: list) -> float:
    features = np.array(features).reshape(1, -1)
    price = model.predict(features)[0]
    return round(float(price), 2)