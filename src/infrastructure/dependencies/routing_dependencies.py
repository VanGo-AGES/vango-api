"""US10-TK06 — DI para IRoutingService."""

from src.config import settings
from src.domains.routing.service import IRoutingService
from src.infrastructure.routing.mapbox_routing_service import MapboxRoutingService


# US10-TK06
def get_routing_service() -> IRoutingService:
    """Retorna uma instância de MapboxRoutingService configurada com a API key."""
    return MapboxRoutingService(api_key=settings.mapbox_api_key)
