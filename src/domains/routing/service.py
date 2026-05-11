"""US10-TK06 — Interface IRoutingService."""

from abc import ABC, abstractmethod

from src.domains.routing.dtos import RouteInfoResult


class IRoutingService(ABC):
    """Interface para cálculo de rotas e otimização de paradas."""

    # US10-TK07
    @abstractmethod
    def optimize_stop_order(self, stop_coordinates: list[dict]) -> list[int]:
        """Reordena as paradas pelo menor tempo de percurso via Mapbox Optimization API v1.

        Parâmetro:
          stop_coordinates: lista de dicts { "id": any, "lat": float, "lng": float }
            na ordem atual das paradas.

        Retorno:
          Lista de índices originais na nova ordem otimizada.
          Ex.: [0, 2, 1] significa que a parada 0 fica em 1º, a 2 em 2º e a 1 em 3º.
        """
        pass

    # US10-TK07
    @abstractmethod
    def get_route_info(
        self,
        origin: dict,
        waypoints: list[dict],
        destination: dict,
    ) -> RouteInfoResult:
        """Calcula distância total e duração estimada via Mapbox Directions API.

        Parâmetros:
          origin, destination: dicts { "lat": float, "lng": float }
          waypoints: lista de paradas intermediárias no mesmo formato.

        Retorno:
          RouteInfoResult com total_distance_km e estimated_duration_min.
        """
        pass
