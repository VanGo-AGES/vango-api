"""US10-TK06 — Interface IRoutingService.
US10-TK18 — Interface IGeocodingService."""

from abc import ABC, abstractmethod

from src.domains.routing.dtos import GeocodeResult, RouteInfoResult


class IRoutingService(ABC):
    """Interface para cálculo de rotas e otimização de paradas."""

    # US10-TK07
    @abstractmethod
    def optimize_stop_order(
        self,
        stop_coordinates: list[dict],
        origin: dict | None = None,
        destination: dict | None = None,
    ) -> list[int]:
        """Reordena as paradas pelo menor tempo de percurso via Mapbox Optimization API v1.

        Parâmetros:
          stop_coordinates: lista de dicts { "id": any, "lat": float, "lng": float }
            com as paradas intermediárias (embarques) na ordem atual.
          origin, destination: dicts { "lat": float, "lng": float } com os pontos
            fixos de início e fim da rota. Quando AMBOS são informados, são tratados
            como âncoras (source=first / destination=last / roundtrip=false): só as
            paradas intermediárias são reordenadas, mantendo origem em 1º e destino
            por último. Se algum for None, cai no modo livre (sem âncoras).

        Retorno:
          Sequência de visita das paradas: lista de índices de `stop_coordinates`
          na nova ordem. Ex.: [0, 2, 1] significa visitar a parada 0, depois a 2,
          depois a 1. Origem/destino NÃO entram no retorno.
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
