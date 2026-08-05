from datetime import datetime
from pathlib import Path

from sqlalchemy import (Boolean, Column, Date, DateTime, Float, ForeignKey, Index,
                        Integer, Numeric, String, Text, UniqueConstraint, create_engine, text)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


DATABASE_PATH = Path(__file__).resolve().parent / "predictions.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    floor = Column(Float)
    bedroom = Column(Float)
    bathroom = Column(Float)
    land_area = Column(Float)
    road_access = Column(Float)
    property_age = Column(Float)
    has_parking = Column(Integer)
    has_balcony = Column(Integer)
    has_garden = Column(Integer)
    has_modular_kitchen = Column(Integer)
    location_encoded = Column(Float)
    location_label = Column(String)
    facing_encoded = Column(Integer)
    predicted_price = Column(Float)
    base_predicted_price = Column(Float)
    macro_adjusted_price = Column(Float)
    macro_adjustment_percentage = Column(Float)
    macro_indicator_record_id = Column(Integer, ForeignKey("macro_indicators.id"), nullable=True)
    macro_reference_date = Column(Date, nullable=True)
    macro_calibration_version = Column(String, nullable=True)
    scenario_price = Column(Float, nullable=True)
    scenario_data_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class MacroIndicator(Base):
    __tablename__ = "macro_indicators"
    __table_args__ = (
        UniqueConstraint("source_checksum", name="uq_macro_source_checksum"),
        Index("ix_macro_reference_date", "reference_date"),
        Index("ix_macro_publication_date", "publication_date"),
        Index("ix_macro_extraction_status", "extraction_status"),
    )

    id = Column(Integer, primary_key=True)
    report_month = Column(Integer, nullable=False)
    report_year = Column(Integer, nullable=False)
    cpi_inflation = Column(Numeric(10, 4), nullable=False)
    housing_inflation = Column(Numeric(10, 4), nullable=True)
    lending_rate = Column(Numeric(10, 4), nullable=False)
    deposit_rate = Column(Numeric(10, 4), nullable=False)
    credit_growth = Column(Numeric(10, 4), nullable=False)
    remittance_growth = Column(Numeric(10, 4), nullable=False)
    source = Column(Text, nullable=False, default="Nepal Rastra Bank")
    last_updated = Column(DateTime(timezone=True), nullable=False)
    reference_date = Column(Date, nullable=False)
    reference_period = Column(String, nullable=False)
    publication_date = Column(Date, nullable=False)
    source_title = Column(Text, nullable=False)
    source_url = Column(Text, nullable=False)
    source_file_type = Column(String, nullable=False)
    source_checksum = Column(String(64), nullable=False)
    housing_indicator_type = Column(String, nullable=False, default="housing_utilities_cpi")
    cpi_measurement_basis = Column(Text, nullable=False)
    housing_measurement_basis = Column(Text, nullable=True)
    lending_measurement_basis = Column(Text, nullable=False)
    deposit_measurement_basis = Column(Text, nullable=False)
    credit_measurement_basis = Column(Text, nullable=False)
    remittance_measurement_basis = Column(Text, nullable=False)
    extraction_status = Column(String, nullable=False, default="validated")
    extraction_version = Column(String, nullable=False)
    is_provisional = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False)


Base.metadata.create_all(bind=engine)


def _ensure_location_label_column():
    with engine.connect() as connection:
        columns = connection.execute(text("PRAGMA table_info(predictions)")).fetchall()
        column_names = {column[1] for column in columns}
        if "location_label" not in column_names:
            connection.execute(text("ALTER TABLE predictions ADD COLUMN location_label VARCHAR"))
            connection.commit()


_ensure_location_label_column()


def _ensure_prediction_macro_columns():
    """Small SQLite-compatible migration for existing local databases."""
    additions = {
        "base_predicted_price": "FLOAT", "macro_adjusted_price": "FLOAT",
        "macro_adjustment_percentage": "FLOAT", "macro_indicator_record_id": "INTEGER",
        "macro_reference_date": "DATE", "macro_calibration_version": "VARCHAR",
        "scenario_price": "FLOAT", "scenario_data_json": "TEXT",
    }
    with engine.connect() as connection:
        existing = {row[1] for row in connection.execute(text("PRAGMA table_info(predictions)"))}
        for name, sql_type in additions.items():
            if name not in existing:
                connection.execute(text(f"ALTER TABLE predictions ADD COLUMN {name} {sql_type}"))
        connection.commit()


_ensure_prediction_macro_columns()
