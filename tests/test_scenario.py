import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from scenario.config import ScenarioConfigurationError, load_scenario_rules
from scenario.rules import ScenarioValidationError
from scenario.service import ScenarioService
from scenario_routes import router


CURRENT = {
    "nearest_road_distance_m": 60,
    "nearest_major_road_distance_m": 850,
    "nearest_major_road_type": "secondary",
    "schools": 5, "colleges": 1, "kindergartens": 1,
    "hospitals": 2, "clinics": 2, "bus_stops": 3,
    "marketplaces": 1, "supermarkets": 1, "banks": 3, "parks": 2,
}


def request(changes=None, price=40_000_000):
    return {"baseline_price": price, "current_infrastructure": dict(CURRENT), "changes": changes or []}


def test_empty_scenario_has_no_index_change_and_preserves_current_data():
    original = request()
    result = ScenarioService().simulate(original)
    assert result["scenario"]["index_change"] == 0
    assert result["current"]["infrastructure"] == result["scenario"]["infrastructure"]
    assert original["current_infrastructure"] == CURRENT
    assert result["value_shift"]["classification"] == "Minimal Change"


def test_one_new_facility_and_multiple_changes_are_applied_to_copy():
    one = ScenarioService().simulate(request([{"type": "new_hospital", "quantity": 1}]))
    assert one["current"]["infrastructure"]["hospitals"] == 2
    assert one["scenario"]["infrastructure"]["hospitals"] == 3
    assert one["scenario"]["category_scores"]["healthcare"] > one["current"]["category_scores"]["healthcare"]

    multiple = ScenarioService().simulate(request([
        {"type": "new_school", "quantity": 2},
        {"type": "new_bus_stop", "quantity": 2},
        {"type": "new_park", "quantity": 1},
    ]))
    assert multiple["scenario"]["infrastructure"]["schools"] == 7
    assert multiple["scenario"]["infrastructure"]["bus_stops"] == 5
    assert len(multiple["rule_contributions"]) == 3


def test_road_distance_improvement_and_classification_upgrade():
    result = ScenarioService().simulate(request([
        {"type": "major_road_distance", "new_distance_m": 180},
        {"type": "road_upgrade", "new_road_type": "primary"},
    ]))
    assert result["scenario"]["infrastructure"]["nearest_major_road_distance_m"] == 180
    assert result["scenario"]["infrastructure"]["nearest_major_road_type"] == "primary"
    assert result["scenario"]["category_scores"]["accessibility"] > result["current"]["category_scores"]["accessibility"]
    assert {item["category"] for item in result["rule_contributions"]} >= {"accessibility", "public_transport"}


@pytest.mark.parametrize("changes, message", [
    ([{"type": "unknown_change", "quantity": 1}], "Unsupported scenario type"),
    ([{"type": "new_hospital", "quantity": 4}], "maximum"),
    ([{"type": "new_hospital", "quantity": -1}], "negative"),
    ([{"type": "major_road_distance", "new_distance_m": 900}], "closer"),
    ([{"type": "road_upgrade", "new_road_type": "residential"}], "not an upgrade"),
])
def test_invalid_scenarios_are_rejected(changes, message):
    with pytest.raises(ScenarioValidationError, match=message):
        ScenarioService().simulate(request(changes))


def test_duplicate_facility_entries_cannot_bypass_cap():
    with pytest.raises(ScenarioValidationError, match="total quantity"):
        ScenarioService().simulate(request([
            {"type": "new_hospital", "quantity": 2},
            {"type": "new_hospital", "quantity": 2},
        ]))


def test_positive_negative_and_no_change_value_rules_and_price_range():
    service = ScenarioService(); rules = load_scenario_rules()
    minimal = service.calculate_value_shift(40_000_000, 0, rules)
    positive = service.calculate_value_shift(40_000_000, 7, rules)
    negative = service.calculate_value_shift(40_000_000, -6, rules)
    assert minimal["minimum_percent"] == 0
    assert positive["minimum_value"] == 41_200_000
    assert positive["maximum_value"] == 42_800_000
    assert negative["minimum_percent"] == -8
    assert negative["maximum_value"] == 38_800_000
    assert positive["is_forecast"] is False and positive["statistically_validated"] is False


def test_score_caps_floor_and_ceiling():
    service = ScenarioService(); rules = load_scenario_rules()
    assert service._clamp_score(140, rules) == 100
    assert service._clamp_score(-20, rules) == 0


def test_output_is_deterministic_except_generation_timestamp():
    service = ScenarioService()
    first = service.simulate(request([{"type": "new_hospital", "quantity": 1}]))
    second = service.simulate(request([{"type": "new_hospital", "quantity": 1}]))
    first["metadata"].pop("generated_at"); second["metadata"].pop("generated_at")
    assert first == second


def test_rule_loading_and_invalid_configuration(tmp_path):
    assert load_scenario_rules()["version"] == "1.0.0"
    invalid = tmp_path / "scenario.json"
    invalid.write_text(json.dumps({"version": "bad"}), encoding="utf-8")
    with pytest.raises(ScenarioConfigurationError, match="missing"):
        load_scenario_rules(invalid)


def test_disclaimer_and_separate_endpoint_are_present():
    result = ScenarioService().simulate(request())
    assert "not a statistically trained future-price forecast" in result["metadata"]["disclaimer"]
    app = FastAPI(); app.include_router(router)
    response = TestClient(app).post("/scenarios/simulate", json=request([
        {"type": "new_bus_stop", "quantity": 2},
    ]))
    assert response.status_code == 200
    assert response.json()["value_shift"]["method"] == "rule_based_infrastructure_scenario"


def test_endpoint_rejects_nan_infinity_and_negative_current_counts():
    app = FastAPI(); app.include_router(router); client = TestClient(app)
    bad_count = request(); bad_count["current_infrastructure"]["schools"] = -1
    assert client.post("/scenarios/simulate", json=bad_count).status_code == 422
    bad_price = request(); bad_price["baseline_price"] = "NaN"
    assert client.post("/scenarios/simulate", json=bad_price).status_code == 422
