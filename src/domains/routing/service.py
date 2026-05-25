"""US10-TK06 — Interface IRoutingService.
US10-TK18 — Interface IGeocodingService."""

from abc import ABC, abstractmethod

from src.domains.routing.dtos import GeocodeResult, RouteInfoResult


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


# US10-TK18
class IGeocodingService(ABC):
    """Interface para resolução de endereços em coordenadas geográficas.

    Existe como contrato separado de IRoutingService porque geocoding é uma
    responsabilidade distinta (forward geocoding: endereço → coords) e tem
    uma API própria do Mapbox. Mantida separada para permitir injeção
    independente nos services que criam endereços (routes.create_route,
    route_passangers.join_route).
    """

    # US10-TK18
    @abstractmethod
    def geocode_address(
        self,
        street: str,
        number: str,
        neighborhood: str,
        zip_code: str,
        city: str,
        state: str,
    ) -> GeocodeResult | None:
        """Resolve um endereço brasileiro em latitude/longitude via Mapbox
        Geocoding API.

        Parâmetros: campos textuais do AddressModel.

        Retorno:
          GeocodeResult com latitude e longitude se a API encontrou
          coordenadas para o endereço.
          None se: endereço não pôde ser resolvido, API indisponível,
          ou resposta sem coordenadas confiáveis (relevance abaixo de
          limiar configurado pela implementação).

        Implementações nunca devem levantar exceção em uso normal —
        falhas devem virar None para que o fluxo de criação de endereço
        siga adiante mesmo sem coordenadas.
        """
        pass
