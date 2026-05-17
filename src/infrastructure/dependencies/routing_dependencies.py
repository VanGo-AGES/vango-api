"""US10-TK06 — DI para IRoutingService.
US10-TK18 — DI para IGeocodingService."""

from src.config import settings
from src.domains.routing.service import IGeocodingService, IRoutingService
from src.infrastructure.routing.mapbox_routing_service import (
    MapboxGeocodingService,
    MapboxRoutingService,
)


# US10-TK06
def get_routing_service() -> IRoutingService:
    """Retorna uma instância de MapboxRoutingService configurada com a API key."""
    return MapboxRoutingService(api_key=settings.mapbox_api_key)


# US10-TK18
def get_geocoding_service() -> IGeocodingService:
    """Retorna uma instância de MapboxGeocodingService configurada com a API key.

    Injetada no RouteService e RoutePassangerService para popular lat/lng
    no momento de criar AddressModel.
    """
    return MapboxGeocodingService(api_key=settings.mapbox_api_key)
