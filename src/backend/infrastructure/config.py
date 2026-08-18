from pathlib import Path

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_URLS = (OVERPASS_URL, "https://overpass.kumi.systems/api/interpreter")
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "NepalHousePredictor-Infrastructure/1.0 (academic project)"
REQUEST_TIMEOUT_SECONDS = 25.0
RETRY_COUNT = 2
RETRY_BACKOFF_SECONDS = 0.5
CACHE_DURATION_SECONDS = 24 * 60 * 60
COORDINATE_DECIMALS = 4  # About 11 m latitude and 10 m longitude in Nepal.
CONFIGURATION_VERSION = "phase1-v7-clean-place-names"
CACHE_PATH = Path(__file__).resolve().parents[1] / "infrastructure_cache.db"

RADII_METERS = {
    "road": 1_000,
    "major_road": 2_000,
    "school": 1_000,
    "healthcare": 2_000,
    "bus_stop": 1_000,
    "market": 1_000,
    "bank": 1_000,
    "park": 2_000,
    "intersection": 1_000,
}
MAX_QUERY_RADIUS_METERS = max(RADII_METERS.values())
MAJOR_ROAD_TYPES = {"motorway", "trunk", "primary", "secondary"}
PLACE_NAME_DEDUP_DISTANCE_M = 150
UNNAMED_CROSS_TYPE_DEDUP_DISTANCE_M = 5
