from datetime import date, datetime, timezone
from types import SimpleNamespace
import pytest

from src.backend.macro.exceptions import MacroDataUnavailableError
from src.backend.macro.service import MacroAdjustmentService

def record(identifier, year, values):
    defaults=dict(cpi_inflation=5,housing_inflation=4,lending_rate=10,deposit_rate=6,
      credit_growth=8,remittance_growth=10)
    defaults.update(values)
    return SimpleNamespace(id=identifier,reference_date=date(year,6,15),publication_date=date(year,7,1),
      created_at=datetime(year,7,1,tzinfo=timezone.utc),reference_period=f"mid-June {year}",source_url="https://www.nrb.org.np/test.pdf",
      housing_indicator_type="housing_utilities_cpi",is_provisional=False,
      cpi_measurement_basis="year-on-year",housing_measurement_basis="year-on-year",
      lending_measurement_basis="weighted average",deposit_measurement_basis="weighted average",
      credit_measurement_basis="year-on-year",remittance_measurement_basis="fiscal-year-to-date",**defaults)

class Repo:
    def __init__(self, rows): self.rows=rows
    def latest_valid(self): return self.rows[-1] if self.rows else None
    def valid_history(self, earliest_date=None): return [r for r in self.rows if not earliest_date or r.reference_date>=earliest_date]

def test_missing_data_is_explicit_not_zero_adjustment():
    with pytest.raises(MacroDataUnavailableError): MacroAdjustmentService(Repo([])).calculate(25_000_000)

def test_adjustment_is_capped_and_base_is_unchanged(monkeypatch):
    rows=[record(i,2020+i,{"lending_rate":12-i,"credit_growth":4+i}) for i in range(1,7)]
    result=MacroAdjustmentService(Repo(rows)).calculate(25_000_000)
    assert result["base_price"]==25_000_000
    assert abs(result["adjustment_percentage"])<=3
    assert result["method"]=="equal_weight_fallback"
    assert result["empirically_calibrated"] is False
    assert round(sum(x.get("contribution_percentage_points",0) for x in result["indicator_contributions"]),4)==pytest.approx(result["adjustment_percentage"],abs=.001)

def test_lower_lending_rate_has_supportive_direction():
    rows=[record(1,2024,{"lending_rate":12}),record(2,2025,{"lending_rate":10}),record(3,2026,{"lending_rate":7})]
    result=MacroAdjustmentService(Repo(rows)).calculate(10_000_000)
    lending=next(x for x in result["indicator_contributions"] if x["indicator"]=="lending_rate")
    assert lending["market_effect"]=="positive"
    assert lending["contribution_percentage_points"]>0
