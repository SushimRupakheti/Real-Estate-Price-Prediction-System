from pathlib import Path
import json

import sys

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from schemas import HouseInput, PredictionOutput
from database import SessionLocal, Prediction
from model import predict_price, explain_prediction
from infrastructure_routes import router as infrastructure_router
from infrastructure_index.routes import router as infrastructure_index_router



app = FastAPI(title="House Price Prediction API")
app.include_router(infrastructure_router)
app.include_router(infrastructure_index_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "House Price Prediction API is running"}



@app.post("/predict", response_model=PredictionOutput)
def predict(data: HouseInput, db: Session = Depends(get_db)):
    area_per_bedroom = data.land_area / data.bedroom
    total_rooms      = data.bedroom + data.bathroom
    is_new           = 1 if data.property_age <= 2 else 0

    features = [
        data.floor, data.bedroom, data.bathroom,
        data.land_area, data.road_access, data.property_age,
        data.has_parking, data.has_balcony, data.has_garden,
        data.has_modular_kitchen, data.location_encoded,
        data.facing_encoded, area_per_bedroom, total_rooms, is_new,
        data.location_label
    ]

    price      = predict_price(features)
    price_cr   = f"{round(price / 10000000, 2)} Cr"
    shap_vals  = explain_prediction(features)

    # Save to DB
    record = Prediction(
        floor=data.floor, bedroom=data.bedroom,
        bathroom=data.bathroom, land_area=data.land_area,
        road_access=data.road_access, property_age=data.property_age,
        has_parking=data.has_parking, has_balcony=data.has_balcony,
        has_garden=data.has_garden, has_modular_kitchen=data.has_modular_kitchen,
        location_encoded=data.location_encoded, location_label=data.location_label,
        facing_encoded=data.facing_encoded,
        predicted_price=price,
    )
    db.add(record)
    db.commit()

    return {
        "predicted_price"     : price,
        "predicted_price_cr"  : price_cr,
        "shap_values"         : shap_vals
    }


@app.get("/history")
def history(db: Session = Depends(get_db)):
    records = db.query(Prediction).order_by(Prediction.id.desc()).all()
    return records


@app.get("/stats")
def stats():
    root_dir = Path(__file__).resolve().parents[2]
    metrics = json.loads((root_dir / "models" / "metrics.json").read_text(encoding="utf-8"))
    metadata = json.loads((root_dir / "models" / "model_metadata.json").read_text(encoding="utf-8"))
    selected = metrics[metadata["best_model"]]
    return {
        "r2": selected["r2"], "mae": selected["mae"], "rmse": selected["rmse"],
        "model": metadata["best_model"], "features": 15,
        "train_size": metadata["train_rows"], "test_size": metadata["test_rows"],
        "model_comparison": [{"model": name, "status": "Selected" if name == metadata["best_model"] else "Baseline", **values}
                             for name, values in metrics.items()],
    }

