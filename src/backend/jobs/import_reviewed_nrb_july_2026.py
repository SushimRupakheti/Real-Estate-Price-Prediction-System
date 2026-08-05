"""One-time administrator-reviewed correction for NRB's July 13, 2026 report.

The values below were checked against the official English eleven-month report.
Housing & Utilities CPI is intentionally unavailable rather than inferred.
"""
from pathlib import Path
import sys
backend=Path(__file__).resolve().parents[1]
if str(backend) not in sys.path: sys.path.insert(0,str(backend))
from database import SessionLocal, MacroIndicator

def run():
    db=SessionLocal()
    try:
        row=db.query(MacroIndicator).filter(MacroIndicator.id==1).one()
        row.report_month=6; row.report_year=2026
        row.cpi_inflation=5.22; row.housing_inflation=None
        row.lending_rate=6.64; row.deposit_rate=3.29
        row.credit_growth=6.50; row.remittance_growth=38.20
        from datetime import date,datetime,timezone
        row.reference_date=date(2026,6,15)
        row.reference_period="Ending mid-June 2026 (eleven months of FY 2025/26)"
        row.publication_date=date(2026,7,13)
        row.housing_indicator_type="unavailable"
        row.housing_measurement_basis="Not available as a verified Housing and Utilities CPI subgroup in the reviewed English report"
        row.credit_measurement_basis="Private-sector credit from BFIs, year-on-year"
        row.remittance_measurement_basis="Cumulative eleven-month growth in remittance inflows in NPR versus the same prior-year period"
        row.extraction_version="manual_review_v1"; row.is_provisional=True
        row.last_updated=datetime.now(timezone.utc); row.created_at=datetime.now(timezone.utc)
        db.commit(); return row.id
    except Exception: db.rollback(); raise
    finally: db.close()

if __name__=="__main__": print(f"Reviewed macro record id={run()} activated")
