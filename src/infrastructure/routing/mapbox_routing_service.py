"""US10-TK06/TK07 — MapboxRoutingService (stub).

Implementação concreta de IRoutingService usando a Mapbox API.
- optimize_stop_order: Mapbox Optimization API v1
- get_route_info:      Mapbox Directions API
"""

from src.domains.routing.dtos import RouteInfoResult
from src.domains.routing.service import IRoutingService


class MapboxRoutingService(IRoutingService):
    """Calcula rotas e otimiza paradas via Mapbox API."""

    # US10-TK06
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    # US10-TK07
    def optimize_stop_order(self, stop_coordinates: list[dict]) -> list[int]:
        """Chama Mapbox Optimization API v1 e retorna a ordem otimizada."""
        pass  # type: ignore[return-value]

    # US10-TK07
    def get_route_info(
        self,
        origin: dict,
        waypoints: list[dict],
        destination: dict,
    ) -> RouteInfoResult:
        """Chama Mapbox Directions API e retorna distância e duração."""
        pass  # type: ignore[return-value]
