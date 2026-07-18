from __future__ import annotations

import math
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


NonNegativeInt = Annotated[int, Field(ge=0)]


class CurrentInfrastructure(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    nearest_road_distance_m: Annotated[float | None, Field(ge=0)] = None
    nearest_major_road_distance_m: Annotated[float | None, Field(ge=0)] = None
    nearest_major_road_type: str | None = Field(default=None, alias="major_road_type")
    schools: NonNegativeInt
    colleges: NonNegativeInt
    kindergartens: NonNegativeInt
    hospitals: NonNegativeInt
    clinics: NonNegativeInt
    bus_stops: NonNegativeInt
    marketplaces: NonNegativeInt
    supermarkets: NonNegativeInt
    banks: NonNegativeInt
    parks: NonNegativeInt

    @field_validator("nearest_road_distance_m", "nearest_major_road_distance_m")
    @classmethod
    def distances_must_be_finite(cls, value):
        if value is not None and not math.isfinite(value):
            raise ValueError("Distance must be finite.")
        return value


class ScenarioChange(BaseModel):
    type: str
    quantity: int | None = None
    new_distance_m: float | None = None
    new_road_type: str | None = None

    @field_validator("new_distance_m")
    @classmethod
    def distance_must_be_finite(cls, value):
        if value is not None and not math.isfinite(value):
            raise ValueError("Scenario distance must be finite.")
        return value


class ScenarioRequest(BaseModel):
    baseline_price: Annotated[float, Field(gt=0)]
    current_infrastructure: CurrentInfrastructure
    changes: list[ScenarioChange] = Field(default_factory=list)

    @field_validator("baseline_price")
    @classmethod
    def price_must_be_finite(cls, value):
        if not math.isfinite(value):
            raise ValueError("Baseline price must be finite.")
        return value


class PriceAmount(BaseModel):
    amount: int
    formatted: str


class IndexState(BaseModel):
    overall_index: int
    classification: str
    category_scores: dict[str, int]
    infrastructure: dict[str, Any]


class ScenarioIndexState(IndexState):
    index_change: int
    category_score_differences: dict[str, int]


class ValueShift(BaseModel):
    classification: str
    minimum_percent: float
    maximum_percent: float
    minimum_value: int
    maximum_value: int
    minimum_value_formatted: str
    maximum_value_formatted: str
    method: str
    is_forecast: bool
    statistically_validated: bool


class RuleContribution(BaseModel):
    change: str
    change_type: str
    category: str
    current_category_score: int
    scenario_category_score: int
    score_difference: int


class ScenarioMetadata(BaseModel):
    rules_version: str
    generated_at: str
    disclaimer: str
    temporary_copy: bool


class ScenarioResponse(BaseModel):
    baseline_price: PriceAmount
    current: IndexState
    scenario: ScenarioIndexState
    value_shift: ValueShift
    rule_contributions: list[RuleContribution]
    metadata: ScenarioMetadata
