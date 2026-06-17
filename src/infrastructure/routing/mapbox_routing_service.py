"""US10-TK06/TK07 — MapboxRoutingService.
US10-TK18 — MapboxGeocodingService (stub).

Implementação concreta usando a Mapbox API:
- MapboxRoutingService.optimize_stop_order → Mapbox Optimization API v1
- MapboxRoutingService.get_route_info      → Mapbox Directions API
- MapboxGeocodingService.geocode_address   → Mapbox Geocoding API v5/v6
"""

from urllib.parse import quote

import requests
from loguru import logger

from src.domains.routing.dtos import GeocodeResult, RouteInfoResult
from src.domains.routing.service import IGeocodingService, IRoutingService
from src.infrastructure.middleware.request_id import get_request_id


class MapboxRoutingService(IRoutingService):
    """Calcula rotas e otimiza paradas via Mapbox API."""

    # US10-TK06
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    # US10-TK07
    def optimize_stop_order(
        self,
        stop_coordinates: list[dict],
        origin: dict | None = None,
        destination: dict | None = None,
    ) -> list[int]:
        """Chama Mapbox Optimization API v1 e retorna a sequência de visita das paradas.

        Args:
            stop_coordinates: lista de dicts com 'lng' e 'lat' (paradas intermediárias)
            origin, destination: pontos fixos de início/fim. Quando ambos são
                informados, viram âncoras (source=first / destination=last /
                roundtrip=false): origem fica em 1º, destino por último e só as
                paradas intermediárias são reordenadas entre elas.

        Returns:
            Lista de índices de `stop_coordinates` na ordem otimizada de visita.
            Origem/destino não entram no retorno.
        """
        if not stop_coordinates:
            return []

        anchored = origin is not None and destination is not None
        coords_list = [origin, *stop_coordinates, destination] if anchored else list(stop_coordinates)

        coords = ";".join(f"{c['lng']},{c['lat']}" for c in coords_list)
        url = f"https://api.mapbox.com/optimized-trips/v1/mapbox/driving/{coords}"
        params = {"access_token": self.api_key}
        if anchored:
            # Mantém origem como primeiro ponto e destino como último; não é roundtrip.
            params.update({"source": "first", "destination": "last", "roundtrip": "false"})

        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        # waypoints vêm na ordem dos coords de entrada; waypoint_index = posição
        # de cada ponto na rota otimizada. Invertendo, obtemos a sequência de visita
        # (qual ponto de entrada é visitado em cada posição).
        waypoints = data.get("waypoints", [])
        visiting_sequence = sorted(
            range(len(waypoints)),
            key=lambda input_pos: waypoints[input_pos]["waypoint_index"],
        )

        if not anchored:
            return visiting_sequence

        # Em modo ancorado os índices de entrada são: 0=origem, 1..N=paradas,
        # N+1=destino. Mantém só as paradas e mapeia de volta para o índice de
        # stop_coordinates (input_pos - 1), preservando a ordem de visita.
        stop_count = len(stop_coordinates)
        return [input_pos - 1 for input_pos in visiting_sequence if 1 <= input_pos <= stop_count]

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

        # timeout=5: evita worker travado se a Mapbox ficar lenta/indisponível.
        # Timeout/ConnectionError viram RequestException, propagam para o caller,
        # que já trata via try/except (best-effort no helper de routing).
        response = requests.get(url, params=params, timeout=5)
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

    _MIN_RELEVANCE = 0.5

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
        if not self.api_key:
            return None

        query_parts = [
            f"{number} {street}".strip(),
            neighborhood,
            city,
            state,
            zip_code,
            "Brazil",
        ]
        query = ", ".join(part for part in query_parts if part)

        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{quote(query, safe='')}.json"
        params = {
            "access_token": self.api_key,
            "country": "BR",
            "limit": 1,
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            features = data.get("features", [])
            if not features:
                return None

            feature = features[0]
            if feature.get("relevance", 0) < self._MIN_RELEVANCE:
                return None

            center = feature.get("center")
            if isinstance(center, list) and len(center) >= 2:
                return GeocodeResult(latitude=center[1], longitude=center[0])

            return None
        except Exception:
            request_id = get_request_id()
            logger.bind(request_id=request_id, trace_id=request_id).exception(
                "Mapbox geocoding failed",
                city=city,
                state=state,
                zip_code=zip_code,
            )
            return None
