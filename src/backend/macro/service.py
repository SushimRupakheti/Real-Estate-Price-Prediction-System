from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
import statistics

from .config import SETTINGS, load_assumption_rules
from .exceptions import MacroDataUnavailableError

FIELDS = {
    "cpi": ("cpi_inflation", 1, "National CPI Inflation"),
    "housing": ("housing_inflation", 1, "Housing & Utilities CPI Inflation"),
    "lending": ("lending_rate", -1, "Commercial Bank Lending Rate"),
    "deposit": ("deposit_rate", -1, "Commercial Bank Deposit Rate"),
    "credit": ("credit_growth", 1, "Private-Sector Credit Growth"),
    "remittance": ("remittance_growth", 1, "Remittance Growth"),
}

def _number(value): return None if value is None else float(value)
def _median(values): return statistics.median(values)
def _percentile_rank(values, target):
    if not values: return 50
    return round(100 * sum(v <= target for v in values) / len(values))

class MacroIndicatorService:
    def __init__(self, repository): self.repository = repository
    def latest(self):
        record = self.repository.latest_valid()
        if not record: raise MacroDataUnavailableError("No validated NRB macroeconomic record is available.")
        return record
    def status(self, record):
        return "stale" if date.today() - record.reference_date > timedelta(days=SETTINGS.stale_after_days) else "current"
    def serialize(self, r):
        return {
            "record_id": r.id, "cpi": _number(r.cpi_inflation), "housing": _number(r.housing_inflation),
            "housing_label": "Residential House Price Inflation" if r.housing_indicator_type == "residential_house_price_index" else "Housing & Utilities CPI Inflation",
            "housing_indicator_type": r.housing_indicator_type, "lending": _number(r.lending_rate),
            "deposit": _number(r.deposit_rate), "credit": _number(r.credit_growth),
            "remittance": _number(r.remittance_growth), "reference_period": r.reference_period,
            "reference_date": r.reference_date, "publication_date": r.publication_date,
            "last_updated": r.last_updated, "source_title": r.source_title, "source_url": r.source_url,
            "data_status": self.status(r), "is_provisional": r.is_provisional,
            "definitions": {
                "cpi": r.cpi_measurement_basis, "housing": r.housing_measurement_basis,
                "lending": r.lending_measurement_basis, "deposit": r.deposit_measurement_basis,
                "credit": r.credit_measurement_basis, "remittance": r.remittance_measurement_basis,
            }
        }

