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
TRAINING_FRAME = pd.read_csv(ROOT / "data" / "processed" / "X_train.csv")
TRAINING_LOCATIONS = TRAINING_FRAME["LOCATION"].dropna().astype(str)
LOCATION_COUNTS = TRAINING_LOCATIONS.value_counts().to_dict()
MODELED_LOCATIONS = sorted(LOCATION_COUNTS)
try:
    explainer = shap.TreeExplainer(estimator)
except Exception:
    background = preprocessing.transform(pd.read_csv(ROOT / "data" / "processed" / "X_train.csv")).astype(float)
    explainer = shap.LinearExplainer(estimator, background)

FACING_BY_CODE = {0: "south-east", 1: "south-west", 2: "east", 3: "north",
                  4: "north-east", 5: "north-west", 6: "south", 7: "west"}

def aggregate_transformed_shap(feature_names, values) -> list:
    """Group one-hot SHAP columns back into their original input features."""
    grouped = {}
    for name, value in zip(feature_names, values):
        if name.startswith("LOCATION_"):
            original_name = "LOCATION"
        elif name.startswith("FACING_"):
            original_name = "FACING"
        else:
            original_name = name
        grouped[original_name] = grouped.get(original_name, 0.0) + float(value)
    explanation = [{"feature": name, "shap_value": round(value, 2)}
                   for name, value in grouped.items()]
    explanation.sort(key=lambda item: abs(item["shap_value"]), reverse=True)
    return explanation

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
    return aggregate_transformed_shap(FEATURE_NAMES, values)

def explain_prediction_details(features: list) -> dict:
    """Return an additive, auditable local explanation in model output units."""
    frame = make_frame(features)
    transformed = preprocessing.transform(frame)
    values = np.asarray(explainer.shap_values(transformed))
    if values.ndim > 1:
        values = values[0]

    base_value = float(np.asarray(explainer.expected_value).reshape(-1)[0])
    prediction = float(model.predict(frame)[0])
    reconstructed = base_value + float(values.sum())
    return {
        "shap_values": aggregate_transformed_shap(FEATURE_NAMES, values),
        "shap_base_value": round(base_value, 2),
        "shap_reconstructed_value": round(reconstructed, 2),
        "shap_additivity_error": round(prediction - reconstructed, 2),
    }

def explain_location_effect(features: list) -> dict:
    """Compare the same property across every location learned by the model."""
    frame = make_frame(features)
    selected_location = str(frame.iloc[0]["LOCATION"])
    comparison = pd.concat([frame] * len(MODELED_LOCATIONS), ignore_index=True)
    comparison["LOCATION"] = MODELED_LOCATIONS
    predictions = np.asarray(model.predict(comparison), dtype=float)
    selected_prediction = float(model.predict(frame)[0])
    median_prediction = float(np.median(predictions))
    difference = selected_prediction - median_prediction
    percentile = float((predictions <= selected_prediction).mean() * 100)
    sample_count = int(LOCATION_COUNTS.get(selected_location, 0))
    confidence = "high" if sample_count >= 20 else "medium" if sample_count >= 8 else "low"
    difference_percent = 0.0 if median_prediction == 0 else difference / median_prediction * 100
    effect = "premium" if difference_percent >= 1 else "discount" if difference_percent <= -1 else "neutral"
    return {
        "location": selected_location,
        "effect": effect,
        "difference": round(difference, 2),
        "difference_percent": round(difference_percent, 2),
        "percentile": round(percentile, 1),
        "reference_price": round(median_prediction, 2),
        "sample_count": sample_count,
        "confidence": confidence,
        "locations_compared": len(MODELED_LOCATIONS),
    }

def global_feature_importance(raw_features: pd.DataFrame) -> list:
    """Return mean absolute SHAP impact for the fitted pipeline features."""
    transformed = preprocessing.transform(raw_features)
    values = np.asarray(explainer.shap_values(transformed))
    if values.ndim == 3:
        values = values[..., 0]
    mean_abs = np.abs(values).mean(axis=0)
    grouped = {}
    for name, value in zip(FEATURE_NAMES, mean_abs):
        original_name = "LOCATION" if name.startswith("LOCATION_") else "FACING" if name.startswith("FACING_") else name
        grouped[original_name] = grouped.get(original_name, 0.0) + float(value)
    return sorted(
        ({"feature": name, "importance": round(value, 2)} for name, value in grouped.items()),
        key=lambda item: item["importance"], reverse=True,
    )
