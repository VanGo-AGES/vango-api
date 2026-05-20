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
    pass  # type: ignore[return-value]
