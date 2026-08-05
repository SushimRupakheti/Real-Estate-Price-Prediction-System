from .config import PLAUSIBILITY_RANGES
from .exceptions import NRBExtractionError
REQUIRED={"cpi_inflation","lending_rate","deposit_rate","credit_growth","remittance_growth"}
def validate(values):
    missing=REQUIRED-set(values)
    if missing: raise NRBExtractionError("Required indicators were not extracted: "+", ".join(sorted(missing)))
    for field,value in values.items():
        if field in PLAUSIBILITY_RANGES:
            low,high=PLAUSIBILITY_RANGES[field]
            if value is None or not low<=float(value)<=high: raise NRBExtractionError(f"{field} is outside its validation range.")
    return values
