"""US10-TK19 — Helper compartilhado pra calcular totais planejados de uma rota.

Usado por:
- RouteService.get_route / get_routes → preenche total_distance_km e
  estimated_duration_min em RouteResponse
- RoutePassangerService.list_my_routes → preenche em PassangerRouteResponse
- RoutePassangerService.get_my_route_detail → preenche em PassangerRouteDetailResponse

A função recebe uma RouteModel (com origin_address, destination_address e
stops já carregadas via joinedload) e o IRoutingService injetado.
Retorna (total_distance_km, estimated_duration_min) ou (None, None) se:
- routing_service for None
- algum endereço estiver sem latitude/longitude
- IRoutingService.get_route_info levantar exceção

Nunca propaga exceção — totais são best-effort.
"""

from src.domains.routes.entity import RouteModel
from src.domains.routing.service import IRoutingService

_route_totals_cache: dict[tuple[int, float, float, tuple[tuple[float, float], ...], float, float], tuple[float | None, int | None]] = {}


def _address_to_coordinate(address: object | None) -> dict[str, float] | None:
    if address is None:
        return None

    latitude = getattr(address, "latitude", None)
    longitude = getattr(address, "longitude", None)
    if latitude is None or longitude is None:
        return None

    return {"lat": latitude, "lng": longitude}


def _cache_key(
    origin: dict[str, float],
    waypoints: list[dict[str, float]],
    destination: dict[str, float],
) -> tuple[float, float, tuple[tuple[float, float], ...], float, float]:
    return (
        origin["lat"],
        origin["lng"],
        tuple((wp["lat"], wp["lng"]) for wp in waypoints),
        destination["lat"],
        destination["lng"],
    )


def compute_route_totals(
    route: RouteModel,
    routing_service: IRoutingService | None,
) -> tuple[float | None, int | None]:
    """Calcula total_distance_km e estimated_duration_min de uma rota planejada.

    Lê origin, destination e stops (ordenadas por order_index) do RouteModel,
    monta a lista de coordenadas e chama IRoutingService.get_route_info.
    Retorna (None, None) em qualquer cenário de falha — geocoding-like
    best-effort.
    """
    if routing_service is None:
        return None, None

    origin = _address_to_coordinate(getattr(route, "origin_address", None))
    destination = _address_to_coordinate(getattr(route, "destination_address", None))
    if origin is None or destination is None:
        return None, None

    stops = sorted(getattr(route, "stops", []) or [], key=lambda s: getattr(s, "order_index", 0))
    waypoints: list[dict[str, float]] = []
    for stop in stops:
        waypoint = _address_to_coordinate(getattr(stop, "address", None))
        if waypoint is None:
            return None, None
        waypoints.append(waypoint)

    cache_key = (id(routing_service),) + _cache_key(origin, waypoints, destination)
    if cache_key in _route_totals_cache:
        return _route_totals_cache[cache_key]

    try:
        result = routing_service.get_route_info(origin, waypoints, destination)
    except Exception:
        return None, None

    totals = (result.total_distance_km, result.estimated_duration_min)
    _route_totals_cache[cache_key] = totals
    return totals
