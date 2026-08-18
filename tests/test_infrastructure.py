import math

import httpx
import pytest
import respx
from fastapi import FastAPI
from fastapi.testclient import TestClient

from infrastructure import osm_client
from infrastructure.config import NOMINATIM_URL, OVERPASS_URL
from infrastructure.indicators import calculate_indicators, haversine_m
from infrastructure.osm_client import NominatimClient, OSMServiceError, OverpassClient
from infrastructure.service import InfrastructureCache, InfrastructureService
import infrastructure_routes


def node(node_id, lat, lon, **tags):
    return {"type": "node", "id": node_id, "lat": lat, "lon": lon, "tags": tags}


def sample_elements():
    return [
        {"type": "way", "id": 10, "nodes": [1, 2], "tags": {"highway": "primary"},
         "geometry": [{"lat": 27.7000, "lon": 85.3000}, {"lat": 27.7080, "lon": 85.3000}]},
        {"type": "way", "id": 11, "nodes": [2, 3], "tags": {"highway": "residential"},
         "geometry": [{"lat": 27.7080, "lon": 85.3000}, {"lat": 27.7080, "lon": 85.3100}]},
        {"type": "way", "id": 12, "nodes": [2, 4], "tags": {"highway": "residential"},
         "geometry": [{"lat": 27.7080, "lon": 85.3000}, {"lat": 27.7080, "lon": 85.2900}]},
        node(20, 27.7005, 85.3000, amenity="school", name="Test School"),
        node(21, 27.7010, 85.3000, amenity="hospital", name="Test Hospital"),
        node(22, 27.7005, 85.3000, highway="bus_stop", name="Test Bus Stop"),
        node(23, 27.7005, 85.3000, shop="supermarket", name="Test Supermarket"),
        node(24, 27.7005, 85.3000, amenity="bank", name="Test Bank"),
        node(25, 27.7010, 85.3000, leisure="park", name="Test Park"),
    ]


def test_invalid_latitude_and_longitude():
    app = FastAPI(); app.include_router(infrastructure_routes.router)
    client = TestClient(app)
    assert client.post("/infrastructure/analyze", json={"latitude": 91, "longitude": 85}).status_code == 422
    assert client.post("/infrastructure/analyze", json={"latitude": 27, "longitude": 181}).status_code == 422
    assert client.post("/infrastructure/analyze", json={"latitude": "NaN", "longitude": 85}).status_code == 422


@pytest.mark.asyncio
async def test_successful_response_and_cached_response(tmp_path):
    class StubClient:
        calls = 0
        async def fetch_elements(self, latitude, longitude):
            self.calls += 1; return sample_elements()
    stub = StubClient()
    service = InfrastructureService(stub, InfrastructureCache(tmp_path / "cache.db"))
    first = await service.analyze(27.7, 85.3, "Test")
    second = await service.analyze(27.7, 85.3, "Test")
    assert first["amenities"]["schools_within_1km"] == 1
    assert first["roads"]["nearest_major_road_type"] == "primary"
    assert second["metadata"]["cached"] is True
    assert stub.calls == 1


@pytest.mark.asyncio
async def test_expired_cache_is_used_when_overpass_is_unavailable(tmp_path):
    class StubClient:
        fail = False
        async def fetch_elements(self, latitude, longitude):
            if self.fail: raise OSMServiceError("OpenStreetMap infrastructure service is temporarily unavailable.")
            return sample_elements()
    stub = StubClient(); cache = InfrastructureCache(tmp_path / "cache.db")
    service = InfrastructureService(stub, cache)
    await service.analyze(27.7, 85.3, "Test")
    with cache._connect() as connection:
        connection.execute("UPDATE infrastructure_cache SET expires_at = ?", ("2000-01-01T00:00:00+00:00",))
    stub.fail = True
    result = await service.analyze(27.7, 85.3, "Test")
    assert result["metadata"]["cached"] is True
    assert result["metadata"]["stale"] is True
    assert result["amenities"]["schools_within_1km"] == 1


def test_coordinate_rounding(tmp_path):
    cache = InfrastructureCache(tmp_path / "cache.db")
    assert cache.cache_key(27.70001, 85.30001) == cache.cache_key(27.70004, 85.30004)
    assert cache.cache_key(27.70001, 85.30001) != cache.cache_key(27.70016, 85.30016)


