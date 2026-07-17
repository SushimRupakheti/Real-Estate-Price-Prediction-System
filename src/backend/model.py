"""Load and serve the fitted preprocessing/model pipeline."""
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import shap

ROOT = Path(__file__).resolve().parents[2]
# The runtime scikit-learn version is pinned to the artifact's training version
# in requirements.txt; sklearn model persistence is not cross-version stable.
MODEL_PATH = ROOT / "models" / "best_model.joblib"
model = joblib.load(MODEL_PATH)
preprocessing = model.named_steps["preprocessing"]
estimator = model.named_steps["estimator"]
FEATURE_NAMES = preprocessing.get_feature_names_out().tolist()
try:
    explainer = shap.TreeExplainer(estimator)
except Exception:
    background = preprocessing.transform(pd.read_csv(ROOT / "data" / "processed" / "X_train.csv")).astype(float)
    explainer = shap.LinearExplainer(estimator, background)

FACING_BY_CODE = {0: "south-east", 1: "south-west", 2: "east", 3: "north",
                  4: "north-east", 5: "north-west", 6: "south", 7: "west"}

def make_frame(features: list) -> pd.DataFrame:
    (floor, bedroom, bathroom, land_area, road_access, property_age,
     has_parking, has_balcony, has_garden, has_modular_kitchen,
     _legacy_location_encoded, facing_encoded, area_per_bedroom,
     total_rooms, is_new, *rest) = features
    location = rest[0] if rest and rest[0] else "unknown"
    return pd.DataFrame([{
      "LOCATION": location, "FACING": FACING_BY_CODE.get(int(facing_encoded), "unknown"),
      "FLOOR": floor, "BEDROOM": bedroom, "BATHROOM": bathroom,
      "LAND AREA (sqft)": land_area, "ROAD ACCESS (ft)": road_access,
      "PROPERTY AGE": property_age, "HAS_PARKING": has_parking,
      "HAS_BALCONY": has_balcony, "HAS_GARDEN": has_garden,
      "HAS_MODULAR_KITCHEN": has_modular_kitchen,
      "AREA_PER_BEDROOM": area_per_bedroom, "TOTAL_ROOMS": total_rooms, "IS_NEW": is_new,
    }])

def predict_price(features: list) -> float:
    return round(float(model.predict(make_frame(features))[0]), 2)

def explain_prediction(features: list) -> list:
    transformed = preprocessing.transform(make_frame(features))
    values = np.asarray(explainer.shap_values(transformed))
    if values.ndim > 1: values = values[0]
    explanation = [{"feature": name, "shap_value": round(float(value), 2)}
                   for name, value in zip(FEATURE_NAMES, values)]
    explanation.sort(key=lambda item: abs(item["shap_value"]), reverse=True)
    return explanation

def global_feature_importance(raw_features: pd.DataFrame) -> list:
    """Return mean absolute SHAP impact for the fitted pipeline features."""
    transformed = preprocessing.transform(raw_features)
    values = np.asarray(explainer.shap_values(transformed))
    if values.ndim == 3:
        values = values[..., 0]
    mean_abs = np.abs(values).mean(axis=0)
    return sorted(
        ({"feature": name, "importance": round(float(value), 2)}
         for name, value in zip(FEATURE_NAMES, mean_abs)),
        key=lambda item: item["importance"], reverse=True,
    )
