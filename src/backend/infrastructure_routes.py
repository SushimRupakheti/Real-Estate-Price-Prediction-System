from fastapi import APIRouter, HTTPException

from infrastructure.osm_client import NominatimClient, OSMServiceError
from infrastructure.service import InfrastructureService
from infrastructure_schemas import (
    GeocodingInput, GeocodingOutput, InfrastructureAnalysisInput,
    InfrastructureAnalysisOutput,
)

router = APIRouter(prefix="/infrastructure", tags=["infrastructure"])
service = InfrastructureService()
geocoder = NominatimClient()


@router.post("/geocode", response_model=GeocodingOutput)
async def geocode_location(data: GeocodingInput):
    try:
        return await geocoder.geocode(data.location_name.strip())
    except OSMServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/analyze", response_model=InfrastructureAnalysisOutput)
async def analyze_infrastructure(data: InfrastructureAnalysisInput):
    try:
        return await service.analyze(data.latitude, data.longitude, data.location_name)
    except OSMServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
