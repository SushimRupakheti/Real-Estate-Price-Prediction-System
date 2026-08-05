-- Reference migration for SQLite deployments. The local app performs the
-- equivalent additive migration on startup so existing prediction rows remain valid.
CREATE TABLE IF NOT EXISTS macro_indicators (
 id INTEGER PRIMARY KEY, report_month INTEGER NOT NULL, report_year INTEGER NOT NULL,
 cpi_inflation NUMERIC(10,4) NOT NULL, housing_inflation NUMERIC(10,4),
 lending_rate NUMERIC(10,4) NOT NULL, deposit_rate NUMERIC(10,4) NOT NULL,
 credit_growth NUMERIC(10,4) NOT NULL, remittance_growth NUMERIC(10,4) NOT NULL,
 source TEXT NOT NULL, last_updated DATETIME NOT NULL, reference_date DATE NOT NULL,
 reference_period VARCHAR NOT NULL, publication_date DATE NOT NULL,
 source_title TEXT NOT NULL, source_url TEXT NOT NULL, source_file_type VARCHAR NOT NULL,
 source_checksum VARCHAR(64) NOT NULL UNIQUE, housing_indicator_type VARCHAR NOT NULL,
 cpi_measurement_basis TEXT NOT NULL, housing_measurement_basis TEXT,
 lending_measurement_basis TEXT NOT NULL, deposit_measurement_basis TEXT NOT NULL,
 credit_measurement_basis TEXT NOT NULL, remittance_measurement_basis TEXT NOT NULL,
 extraction_status VARCHAR NOT NULL, extraction_version VARCHAR NOT NULL,
 is_provisional BOOLEAN NOT NULL DEFAULT 0, created_at DATETIME NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_macro_reference_date ON macro_indicators(reference_date);
CREATE INDEX IF NOT EXISTS ix_macro_publication_date ON macro_indicators(publication_date);
CREATE INDEX IF NOT EXISTS ix_macro_extraction_status ON macro_indicators(extraction_status);