class MacroAdjustmentService:
    def __init__(self, repository):
        self.repository = repository; self.indicators = MacroIndicatorService(repository)

    def _statistics(self, records):
        result = {}
        for key, (field, _, _) in FIELDS.items():
            values = [_number(getattr(r, field)) for r in records if getattr(r, field) is not None]
            if not values: result[key] = None; continue
            median = _median(values); deviations = [abs(v - median) for v in values]
            mad = _median(deviations)
            ordered = sorted(values); q1 = ordered[max(0, int((len(ordered)-1)*.25))]; q3 = ordered[int((len(ordered)-1)*.75)]
            scale = mad * 1.4826 or (q3-q1)/1.349 or max(abs(median)*.1, 1)
            result[key] = {"values": values, "median": median, "scale": scale}
        return result

    def _assumption_calculation(self, current, base_price, overrides=None):
        rules=load_assumption_rules(); contributions=[]; total=0.0
        for key,(field,direction,display) in FIELDS.items():
            actual=_number(getattr(current,field)); value=overrides.get(key,actual) if overrides else actual
            rule=rules["indicators"][key]
            if value is None:
                contributions.append({"indicator":field,"display_name":display,"value":None,"available":False,
                  "explanation":f"{display} is unavailable and was excluded rather than replaced with zero."}); continue
            difference=value-rule["neutral_baseline"]
            contribution=difference*rule["percentage_points_per_unit"]*rule["direction"]
            if key=="cpi" and value>rule.get("moderate_upper_bound",999): contribution=-abs(contribution)
            limit=rule["maximum_contribution"]; contribution=max(-limit,min(limit,contribution)); total+=contribution
            effect="positive" if contribution>.005 else "negative" if contribution<-.005 else "neutral"
            contributions.append({"indicator":field,"display_name":display,"value":round(value,4),
              "baseline":rule["neutral_baseline"],"measurement_basis":getattr(current,f"{field.split('_')[0]}_measurement_basis","official reported percentage"),
              "normalized_signal":round(difference,4),"economic_direction":"positive" if direction>0 else "negative",
              "market_effect":effect,"available":True,"contribution_percentage_points":round(contribution,4),
              "explanation":f"Under the documented fallback rule, {display} at {value:.2f}% versus the {rule['neutral_baseline']:.2f}% assumption contributes {contribution:+.2f} percentage points."})
        maximum=rules["maximum_total_adjustment_percent"]; adjustment=max(-maximum,min(maximum,total))
        if total and adjustment!=total:
            scale=adjustment/total
            for c in contributions:
                if c.get("available"): c["contribution_percentage_points"]=round(c["contribution_percentage_points"]*scale,4)
        money=(Decimal(str(base_price))*(Decimal(1)+Decimal(str(adjustment))/Decimal(100))).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
        available=[c for c in contributions if c.get("available")]
        positive=max(available,key=lambda c:c["contribution_percentage_points"],default=None)
        negative=min(available,key=lambda c:c["contribution_percentage_points"],default=None)
        summary=f"For {current.reference_period}, "
        if positive and positive["contribution_percentage_points"]>0: summary+=f"{positive['display_name']} provides the strongest supportive assumed contribution. "
        if negative and negative["contribution_percentage_points"]<0: summary+=f"{negative['display_name']} provides the strongest restrictive assumed contribution. "
        summary+=f"Together the documented assumptions produce a {adjustment:+.2f}% adjustment. This is not historically calibrated, an NRB property forecast, or a guarantee."
        status="Positive Market" if adjustment>.25 else "Cooling Market" if adjustment<-.25 else "Neutral Market"
        return {"base_price":float(Decimal(str(base_price)).quantize(Decimal('.01'))),"adjustment_percentage":round(adjustment,4),
          "adjusted_price":float(money),"market_score":round(50+(adjustment/maximum)*50),"market_status":status,
          "method":rules["method"],"empirically_calibrated":False,"indicator_contributions":contributions,
          "economic_summary":summary,"reference_period":current.reference_period,"reference_date":current.reference_date,
          "publication_date":current.publication_date,"data_status":self.indicators.status(current),"source_url":current.source_url,
          "macro_indicator_record_id":current.id,"calibration_version":rules["version"],
          "calibration_metadata":{"baseline_years":0,"maximum_adjustment_percent":maximum,"assumption_rules":rules["indicators"],"limitations":rules["limitations"]}}

    def calculate(self, base_price, overrides=None):
        current = self.indicators.latest()
        earliest = current.reference_date.replace(year=max(1, current.reference_date.year-SETTINGS.baseline_years))
        history = self.repository.valid_history(earliest)
        if len(history) < 3:
            return self._assumption_calculation(current, base_price, overrides)
        stats = self._statistics(history)
        contributions, directed = [], []
        for key, (field, direction, display) in FIELDS.items():
            actual = _number(getattr(current, field))
            value = overrides.get(key, actual) if overrides else actual
            stat = stats.get(key)
            if value is None or not stat:
                contributions.append({"indicator": field, "display_name": display, "value": None, "available": False, "explanation": f"{display} is unavailable and was excluded."}); continue
            signal = max(-2.5, min(2.5, (value-stat["median"])/stat["scale"]))
            # CPI becomes restrictive above a robust +1 signal; housing is deliberately capped.
            if key == "cpi": signal = signal if signal <= 1 else max(-1, 2-signal)
            if key == "housing": signal = max(-1.25, min(1.25, signal))
            directed_signal = signal * direction; directed.append(directed_signal)
            contributions.append({"indicator": field, "display_name": display, "value": round(value, 4),
              "baseline": round(stat["median"], 4), "measurement_basis": getattr(current, f"{field.split('_')[0]}_measurement_basis", "official reported percentage"),
              "normalized_signal": round(signal, 4), "economic_direction": "positive" if direction > 0 else "negative",
              "market_effect": "positive" if directed_signal > .05 else "negative" if directed_signal < -.05 else "neutral",
              "available": True})
        count = len(directed); mai = sum(directed)/count if count else 0
        adjustment = max(-SETTINGS.fallback_max_adjustment, min(SETTINGS.fallback_max_adjustment,
                         mai/2.5*SETTINGS.fallback_max_adjustment))
        available = [c for c in contributions if c.get("available")]
        for c in available:
            ds = c["normalized_signal"] * (-1 if c["economic_direction"] == "negative" else 1)
            c["contribution_percentage_points"] = round(ds/count/2.5*SETTINGS.fallback_max_adjustment, 4)
            comparison="above" if c["value"]>c["baseline"] else "below" if c["value"]<c["baseline"] else "equal to"
            c["explanation"] = f"{c['display_name']} is {comparison} its trailing baseline and may have a {c['market_effect']} market contribution."
        historical_mai = []
        for r in history:
            vals=[]
            for key,(field,direction,_) in FIELDS.items():
                s=stats.get(key); v=_number(getattr(r,field))
                if s and v is not None: vals.append(max(-2.5,min(2.5,(v-s['median'])/s['scale']))*direction)
            if vals: historical_mai.append(sum(vals)/len(vals))
        score=_percentile_rank(historical_mai,mai) if len(historical_mai)>=3 else 50
        ordered=sorted(historical_mai); lower=ordered[len(ordered)//3] if ordered else 0; upper=ordered[(2*len(ordered))//3] if ordered else 0
        status="Neutral Market" if len(historical_mai)<3 else "Positive Market" if mai>upper else "Cooling Market" if mai<lower else "Neutral Market"
        money=(Decimal(str(base_price))*(Decimal("1")+Decimal(str(adjustment))/Decimal("100"))).quantize(Decimal("0.01"),rounding=ROUND_HALF_UP)
        positives=sorted(available,key=lambda c:c["contribution_percentage_points"],reverse=True)
        negatives=sorted(available,key=lambda c:c["contribution_percentage_points"])
        unavailable=[c["display_name"] for c in contributions if not c.get("available")]
        has_signal=any(abs(c["contribution_percentage_points"])>.0001 for c in available)
        summary=(f"For {current.reference_period}, {positives[0]['display_name']} provides the strongest supportive signal." if positives and has_signal else f"For {current.reference_period}, the available indicators are neutral relative to the currently stored baseline.")
        if negatives and negatives[0]["contribution_percentage_points"] < 0:
            summary += f" {negatives[0]['display_name']} provides the strongest restrictive signal."
        summary += f" Conditions suggest a {adjustment:+.2f}% analytical adjustment; this is not an NRB property valuation or a guarantee."
        if unavailable: summary += " Unavailable and excluded: " + ", ".join(unavailable) + "."
        return {"base_price": float(Decimal(str(base_price)).quantize(Decimal('0.01'))), "adjustment_percentage": round(adjustment,4),
          "adjusted_price": float(money), "market_score": score, "market_status": status,
          "method": "equal_weight_fallback", "empirically_calibrated": False,
          "indicator_contributions": contributions, "economic_summary": summary,
          "reference_period": current.reference_period, "reference_date": current.reference_date,
          "publication_date": current.publication_date, "data_status": self.indicators.status(current),
          "source_url": current.source_url, "macro_indicator_record_id": current.id,
          "calibration_version": SETTINGS.calibration_version,
          "calibration_metadata": {"baseline_years": SETTINGS.baseline_years, "maximum_adjustment_percent": SETTINGS.fallback_max_adjustment,
             "limitation": "Equal weighting is a conservative fallback and is not empirically calibrated to Nepal property-price changes."}}

class MacroScenarioService:
    def __init__(self, adjustment): self.adjustment=adjustment
    def calculate(self, request):
        base=self.adjustment.calculate(request.base_price)
        current=self.adjustment.indicators.latest()
        changes=request.economic_changes.model_dump()
        overrides={key:_number(getattr(current,field))+changes[f"{key}_change_pp"] for key,(field,_,_) in FIELDS.items() if getattr(current,field) is not None}
        # Convert the absolute future MAI factor to an incremental factor relative
        # to today's MAI, preventing the current adjustment from being compounded twice.
        future=self.adjustment.calculate(request.base_price,overrides)
        current_factor=Decimal(1)+Decimal(str(base["adjustment_percentage"]))/Decimal(100)
        future_factor=Decimal(1)+Decimal(str(future["adjustment_percentage"]))/Decimal(100)
        future_econ=float(((future_factor/current_factor)-Decimal(1))*Decimal(100))
        warnings=["This is a hypothetical scenario and not a guaranteed future property value."]
        infra=[]
        for project in request.infrastructure_projects:
            infra.append({"project":project.name,"adjustment_percentage_points":0,"explanation":"No validated project-impact calibration is available; the project is recorded as an assumption but no price premium was applied."})
        if infra: warnings.append("Infrastructure projects have no price adjustment because this project has no evidence-based impact calibration.")
        scenario=Decimal(str(base["adjusted_price"]))*(Decimal(1)+Decimal(str(future_econ))/Decimal(100))
        return {"base_price":request.base_price,"current_macro_adjustment_percentage":base["adjustment_percentage"],
          "current_macro_adjusted_price":base["adjusted_price"],"future_economic_adjustment_percentage":future_econ,
          "future_infrastructure_adjustment_percentage":0,"future_scenario_price":float(scenario.quantize(Decimal('.01'))),
          "hypothetical":True,"assumptions":["Economic inputs are percentage-point changes from the latest validated NRB values."],
          "warnings":warnings,"contributions":{"current_macro":base["indicator_contributions"],"future_economic":future["indicator_contributions"],"future_infrastructure":infra}}
