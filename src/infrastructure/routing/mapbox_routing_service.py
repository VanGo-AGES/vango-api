"""US10-TK06/TK07 — MapboxRoutingService (stub).
US10-TK18 — MapboxGeocodingService (stub).

Implementações concretas usando a Mapbox API:
- MapboxRoutingService.optimize_stop_order → Mapbox Optimization API v1
- MapboxRoutingService.get_route_info      → Mapbox Directions API
- MapboxGeocodingService.geocode_address   → Mapbox Geocoding API v5/v6
"""

from src.domains.routing.dtos import GeocodeResult, RouteInfoResult
from src.domains.routing.service import IGeocodingService, IRoutingService


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


# US10-TK18
class MapboxGeocodingService(IGeocodingService):
    """Resolve endereços brasileiros em coordenadas via Mapbox Geocoding API.

    Implementação esperada:
    - Montar uma query textual a partir dos campos do endereço
      (ex.: "{street} {number}, {neighborhood}, {city}, {state}, {zip}, Brazil").
    - Chamar a Mapbox Geocoding API (forward geocoding) com country=BR e
      limit=1 (ou similar) usando self.api_key.
    - Conferir relevance da feature retornada; descartar se abaixo de
      limiar (~0.5) — endereços ambíguos viram None.
    - Extrair longitude/latitude da feature (center[0]/center[1] no v5,
      properties.coordinates no v6) e devolver GeocodeResult.
    - Qualquer erro de rede/parsing/credencial deve resultar em None,
      nunca em exceção propagada — geocoding é best-effort durante a
      criação do endereço.
    """

    # US10-TK18
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    # US10-TK18
    def geocode_address(
        self,
        street: str,
        number: str,
        neighborhood: str,
        zip_code: str,
        city: str,
        state: str,
    ) -> GeocodeResult | None:
        """Chama Mapbox Geocoding API e retorna lat/lng do endereço."""
        pass  # type: ignore[return-value]
