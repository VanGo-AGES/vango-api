"""US10-TK06/TK07 — MapboxRoutingService.
US10-TK18 — MapboxGeocodingService (stub).

Implementação concreta usando a Mapbox API:
- MapboxRoutingService.optimize_stop_order → Mapbox Optimization API v1
- MapboxRoutingService.get_route_info      → Mapbox Directions API
- MapboxGeocodingService.geocode_address   → Mapbox Geocoding API v5/v6
"""

import requests

from src.domains.routing.dtos import GeocodeResult, RouteInfoResult
from src.domains.routing.service import IGeocodingService, IRoutingService


class MapboxRoutingService(IRoutingService):
    """Calcula rotas e otimiza paradas via Mapbox API."""

    # US10-TK06
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    # US10-TK07
    def optimize_stop_order(self, stop_coordinates: list[dict]) -> list[int]:
        """Chama Mapbox Optimization API v1 e retorna a ordem otimizada.

        Args:
            stop_coordinates: lista de dicts com 'lng' e 'lat'

        Returns:
            lista de índices originais na nova sequência otimizada
        """
        coords = ";".join(f"{stop['lng']},{stop['lat']}" for stop in stop_coordinates)

        url = f"https://api.mapbox.com/optimized-trips/v1/mapbox/driving/{coords}"
        params = {"access_token": self.api_key}

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        waypoints = data.get("waypoints", [])
        optimized_order = [wp["waypoint_index"] for wp in waypoints]

        return optimized_order

    # US10-TK07
    def get_route_info(
        self,
        origin: dict,
        waypoints: list[dict],
        destination: dict,
    ) -> RouteInfoResult:
        """Chama Mapbox Directions API e retorna distância e duração.

        Args:
            origin: dict com 'lng' e 'lat'
            waypoints: lista de dicts com 'lng' e 'lat'
            destination: dict com 'lng' e 'lat'

        Returns:
            RouteInfoResult com total_distance_km e estimated_duration_min
        """
        coordinates = [origin] + waypoints + [destination]
        coords = ";".join(f"{coord['lng']},{coord['lat']}" for coord in coordinates)

        url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{coords}"
        params = {"access_token": self.api_key}

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        route = data.get("routes", [{}])[0]
        distance_m = route.get("distance", 0)
        duration_s = route.get("duration", 0)

        total_distance_km = distance_m / 1000
        estimated_duration_min = int(duration_s / 60)

        return RouteInfoResult(
            total_distance_km=total_distance_km,
            estimated_duration_min=estimated_duration_min,
        )


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
