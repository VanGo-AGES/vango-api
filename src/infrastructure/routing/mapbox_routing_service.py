"""US10-TK06/TK07 — MapboxRoutingService.

Implementação concreta de IRoutingService usando a Mapbox API.
- optimize_stop_order: Mapbox Optimization API v1
- get_route_info:      Mapbox Directions API
"""

import requests

from src.domains.routing.dtos import RouteInfoResult
from src.domains.routing.service import IRoutingService


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
        # Monta coordenadas em formato "lng,lat;lng,lat;..."
        coords = ";".join(f"{stop['lng']},{stop['lat']}" for stop in stop_coordinates)

        url = f"https://api.mapbox.com/optimized-trips/v1/mapbox/driving/{coords}"
        params = {"access_token": self.api_key}

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Extrai os waypoint_index de cada waypoint na resposta
        # A ordem de waypoints[i]["waypoint_index"] representa a ordem otimizada
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
        # Monta coordenadas: origin;waypoint1;waypoint2;...;destination
        coordinates = [origin] + waypoints + [destination]
        coords = ";".join(f"{coord['lng']},{coord['lat']}" for coord in coordinates)

        url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{coords}"
        params = {"access_token": self.api_key}

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Extrai distância (metros) e duração (segundos) da primeira rota
        route = data.get("routes", [{}])[0]
        distance_m = route.get("distance", 0)
        duration_s = route.get("duration", 0)

        # Converte: metros → km, segundos → minutos
        total_distance_km = distance_m / 1000
        estimated_duration_min = int(duration_s / 60)

        return RouteInfoResult(
            total_distance_km=total_distance_km,
            estimated_duration_min=estimated_duration_min,
        )
