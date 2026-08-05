import json
import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

@dataclass(frozen=True)
class MacroSettings:
    archive_url: str = os.getenv("NRB_MACRO_ARCHIVE_URL", "https://www.nrb.org.np/")
    allowed_domains: tuple[str, ...] = tuple(x.strip() for x in os.getenv("NRB_ALLOWED_DOMAINS", "nrb.org.np,www.nrb.org.np").split(","))
    timeout_seconds: float = float(os.getenv("NRB_REQUEST_TIMEOUT_SECONDS", "20"))
    retry_count: int = int(os.getenv("NRB_REQUEST_RETRY_COUNT", "3"))
    max_download_mb: int = int(os.getenv("NRB_MAX_DOWNLOAD_SIZE_MB", "25"))
    stale_after_days: int = int(os.getenv("MACRO_STALE_AFTER_DAYS", "60"))
    baseline_years: int = int(os.getenv("MACRO_BASELINE_YEARS", "5"))
    calibration_version: str = os.getenv("MACRO_CALIBRATION_VERSION", "mai_equal_v1")
    fallback_max_adjustment: float = float(os.getenv("MACRO_FALLBACK_MAX_ADJUSTMENT_PERCENT", "3"))
    temp_directory: Path = Path(os.getenv("TEMP_DOWNLOAD_DIRECTORY", str(ROOT / "tmp" / "nrb")))

SETTINGS = MacroSettings()

def load_assumption_rules():
    return json.loads((ROOT / "config" / "macro_adjustment_rules.json").read_text(encoding="utf-8"))

PLAUSIBILITY_RANGES = {
    "cpi_inflation": (-20, 50), "housing_inflation": (-30, 80),
    "lending_rate": (0, 40), "deposit_rate": (0, 30),
    "credit_growth": (-50, 100), "remittance_growth": (-80, 150),
}
