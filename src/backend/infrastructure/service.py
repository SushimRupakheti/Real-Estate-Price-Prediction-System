import json
import sqlite3
from datetime import datetime, timedelta, timezone

from .config import (
    CACHE_DURATION_SECONDS, CACHE_PATH, CONFIGURATION_VERSION, COORDINATE_DECIMALS,
)
from .indicators import calculate_indicators
from .osm_client import OverpassClient, OSMServiceError


class InfrastructureCache:
    def __init__(self, path=CACHE_PATH):
        self.path = path
        self._initialize()

    def _connect(self):
        return sqlite3.connect(self.path)

    def _initialize(self):
        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS infrastructure_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    cache_key TEXT NOT NULL UNIQUE,
                    response_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    configuration_version TEXT NOT NULL
                )
            """)

    @staticmethod
    def cache_key(latitude: float, longitude: float) -> str:
        return f"{round(latitude, COORDINATE_DECIMALS):.{COORDINATE_DECIMALS}f}:" \
               f"{round(longitude, COORDINATE_DECIMALS):.{COORDINATE_DECIMALS}f}:" \
               f"{CONFIGURATION_VERSION}"

    def get(self, latitude: float, longitude: float):
        key = self.cache_key(latitude, longitude)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT response_json, expires_at FROM infrastructure_cache WHERE cache_key = ?", (key,)
            ).fetchone()
        if not row or datetime.fromisoformat(row[1]) <= datetime.now(timezone.utc):
            return None
        return json.loads(row[0])

    def get_stale(self, latitude: float, longitude: float):
        """Return the last successful response even after expiry for outage fallback."""
        key = self.cache_key(latitude, longitude)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT response_json, expires_at FROM infrastructure_cache WHERE cache_key = ?", (key,)
            ).fetchone()
        if not row:
            return None
        response = json.loads(row[0])
        response["metadata"]["cache_expired_at"] = row[1]
        return response

    def set(self, latitude: float, longitude: float, response: dict):
        now = datetime.now(timezone.utc)
        expires = now + timedelta(seconds=CACHE_DURATION_SECONDS)
        key = self.cache_key(latitude, longitude)
        with self._connect() as connection:
            connection.execute("""
                INSERT INTO infrastructure_cache
                (latitude, longitude, cache_key, response_json, created_at, expires_at, configuration_version)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                  response_json=excluded.response_json, created_at=excluded.created_at,
                  expires_at=excluded.expires_at, configuration_version=excluded.configuration_version
            """, (round(latitude, COORDINATE_DECIMALS), round(longitude, COORDINATE_DECIMALS), key,
                  json.dumps(response), now.isoformat(), expires.isoformat(), CONFIGURATION_VERSION))


class InfrastructureService:
    def __init__(self, client=None, cache=None):
        self.client = client or OverpassClient()
        self.cache = cache or InfrastructureCache()

    async def analyze(self, latitude: float, longitude: float, location_name: str | None = None):
        cached = self.cache.get(latitude, longitude)
        if cached is not None:
            cached["selected_location"]["location_name"] = location_name
            cached["metadata"]["cached"] = True
            return cached

        try:
            elements = await self.client.fetch_elements(latitude, longitude)
        except OSMServiceError:
            stale = self.cache.get_stale(latitude, longitude)
            if stale is None:
                raise
            stale["selected_location"]["location_name"] = location_name
            stale["metadata"]["cached"] = True
            stale["metadata"]["stale"] = True
            stale["metadata"]["limitations"].append(
                "The live Overpass provider was unavailable, so this response uses the last successful cached analysis."
            )
            return stale
        indicators = calculate_indicators(elements, latitude, longitude)
        response = {
            "selected_location": {"location_name": location_name, "latitude": latitude, "longitude": longitude},
            **indicators,
            "metadata": {
                "source": "OpenStreetMap contributors",
                "attribution_url": "https://www.openstreetmap.org/copyright",
                "method": "current_infrastructure_context",
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "cached": False,
                "stale": False,
                "limitations": [
                    "OpenStreetMap coverage and tag completeness vary by location.",
                    "Distances use mapped geometry and are approximate, not travel times.",
                    "Facility distances are straight-line distances to the mapped feature centre.",
                    "Road distances use the nearest mapped road geometry boundary.",
                    "Intersection indicators are null because lightweight Overpass geometry is not a validated road graph.",
                    "This analysis is not a price forecast or infrastructure score.",
                ],
            },
        }
        self.cache.set(latitude, longitude, response)
        return response
