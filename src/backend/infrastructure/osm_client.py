import asyncio

import httpx

from .config import (
    NOMINATIM_URL, OVERPASS_URLS, REQUEST_TIMEOUT_SECONDS,
    RETRY_BACKOFF_SECONDS, RETRY_COUNT, USER_AGENT,
)


class OSMServiceError(RuntimeError):
    """Raised when Overpass cannot provide a usable response."""


def build_overpass_query(latitude: float, longitude: float) -> str:
    def point(radius): return f"{radius},{latitude:.7f},{longitude:.7f}"
    return f"""[out:json][timeout:20];
(
  way(around:{point(1000)})[highway];
  way(around:{point(2000)})[highway~\"^(motorway|trunk|primary|secondary)$\"];
  nwr(around:{point(1000)})[amenity~\"^(school|college|kindergarten|marketplace|bank)$\"];
  nwr(around:{point(2000)})[amenity~\"^(hospital|clinic)$\"];
  nwr(around:{point(2000)})[healthcare~\"^(hospital|clinic)$\"];
  nwr(around:{point(1000)})[highway=bus_stop];
  nwr(around:{point(1000)})[public_transport=platform][bus=yes];
  nwr(around:{point(1000)})[shop=supermarket];
  nwr(around:{point(2000)})[leisure=park];
);
out center geom;"""


class OverpassClient:
    def __init__(self, client: httpx.AsyncClient | None = None):
        self._client = client

    async def fetch_elements(self, latitude: float, longitude: float) -> list[dict]:
        query = build_overpass_query(latitude, longitude)
        headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS)
        try:
            for attempt in range(RETRY_COUNT + 1):
                try:
                    endpoint = OVERPASS_URLS[attempt % len(OVERPASS_URLS)]
                    response = await client.post(endpoint, content=query, headers=headers)
                    response.raise_for_status()
                    payload = response.json()
                    elements = payload.get("elements")
                    if not isinstance(elements, list):
                        raise OSMServiceError("Overpass returned an invalid response format.")
                    return elements
                except (httpx.TimeoutException, httpx.HTTPError, ValueError) as exc:
                    if attempt == RETRY_COUNT:
                        raise OSMServiceError(
                            "OpenStreetMap infrastructure service is temporarily unavailable."
                        ) from exc
                    await asyncio.sleep(RETRY_BACKOFF_SECONDS * (attempt + 1))
        finally:
            if owns_client:
                await client.aclose()


class NominatimClient:
    def __init__(self):
        self._cache = {}

    async def geocode(self, location_name: str) -> dict:
        cache_key = location_name.casefold().strip()
        if cache_key in self._cache:
            return self._cache[cache_key].copy()
        params = {"q": f"{location_name}, Nepal", "format": "jsonv2", "limit": 1, "countrycodes": "np"}
        headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
                response = await client.get(NOMINATIM_URL, params=params, headers=headers)
                response.raise_for_status()
                results = response.json()
        except (httpx.TimeoutException, httpx.HTTPError, ValueError) as exc:
            raise OSMServiceError("OpenStreetMap geocoding is temporarily unavailable.") from exc
        if not isinstance(results, list) or not results:
            raise OSMServiceError(f"Location '{location_name}' could not be resolved in Nepal.")
        result = {
            "location_name": location_name,
            "latitude": float(results[0]["lat"]),
            "longitude": float(results[0]["lon"]),
            "display_name": results[0].get("display_name"),
        }
        self._cache[cache_key] = result
        return result.copy()
