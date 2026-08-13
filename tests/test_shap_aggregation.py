import pytest

from model import aggregate_transformed_shap, explain_prediction_details


def test_one_hot_location_and_facing_contributions_are_grouped():
    result = aggregate_transformed_shap(
        ["BATHROOM", "LOCATION_Bhaisepati, Lalitpur", "LOCATION_Kalanki, Kathmandu", "FACING_east", "FACING_west"],
        [5.0, -2.0, 10.0, 3.0, -1.0],
    )
    assert result == [
        {"feature": "LOCATION", "shap_value": 8.0},
        {"feature": "BATHROOM", "shap_value": 5.0},
        {"feature": "FACING", "shap_value": 2.0},
    ]


def test_grouping_preserves_total_shap_contribution():
    values = [12.5, -4.0, 1.5, 2.0]
    result = aggregate_transformed_shap(
        ["LAND AREA (sqft)", "LOCATION_A", "LOCATION_B", "FACING_east"], values,
    )
    assert sum(item["shap_value"] for item in result) == sum(values)


def test_local_explanation_reconstructs_prediction():
    features = [
        2, 3, 2, 1500, 12, 10, 1, 1, 0, 1,
        0, 2, 500, 5, 0, "Bafal, Kathmandu",
    ]
    details = explain_prediction_details(features)
    contribution_total = sum(item["shap_value"] for item in details["shap_values"])

    assert details["shap_reconstructed_value"] == pytest.approx(
        details["shap_base_value"] + contribution_total, abs=0.2
    )
    assert details["shap_additivity_error"] == pytest.approx(0, abs=1.0)
