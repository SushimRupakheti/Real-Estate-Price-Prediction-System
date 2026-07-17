from __future__ import annotations

import math
from typing import Annotated, Any

from pydantic import BaseModel, Field, model_validator

from infrastructure_schemas import InfrastructureAnalysisOutput, SelectedLocation


class InfrastructureIndexInput(BaseModel):
    latitude: Annotated[float | None, Field(ge=-90, le=90)] = None
    longitude: Annotated[float | None, Field(ge=-180, le=180)] = None
    location_name: str | None = None
    analysis: InfrastructureAnalysisOutput | None = None

    @model_validator(mode="after")
    def require_analysis_or_coordinates(self):
        has_coordinates = self.latitude is not None and self.longitude is not None
        if self.analysis is None and not has_coordinates:
            raise ValueError("Provide either an infrastructure analysis or both latitude and longitude.")
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Latitude and longitude must be provided together.")
        if self.latitude is not None and not math.isfinite(self.latitude):
            raise ValueError("Latitude must be finite.")
        if self.longitude is not None and not math.isfinite(self.longitude):
            raise ValueError("Longitude must be finite.")
        return self


class MatchedRule(BaseModel):
    indicator: str
    label: str
    observed_value: int | float | str | None
    display_value: str
    matched_rule: str
    component_score: int
    component_weight: float
    weighted_contribution: float


class CategoryScore(BaseModel):
    key: str
    label: str
    description: str
    score: int
    classification: str
    reason: str
    rules_used: list[MatchedRule]


class InfrastructureIndexMetadata(BaseModel):
    name: str
    method: str
    rules_version: str
    rules_path: str
    calculated_at: str
    source: str
    limitations: list[str]


class InfrastructureIndexOutput(BaseModel):
    overall_score: int
    classification: str
    categories: dict[str, CategoryScore]
    category_weights: dict[str, float]
    weighted_contributions: dict[str, float]
    indicators_used: dict[str, Any]
    selected_location: SelectedLocation
    metadata: InfrastructureIndexMetadata
