from pydantic import BaseModel
from typing import List

class HouseInput(BaseModel):
    floor: float
    bedroom: float
    bathroom: float
    land_area: float
    road_access: float
    property_age: float
    has_parking: int
    has_balcony: int
    has_garden: int
    has_modular_kitchen: int
    location_encoded: float
    location_label: str | None = None
    facing_encoded: int

class ShapFeature(BaseModel):
    feature: str
    shap_value: float

class PredictionOutput(BaseModel):
    predicted_price: float
    predicted_price_cr: str
    shap_values: List[ShapFeature]