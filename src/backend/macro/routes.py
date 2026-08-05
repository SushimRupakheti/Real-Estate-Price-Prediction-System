from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from .exceptions import MacroDataUnavailableError
from .repository import MacroIndicatorRepository
from .schemas import PriceRequest, ScenarioRequest
from .service import MacroAdjustmentService, MacroIndicatorService, MacroScenarioService

router=APIRouter(prefix="/api/macro",tags=["macroeconomic-adjustment"])
def db_session():
    db=SessionLocal()
    try: yield db
    finally: db.close()
def services(db):
    repo=MacroIndicatorRepository(db); adjustment=MacroAdjustmentService(repo)
    return MacroIndicatorService(repo), adjustment, MacroScenarioService(adjustment)
def unavailable(exc): return HTTPException(status_code=503,detail=str(exc))

@router.get("/current")
def current(db:Session=Depends(db_session)):
    try:
        service,_,_=services(db); return service.serialize(service.latest())
    except MacroDataUnavailableError as exc: raise unavailable(exc)

@router.post("/adjust")
def adjust(data:PriceRequest,db:Session=Depends(db_session)):
    try: return services(db)[1].calculate(data.predicted_price)
    except MacroDataUnavailableError as exc: raise unavailable(exc)

@router.post("/scenario")
def scenario(data:ScenarioRequest,db:Session=Depends(db_session)):
    try: return services(db)[2].calculate(data)
    except MacroDataUnavailableError as exc: raise unavailable(exc)
