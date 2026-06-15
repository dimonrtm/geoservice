from uuid import UUID

from fastapi import APIRouter, Depends

from api.auth import require_editor
from api.deps import get_utility_network_service
from models.user import User
from schemas.utility_network import UtilityFeederOut
from services.utility_network_service import UtilityNetworkService


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
    _: User = Depends(require_editor),
    service: UtilityNetworkService = Depends(get_utility_network_service),
) -> UtilityFeederOut:
    feeder_id = feederId
    return await service.get_feeder(feeder_id)
