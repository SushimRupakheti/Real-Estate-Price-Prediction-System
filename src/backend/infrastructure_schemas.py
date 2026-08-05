from __future__ import annotations

import math
from typing import Annotated

from pydantic import BaseModel, Field, field_validator


class InfrastructureAnalysisInput(BaseModel):
    latitude: Annotated[float, Field(ge=-90, le=90)]
    longitude: Annotated[float, Field(ge=-180, le=180)]
    location_name: str | None = None

    @field_validator("latitude", "longitude")
    @classmethod
    def coordinates_must_be_finite(cls, value):
        if not math.isfinite(value):
            raise ValueError("Coordinate must be finite.")
        return value


class GeocodingInput(BaseModel):
    location_name: Annotated[str, Field(min_length=2, max_length=200)]


class GeocodingOutput(BaseModel):
    location_name: str
    latitude: float
    longitude: float
    display_name: str | None = None


class SelectedLocation(BaseModel):
    location_name: str | None
    latitude: float
    longitude: float


class RoadIndicators(BaseModel):
    nearest_road_distance_m: float | None
    nearest_major_road_distance_m: float | None
    nearest_major_road_type: str | None
    nearest_road: RoadPlace | None
    nearest_major_road: RoadPlace | None


class RoadPlace(BaseModel):
    name: str
    distance_m: float
    road_type: str
    highway_classification: str
    osm_id: int
    osm_type: str
    latitude: float | None
    longitude: float | None
    tags: dict[str, str]


class InfrastructurePlace(BaseModel):
    name: str
    osm_id: int
    osm_type: str
    latitude: float
    longitude: float
    distance_m: float
    tags: dict[str, str]


class AmenityIndicators(BaseModel):
    schools_within_1km: int
    hospitals_and_clinics_within_2km: int
    bus_stops_within_1km: int
    markets_within_1km: int
    banks_within_1km: int
    parks_within_2km: int


class CountIndicator(BaseModel):
    raw_count: int
    deduplicated_count: int
    radius_m: int
    places: list[InfrastructurePlace]


class ConnectivityIndicators(BaseModel):
    road_network_nodes_within_1km: int | None
    road_intersections_within_1km: int | None
    three_way_intersections_within_1km: int | None
    four_or_more_way_intersections_within_1km: int | None


class InfrastructureMetadata(BaseModel):
    source: str
    attribution_url: str
    method: str
    analysis_timestamp: str
    cached: bool
    stale: bool = False
    cache_expired_at: str | None = None
    limitations: list[str]


class InfrastructureAnalysisOutput(BaseModel):
    selected_location: SelectedLocation
    roads: RoadIndicators
    categories: dict[str, CountIndicator]
    amenities: AmenityIndicators
    connectivity: ConnectivityIndicators
    metadata: InfrastructureMetadata