@app.get("/locations")
def locations():
    return [
        {"label": "Aakasedhara, Kathmandu", "value": 31500000},
        {"label": "Aaptari, Chitwan", "value": 22000000},
        {"label": "Aarubari, Kathmandu", "value": 19000000},
        {"label": "Anamnagar, Kathmandu", "value": 42500000},
        {"label": "Bafal, Kathmandu", "value": 37000000},
        {"label": "Bagdol, Lalitpur", "value": 42000000},
        {"label": "Bagdurbar, Kathmandu", "value": 30000000},
        {"label": "Bageshwori, Bhaktapur", "value": 25000000},
        {"label": "Balaju, Kathmandu", "value": 57500000},
        {"label": "Balambu, Kathmandu", "value": 27500000},
        {"label": "Balkhu, Kathmandu", "value": 37000000},
        {"label": "Balkhu, Lalitpur", "value": 24900000},
        {"label": "Balkot, Bhaktapur", "value": 35250000},
        {"label": "Balkumari, Lalitpur", "value": 60500000},
        {"label": "Baluwatar, Kathmandu", "value": 54000000},
        {"label": "Banasthali, Kathmandu", "value": 45000000},
        {"label": "Banepa, Kavrepalanchok", "value": 20000000},
        {"label": "Baneshwor, Kathmandu", "value": 44950000},
        {"label": "Baniyatar, Kathmandu", "value": 28500000},
        {"label": "Bansbari, Kathmandu", "value": 55000000},
        {"label": "Basundhara, Kathmandu", "value": 39000000},
        {"label": "Bhaisepati, Lalitpur", "value": 43500000},
        {"label": "Bhaktapur, Bhaktapur", "value": 14000000},
        {"label": "Bijulibajar, Kathmandu", "value": 85000000},
        {"label": "Bouddha, Kathmandu", "value": 67500000},
        {"label": "Budhanilkantha, Kathmandu", "value": 43000000},
        {"label": "Chabahil, Kathmandu", "value": 120000000},
        {"label": "Chandol, Kathmandu", "value": 87500000},
        {"label": "Chandragiri, Kathmandu", "value": 17000000},
        {"label": "Chapali, Kathmandu", "value": 28000000},
        {"label": "Chhauni, Kathmandu", "value": 34000000},
        {"label": "Chhetrapati, Kathmandu", "value": 125000000},
        {"label": "Chundevi, Kathmandu", "value": 67500000},
        {"label": "Dallu, Kathmandu", "value": 57500000},
        {"label": "Dhapasi, Kathmandu", "value": 33000000},
        {"label": "Dhobighat, Lalitpur", "value": 37500000},
        {"label": "Dholahiti, Lalitpur", "value": 41000000},
        {"label": "Dhumbarahi, Kathmandu", "value": 55000000},
        {"label": "Dillibazar, Kathmandu", "value": 140000000},
        {"label": "Ekantakuna, Lalitpur", "value": 36000000},
        {"label": "Gairidhara, Kathmandu", "value": 51000000},
        {"label": "Gokarna, Kathmandu", "value": 21500000},
        {"label": "Gongabu, Kathmandu", "value": 35000000},
        {"label": "Gothatar, Kathmandu", "value": 21750000},
        {"label": "Gwarko, Lalitpur", "value": 27500000},
        {"label": "Gyaneshwor, Kathmandu", "value": 45000000},
        {"label": "Handigaun, Kathmandu", "value": 52500000},
        {"label": "Harisiddhi, Lalitpur", "value": 27000000},
        {"label": "Hasantar, Kathmandu", "value": 48500000},
        {"label": "Imadol, Lalitpur", "value": 27500000},
        {"label": "Itahari, Sunsari", "value": 39000000},
        {"label": "Jawalakhel, Lalitpur", "value": 73000000},
        {"label": "Jhamsikhel, Lalitpur", "value": 40000000},
        {"label": "Jorpati, Kathmandu", "value": 23000000},
        {"label": "Kalanki, Kathmandu", "value": 35000000},
        {"label": "Kalikasthan, Kathmandu", "value": 42500000},
        {"label": "Kamalpokhari, Kathmandu", "value": 180000000},
        {"label": "Kapan, Kathmandu", "value": 28000000},
        {"label": "Khumaltar, Lalitpur", "value": 42500000},
        {"label": "Khusibu, Kathmandu", "value": 41000000},
        {"label": "Koteshwor, Kathmandu", "value": 45000000},
        {"label": "Kuleshwor, Kathmandu", "value": 45000000},
        {"label": "Kupandole, Lalitpur", "value": 80000000},
        {"label": "Kusunti, Lalitpur", "value": 76250000},
        {"label": "Lainchaur, Kathmandu", "value": 35000000},
        {"label": "Lakeside, Kaski", "value": 85000000},
        {"label": "Lalitpur, Lalitpur", "value": 27000000},
        {"label": "Lazimpat, Kathmandu", "value": 56000000},
        {"label": "Lele, Lalitpur", "value": 73000000},
        {"label": "Lubhu, Lalitpur", "value": 17500000},
        {"label": "Maharajgunj, Kathmandu", "value": 90000000},
        {"label": "Maitidevi, Kathmandu", "value": 105000000},
        {"label": "Maligaon, Kathmandu", "value": 65000000},
        {"label": "Manbhawan, Lalitpur", "value": 62000000},
        {"label": "Mid Baneshwor, Kathmandu", "value": 100000000},
        {"label": "Mulpani, Kathmandu", "value": 17750000},
        {"label": "Nakhipot, Lalitpur", "value": 32500000},
        {"label": "Nakkhu, Lalitpur", "value": 33000000},
        {"label": "Narephat, Kathmandu", "value": 31500000},
        {"label": "Naxal, Kathmandu", "value": 46500000},
        {"label": "Nayabazar, Kathmandu", "value": 27500000},
        {"label": "New Baneshwor, Kathmandu", "value": 16800000},
        {"label": "New Buspark, Kathmandu", "value": 61500000},
        {"label": "Paknajol, Kathmandu", "value": 72500000},
        {"label": "Panipokhari, Kathmandu", "value": 65000000},
        {"label": "Pepsicola, Kathmandu", "value": 27500000},
        {"label": "Pingalasthan, Kathmandu", "value": 45000000},
        {"label": "Pokhara, Kaski", "value": 37500000},
        {"label": "Putalisadak, Kathmandu", "value": 85000000},
        {"label": "Ratopool, Kathmandu", "value": 138000000},
        {"label": "Rudreshwor, Kathmandu", "value": 53750000},
        {"label": "Sainbu, Lalitpur", "value": 35000000},
        {"label": "Samakhusi, Kathmandu", "value": 33000000},
        {"label": "Sanepa, Lalitpur", "value": 69250000},
        {"label": "Satdobato, Lalitpur", "value": 45000000},
        {"label": "Shankhamul, Kathmandu", "value": 50250000},
        {"label": "Shantinagar, Kathmandu", "value": 48750000},
        {"label": "Sinamangal, Kathmandu", "value": 47000000},
        {"label": "Sitapaila, Kathmandu", "value": 29500000},
        {"label": "Sukedhara, Kathmandu", "value": 30000000},
        {"label": "Sunakothi, Lalitpur", "value": 40000000},
        {"label": "Swoyambhu, Kathmandu", "value": 110000000},
        {"label": "Tahachal, Kathmandu", "value": 66500000},
        {"label": "Teku, Kathmandu", "value": 77500000},
        {"label": "Thaiba, Lalitpur", "value": 46750000},
        {"label": "Thamel, Kathmandu", "value": 39000000},
        {"label": "Thapagaun, Kathmandu", "value": 43000000},
        {"label": "Tikathali, Lalitpur", "value": 25500000},
        {"label": "Tilganga, Kathmandu", "value": 61500000},
        {"label": "Tokha, Kathmandu", "value": 33750000},
        {"label": "Vinayak Colony, Lalitpur", "value": 51000000},
    ]

@app.get("/shap-importance")
def shap_importance():
    import pandas as pd
    from model import global_feature_importance

    X_train = pd.read_csv(
        r"C:\Users\ASUS\Desktop\prediction_model\data\processed\X_train.csv"
    )

    return global_feature_importance(X_train)