def test_distance_calculation_and_counts_deduplicate():
    elements = sample_elements() + [sample_elements()[2]]
    result = calculate_indicators(elements, 27.7, 85.3)
    assert haversine_m(27.7, 85.3, 27.7, 85.3) == 0
    assert result["roads"]["nearest_road_distance_m"] == 0
    assert result["amenities"] == {
        "schools_within_1km": 1, "hospitals_and_clinics_within_2km": 1,
        "bus_stops_within_1km": 1, "markets_within_1km": 1,
        "banks_within_1km": 1, "parks_within_2km": 1,
    }
    assert result["connectivity"]["road_intersections_within_1km"] is None


def test_tertiary_road_is_not_classified_as_major():
    elements = [
        {"type": "way", "id": 301, "tags": {"highway": "tertiary"},
         "geometry": [{"lat": 27.7, "lon": 85.3001}, {"lat": 27.71, "lon": 85.3001}]},
        {"type": "way", "id": 302, "tags": {"highway": "secondary"},
         "geometry": [{"lat": 27.7, "lon": 85.301}, {"lat": 27.71, "lon": 85.301}]},
    ]
    result = calculate_indicators(elements, 27.7, 85.3)
    assert result["roads"]["nearest_road_distance_m"] < result["roads"]["nearest_major_road_distance_m"]
    assert result["roads"]["nearest_major_road_type"] == "secondary"


def test_empty_and_incomplete_elements_return_missing_indicators():
    for elements in ([], [{"type": "node", "id": 1, "tags": {"amenity": "school"}}]):
        result = calculate_indicators(elements, 27.7, 85.3)
        assert result["roads"]["nearest_road_distance_m"] is None
        assert result["roads"]["nearest_major_road_distance_m"] is None
        assert result["roads"]["nearest_major_road_type"] is None
        assert result["connectivity"]["road_intersections_within_1km"] is None


def test_narrow_tags_deduplication_and_radius_rules():
    elements = [
        node(100, 27.7002, 85.3000, amenity="school", name="Shree School", wikidata="Q1"),
        {"type": "way", "id": 101, "center": {"lat": 27.70021, "lon": 85.30001},
         "tags": {"amenity": "school", "name": "Shree School", "wikidata": "Q1"}},
        {"type": "way", "id": 102, "center": {"lat": 27.70022, "lon": 85.30002},
         "tags": {"building": "school"}},
        {"type": "way", "id": 107, "center": {"lat": 27.7002, "lon": 85.3000},
         "geometry": [{"lat": 27.699, "lon": 85.299}, {"lat": 27.699, "lon": 85.301},
                      {"lat": 27.701, "lon": 85.301}, {"lat": 27.701, "lon": 85.299},
                      {"lat": 27.699, "lon": 85.299}],
         "tags": {"amenity": "school", "name": "School Main Building"}},
        node(103, 27.7003, 85.3000, amenity="pharmacy", name="Pharmacy"),
        node(104, 27.7003, 85.3000, amenity="atm", name="ATM"),
        node(105, 27.7003, 85.3000, shop="convenience", name="Shop"),
        node(106, 27.7200, 85.3000, amenity="school", name="Outside School"),
    ]
    result = calculate_indicators(elements, 27.7, 85.3, include_debug=True)
    school_result = result["categories"]["schools"]
    assert {key: school_result[key] for key in ("raw_count", "deduplicated_count", "radius_m")} == {"raw_count": 3, "deduplicated_count": 1, "radius_m": 1000}
    assert len(school_result["places"]) == school_result["deduplicated_count"]
    assert result["categories"]["hospitals"]["deduplicated_count"] == 0
    assert result["categories"]["banks"]["deduplicated_count"] == 0
    assert result["categories"]["marketplaces"]["deduplicated_count"] == 0


def test_unnamed_places_are_excluded_from_facility_counts():
    elements = [
        node(200, 27.7001, 85.3000, amenity="bank"),
        node(201, 27.70011, 85.3000, amenity="bank"),
        {"type": "way", "id": 202, "center": {"lat": 27.7001, "lon": 85.3000}, "tags": {"amenity": "bank"}},
        node(203, 27.7010, 85.3000, amenity="bank", name="Nepal Bank"),
        node(204, 27.7060, 85.3000, amenity="bank", name="Nepal Bank"),
    ]
    result = calculate_indicators(elements, 27.7, 85.3)
    assert result["categories"]["banks"]["raw_count"] == 2
    assert result["categories"]["banks"]["deduplicated_count"] == 2


