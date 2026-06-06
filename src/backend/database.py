from datetime import datetime
from pathlib import Path

from sqlalchemy import Column, DateTime, Float, Integer, create_engine
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
    facing_encoded = Column(Integer)
    predicted_price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)
