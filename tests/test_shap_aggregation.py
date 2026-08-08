from model import aggregate_transformed_shap


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
