"""Discover, download, validate and store the newest official NRB macro report.

Run from the repository root: python -m src.backend.jobs.update_nrb_macro
"""
from datetime import date,datetime,timezone
import logging
from pathlib import Path
import sys

backend=Path(__file__).resolve().parents[1]
if str(backend) not in sys.path: sys.path.insert(0,str(backend))
from database import MacroIndicator,SessionLocal
from macro.nrb_source import NRBSourceDiscovery
from macro.nrb_downloader import NRBDownloader
from macro.nrb_extractors import NRBExcelExtractor,NRBPdfExtractor,NRBCsvExtractor
from macro.repository import MacroIndicatorRepository
from macro.validation import validate

logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(message)s")
log=logging.getLogger("nrb-macro-updater")

def run():
    path=None; db=SessionLocal()
    try:
        source=NRBSourceDiscovery().discover(); path,checksum=NRBDownloader().download(source.file_url,source.file_type)
        repo=MacroIndicatorRepository(db)
        if repo.checksum_exists(checksum): log.info("Newest official NRB report is already stored; no update required."); return 0
        extractor={"xlsx":NRBExcelExtractor,"csv":NRBCsvExtractor,"pdf":NRBPdfExtractor}[source.file_type]()
        values,evidence=extractor.extract(path); validate(values)
        published=source.publication_date or date.today(); reference=published
        basis={
          "cpi_measurement_basis":"National CPI, year-on-year percentage change",
          "housing_measurement_basis":"Housing and Utilities CPI subgroup, year-on-year percentage change" if values.get("housing_inflation") is not None else "unavailable",
          "lending_measurement_basis":"Weighted average commercial-bank lending rate",
          "deposit_measurement_basis":"Weighted average commercial-bank deposit rate",
          "credit_measurement_basis":"Private-sector credit from BFIs; verify report-period basis in source evidence",
          "remittance_measurement_basis":"Remittance inflow growth in NPR; verify report-period basis in source evidence"}
        record=MacroIndicator(report_month=reference.month,report_year=reference.year,source="Nepal Rastra Bank",
          last_updated=datetime.now(timezone.utc),reference_date=reference,reference_period=f"Report published {published.isoformat()}",
          publication_date=published,source_title=source.title,source_url=source.file_url,source_file_type=source.file_type,
          source_checksum=checksum,housing_indicator_type="housing_utilities_cpi" if values.get("housing_inflation") is not None else "unavailable",
          extraction_status="validated",extraction_version="nrb_extract_v1",is_provisional=False,created_at=datetime.now(timezone.utc),**values,**basis)
        if not repo.insert(record): log.info("Report checksum already exists; no duplicate inserted.")
        else: log.info("Stored validated NRB record id=%s",record.id)
        return 0
    except Exception: db.rollback(); log.exception("NRB update failed; the previous validated record remains active."); return 1
    finally:
        db.close()
        if path:
            try: path.unlink(missing_ok=True)
            except OSError: log.warning("Unable to remove temporary file %s",path)

if __name__=="__main__": raise SystemExit(run())
