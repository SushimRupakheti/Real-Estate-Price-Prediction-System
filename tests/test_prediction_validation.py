import pytest
from pydantic import ValidationError

from schemas import HouseInput


def valid_payload():
    return {
        "floor": 2.5, "bedroom": 3, "bathroom": 2,
        "land_area": 1369, "road_access": 12, "property_age": 10,
        "has_parking": 1, "has_balcony": 0, "has_garden": 0,
        "has_modular_kitchen": 1, "location_encoded": 35000000,
        "location_label": "Kalanki, Kathmandu", "facing_encoded": 2,
    }


def test_prediction_input_rejects_zero_bedrooms():
    payload = valid_payload()
    payload["bedroom"] = 0
    with pytest.raises(ValidationError):
        HouseInput(**payload)


@pytest.mark.parametrize("field,value", [
    ("floor", 8), ("bathroom", 35), ("land_area", 6000),
    ("property_age", 101), ("facing_encoded", 8),
])
def test_prediction_input_rejects_out_of_range_values(field, value):
    payload = valid_payload()
    payload[field] = value
    with pytest.raises(ValidationError):
        HouseInput(**payload)
