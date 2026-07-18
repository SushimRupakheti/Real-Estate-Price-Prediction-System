from fastapi import APIRouter, HTTPException

from scenario.config import ScenarioConfigurationError
from scenario.rules import ScenarioValidationError
from scenario.schemas import ScenarioRequest, ScenarioResponse
from scenario.service import ScenarioService


router = APIRouter(prefix="/scenarios", tags=["infrastructure-scenarios"])
service = ScenarioService()


@router.post("/simulate", response_model=ScenarioResponse)
def simulate_scenario(data: ScenarioRequest):
    try:
        return service.simulate(data.model_dump(by_alias=False))
    except ScenarioValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ScenarioConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
