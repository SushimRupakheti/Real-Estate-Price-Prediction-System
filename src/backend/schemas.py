from pydantic import BaseModel, Field
from typing import List, Any

class HouseInput(BaseModel):
    floor: float = Field(ge=1, le=7)
    bedroom: float = Field(ge=1, le=36)
    bathroom: float = Field(ge=1, le=34)
    land_area: float = Field(ge=102.675, le=5886.7)
    road_access: float = Field(ge=0, le=40)
    property_age: float = Field(ge=0, le=100)
    has_parking: int = Field(ge=0, le=1)
    has_balcony: int = Field(ge=0, le=1)
    has_garden: int = Field(ge=0, le=1)
    has_modular_kitchen: int = Field(ge=0, le=1)
    location_encoded: float
    location_label: str | None = None
    facing_encoded: int = Field(ge=0, le=7)

class ShapFeature(BaseModel):
    feature: str
    shap_value: float

class PredictionOutput(BaseModel):
    predicted_price: float
    predicted_price_cr: str
    shap_values: List[ShapFeature]
    base_price: float
    macro_adjustment: dict[str, Any] | None = None
    macro_data_available: bool = False