def test_place_lists_are_sorted_and_exclude_unnamed_facilities():
    elements = [
        node(401, 27.7005, 85.3, amenity="school", name="Farther School"),
        node(402, 27.7001, 85.3, amenity="school"),
    ]
    places = calculate_indicators(elements, 27.7, 85.3)["categories"]["schools"]["places"]
    assert len(places) == 1
    assert places[0]["name"] == "Farther School"
    assert [place["distance_m"] for place in places] == sorted(place["distance_m"] for place in places)
    assert places[0]["osm_id"] == 401 and places[0]["osm_type"] == "node"
    assert places[0]["tags"] == {"amenity": "school"}


def test_name_aliases_acronyms_and_localized_names_are_deduplicated():
    elements = [
        node(601, 27.7001, 85.3, amenity="school", name="Basundhara National Academy"),
        node(602, 27.7002, 85.3, amenity="school", name="BN Academy"),
        node(603, 27.7003, 85.3, amenity="school", name="बसुन्धरा नेशनल एकेडेमी", **{"name:en": "Basundhara National Academy"}),
    ]
    schools = calculate_indicators(elements, 27.7, 85.3)["categories"]["schools"]
    assert schools["raw_count"] == 3
    assert schools["deduplicated_count"] == 1
    assert schools["places"][0]["name"] == "Basundhara National Academy"


def test_named_road_details_are_returned():
    element = {"type": "way", "id": 501, "tags": {"highway": "primary", "name": "Ring Road"},
               "geometry": [{"lat": 27.7, "lon": 85.3}, {"lat": 27.71, "lon": 85.3}]}
    roads = calculate_indicators([element], 27.7, 85.3)["roads"]
    assert roads["nearest_road"]["name"] == "Ring Road"
    assert roads["nearest_major_road"]["highway_classification"] == "primary"
    assert roads["nearest_road"]["tags"] == {"highway": "primary", "name": "Ring Road"}


@pytest.mark.asyncio
@respx.mock
async def test_overpass_timeout(monkeypatch):
    monkeypatch.setattr(osm_client, "RETRY_BACKOFF_SECONDS", 0)
    monkeypatch.setattr(osm_client, "OVERPASS_URLS", (OVERPASS_URL,))
    respx.post(OVERPASS_URL).mock(side_effect=httpx.ReadTimeout("timeout"))
    with pytest.raises(OSMServiceError, match="temporarily unavailable"):
        await OverpassClient().fetch_elements(27.7, 85.3)


@pytest.mark.asyncio
@respx.mock
async def test_overpass_server_error(monkeypatch):
    monkeypatch.setattr(osm_client, "RETRY_BACKOFF_SECONDS", 0)
    monkeypatch.setattr(osm_client, "OVERPASS_URLS", (OVERPASS_URL,))
    respx.post(OVERPASS_URL).mock(return_value=httpx.Response(500))
    with pytest.raises(OSMServiceError, match="temporarily unavailable"):
        await OverpassClient().fetch_elements(27.7, 85.3)


@pytest.mark.asyncio
@respx.mock
async def test_nominatim_geocoding_and_cache():
    route = respx.get(NOMINATIM_URL).mock(return_value=httpx.Response(200, json=[{
        "lat": "27.693", "lon": "85.281", "display_name": "Kalanki, Kathmandu, Nepal"
    }]))
    client = NominatimClient()
    first = await client.geocode("Kalanki, Kathmandu")
    second = await client.geocode("kalanki, kathmandu")
    assert first["latitude"] == 27.693 and first["longitude"] == 85.281
    assert second["latitude"] == 27.693
    assert route.call_count == 1


@pytest.mark.asyncio
async def test_route_returns_503_for_osm_failure(monkeypatch):
    class FailingService:
        async def analyze(self, *args): raise OSMServiceError("OSM unavailable")
    monkeypatch.setattr(infrastructure_routes, "service", FailingService())
    app = FastAPI(); app.include_router(infrastructure_routes.router)
    response = TestClient(app).post("/infrastructure/analyze", json={"latitude": 27.7, "longitude": 85.3})
    assert response.status_code == 503
    assert response.json()["detail"] == "OSM unavailable"
