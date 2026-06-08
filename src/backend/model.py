from pathlib import Path
import pickle
import numpy as np
import shap

MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "best_model.pkl"
with MODEL_PATH.open("rb") as file_handle:
    model = pickle.load(file_handle)

# Build SHAP explainer once at startup
explainer = shap.TreeExplainer(model)

FEATURE_NAMES = [
    "FLOOR", "BEDROOM", "BATHROOM", "LAND AREA (sqft)",
    "ROAD ACCESS (ft)", "PROPERTY AGE", "HAS_PARKING",
    "HAS_BALCONY", "HAS_GARDEN", "HAS_MODULAR_KITCHEN",
    "LOCATION_ENCODED", "FACING_ENCODED",
    "AREA_PER_BEDROOM", "TOTAL_ROOMS", "IS_NEW"
]

def predict_price(features: list) -> float:
    arr = np.array(features).reshape(1, -1)
    price = model.predict(arr)[0]
    return round(float(price), 2)

def explain_prediction(features: list) -> list:
    arr = np.array(features).reshape(1, -1)
    shap_values = explainer.shap_values(arr)[0]

    # Pair feature names with their SHAP values
    explanation = []
    for name, value in zip(FEATURE_NAMES, shap_values):
        explanation.append({
            "feature": name,
            "shap_value": round(float(value), 2)
        })

    # Sort by absolute importance
    explanation.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
    return explanation