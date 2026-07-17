from fastapi import APIRouter, HTTPException

from infrastructure.osm_client import OSMServiceError
from infrastructure.service import InfrastructureService

from .config import RuleConfigurationError
from .schemas import InfrastructureIndexInput, InfrastructureIndexOutput
from .service import InfrastructureIndexService


router = APIRouter(prefix="/infrastructure", tags=["infrastructure-index"])
index_service = InfrastructureIndexService()
infrastructure_service = InfrastructureService()


@router.post("/index", response_model=InfrastructureIndexOutput)
async def calculate_infrastructure_index(data: InfrastructureIndexInput):
    try:
        if data.analysis is not None:
            analysis = data.analysis.model_dump()
        else:
            analysis = await infrastructure_service.analyze(
                data.latitude, data.longitude, data.location_name,
            )
        return index_service.calculate(analysis)
    except OSMServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RuleConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
