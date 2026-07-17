import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from infrastructure_index.routes import router
from infrastructure_index.service import InfrastructureIndexService
import infrastructure_index.routes as index_routes


CATEGORY_NAMES = (
    "schools", "colleges", "kindergartens", "hospitals", "clinics",
    "marketplaces", "supermarkets", "banks", "bus_stops", "parks",
)


def analysis_profile(name, road_distance, major_distance, road_type, counts):
    return {
        "selected_location": {"location_name": name, "latitude": 27.7, "longitude": 85.3},
        "roads": {
            "nearest_road_distance_m": road_distance,
            "nearest_major_road_distance_m": major_distance,
            "nearest_major_road_type": road_type,
        },
        "categories": {
            category: {"deduplicated_count": counts.get(category, 0)}
            for category in CATEGORY_NAMES
        },
        "metadata": {"source": "OpenStreetMap contributors"},
    }


DENSE = analysis_profile("Dense urban", 12, 415, "primary", {
    "schools": 32, "colleges": 7, "kindergartens": 2, "hospitals": 16,
    "clinics": 11, "marketplaces": 4, "supermarkets": 2, "banks": 32,
    "bus_stops": 9, "parks": 11,
})
SUBURBAN = analysis_profile("Suburban", 60, 850, "secondary", {
    "schools": 5, "colleges": 1, "kindergartens": 1, "hospitals": 2,
    "clinics": 2, "marketplaces": 1, "supermarkets": 1, "banks": 3,
    "bus_stops": 3, "parks": 2,
})
LIMITED = analysis_profile("Less developed", 650, 2600, None, {})


def test_dense_suburban_and_limited_profiles_are_ordered_and_explained():
    service = InfrastructureIndexService()
    dense = service.calculate(DENSE)
    suburban = service.calculate(SUBURBAN)
    limited = service.calculate(LIMITED)

    assert dense["overall_score"] > suburban["overall_score"] > limited["overall_score"]
    assert set(dense["categories"]) == {
        "accessibility", "education", "healthcare", "commerce",
        "public_transport", "recreation",
    }
    education = dense["categories"]["education"]
    assert education["score"] == 96
    assert "32 mapped places" in education["reason"]
    assert education["rules_used"][0]["matched_rule"] == "At least 10 schools within 1 km"
    assert "pharmacies" in dense["categories"]["healthcare"]["description"].lower()


def test_scoring_is_deterministic_and_reproducible():
    service = InfrastructureIndexService()
    first = service.calculate(SUBURBAN)
    second = service.calculate(SUBURBAN)
    for key in ("overall_score", "classification", "categories", "weighted_contributions"):
        assert first[key] == second[key]


def test_changing_json_thresholds_changes_score_without_python_changes(tmp_path):
    source_path = InfrastructureIndexService().rules_path
    rules = json.loads(source_path.read_text(encoding="utf-8"))
    rules["categories"]["education"]["components"][0]["bands"] = [
        {"min": 100, "score": 100, "rule": "At least 100 schools within 1 km"},
        {"min": 0, "score": 0, "rule": "Fewer than 100 schools within 1 km"},
    ]
    changed_path = tmp_path / "rules.json"
    changed_path.write_text(json.dumps(rules), encoding="utf-8")

    original = InfrastructureIndexService().calculate(DENSE)
    changed = InfrastructureIndexService(changed_path).calculate(DENSE)
    assert changed["categories"]["education"]["score"] < original["categories"]["education"]["score"]
    assert changed["categories"]["education"]["rules_used"][0]["matched_rule"] == "Fewer than 100 schools within 1 km"


def test_separate_index_endpoint_accepts_coordinates(monkeypatch):
    class StubInfrastructureService:
        async def analyze(self, latitude, longitude, location_name):
            result = {**DENSE, "selected_location": {
                "location_name": location_name, "latitude": latitude, "longitude": longitude,
            }}
            return result

    monkeypatch.setattr(index_routes, "infrastructure_service", StubInfrastructureService())
    app = FastAPI(); app.include_router(router)
    response = TestClient(app).post("/infrastructure/index", json={
        "latitude": 27.7, "longitude": 85.3, "location_name": "Dense urban",
    })
    assert response.status_code == 200
    assert response.json()["metadata"]["method"] == "deterministic_json_rules"
    assert response.json()["selected_location"]["location_name"] == "Dense urban"


def test_index_endpoint_accepts_existing_analysis_without_fetching_osm(monkeypatch):
    class UnexpectedInfrastructureService:
        async def analyze(self, *args):
            raise AssertionError("Existing analysis must not trigger another OSM analysis")

    monkeypatch.setattr(index_routes, "infrastructure_service", UnexpectedInfrastructureService())
    complete = {
        **DENSE,
        "roads": {
            **DENSE["roads"], "nearest_road": None, "nearest_major_road": None,
        },
        "categories": {
            name: {
                "raw_count": item["deduplicated_count"],
                "deduplicated_count": item["deduplicated_count"],
                "radius_m": 2000 if name in {"hospitals", "clinics", "parks"} else 1000,
                "places": [],
            }
            for name, item in DENSE["categories"].items()
        },
        "amenities": {
            "schools_within_1km": 32, "hospitals_and_clinics_within_2km": 27,
            "bus_stops_within_1km": 9, "markets_within_1km": 6,
            "banks_within_1km": 32, "parks_within_2km": 11,
        },
        "connectivity": {
            "road_network_nodes_within_1km": None, "road_intersections_within_1km": None,
            "three_way_intersections_within_1km": None, "four_or_more_way_intersections_within_1km": None,
        },
        "metadata": {
            "source": "OpenStreetMap contributors", "attribution_url": "https://www.openstreetmap.org/copyright",
            "method": "current_infrastructure_context", "analysis_timestamp": "2026-07-17T00:00:00+00:00",
            "cached": False, "limitations": [],
        },
    }
    app = FastAPI(); app.include_router(router)
    response = TestClient(app).post("/infrastructure/index", json={"analysis": complete})
    assert response.status_code == 200
    assert response.json()["overall_score"] == 96


def test_index_request_rejects_missing_analysis_and_coordinates():
    app = FastAPI(); app.include_router(router)
    response = TestClient(app).post("/infrastructure/index", json={})
    assert response.status_code == 422
