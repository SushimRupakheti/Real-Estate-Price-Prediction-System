from pydantic import BaseModel


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
    facing_encoded: int


class PredictionOutput(BaseModel):
    predicted_price: float
    predicted_price_cr: str
from pydantic import BaseModel

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
    facing_encoded: int

class PredictionOutput(BaseModel):
    predicted_price: float
    predicted_price_cr: str