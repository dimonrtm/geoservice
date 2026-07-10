from uuid import UUID

from fastapi import APIRouter, Depends

from utility_service.use_cases.deps import get_utility_network_service
from utility_service.use_cases.dtos import AuthUserDTO
from utility_service.use_cases.schemas.utility_network import UtilityFeederOut
from utility_service.use_cases.services.utility_network_service import UtilityNetworkService
from utility_service.web_api.api.auth import require_editor


utility_network_router = APIRouter(
    prefix="/api/v1/utility-network",
    tags=["utility-network"],
)


@utility_network_router.get(
    "/feeders/{feederId}",
    response_model=UtilityFeederOut,
)
async def get_feeder(
    feederId: UUID,
    _: AuthUserDTO = Depends(require_editor),
    service: UtilityNetworkService = Depends(get_utility_network_service),
) -> UtilityFeederOut:
    feeder_id = feederId
    return await service.get_feeder(feeder_id)
