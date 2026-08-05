from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator
import math

class PriceRequest(BaseModel):
    predicted_price: float = Field(gt=0, le=10_000_000_000)
    @field_validator("predicted_price")
    @classmethod
    def finite(cls, value):
        if not math.isfinite(value): raise ValueError("predicted_price must be finite")
        return value

class EconomicChanges(BaseModel):
    cpi_change_pp: float = Field(0, ge=-20, le=20)
    housing_change_pp: float = Field(0, ge=-20, le=20)
    lending_change_pp: float = Field(0, ge=-20, le=20)
    deposit_change_pp: float = Field(0, ge=-20, le=20)
    credit_change_pp: float = Field(0, ge=-50, le=50)
    remittance_change_pp: float = Field(0, ge=-100, le=100)

class InfrastructureProject(BaseModel):
    type: Literal["hospital", "highway", "university", "shopping_mall"]
    name: str = Field(min_length=1, max_length=200)
    distance_meters: float = Field(gt=0, le=100_000)
    status: Literal["proposed", "approved", "under_construction", "completed"]
    expected_completion_date: date | None = None
    confidence: Literal["low", "medium", "high"]
    source: str = Field(min_length=1, max_length=500)

class ScenarioRequest(BaseModel):
    base_price: float = Field(gt=0, le=10_000_000_000)
    economic_changes: EconomicChanges = Field(default_factory=EconomicChanges)
    infrastructure_projects: list[InfrastructureProject] = Field(default_factory=list, max_length=10)
