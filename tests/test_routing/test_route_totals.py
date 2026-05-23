"""US10-TK19 — Testes do helper compartilhado compute_route_totals.

Cobre:
- Caso happy path: origin + stops + destination com coords → tupla
  com (km, min) vindos de IRoutingService.get_route_info
- Cenários de falha que devem retornar (None, None):
  - routing_service is None
  - origin sem coords
  - destination sem coords
  - alguma stop sem coords (decisão de impl — minha sugestão é continuar
    sem essa stop como waypoint, mas o teste documenta o contrato escolhido)
  - get_route_info levanta exceção
- Ordem dos waypoints: stops devem ser passadas ordenadas por order_index

Todos os testes skipados com US10-TK19 até o helper ser implementado.
"""

from unittest.mock import MagicMock

import pytest


def _make_address_mock(lat: float | None = -30.0, lng: float | None = -51.0):
    from src.domains.addresses.entity import AddressModel

    addr = MagicMock(spec=AddressModel)
    addr.latitude = lat
    addr.longitude = lng
    return addr


def _make_stop_mock(order_index: int, lat: float | None = -30.0, lng: float | None = -51.0):
    from src.domains.stops.entity import StopModel

    stop = MagicMock(spec=StopModel)
    stop.order_index = order_index
    stop.address = _make_address_mock(lat=lat, lng=lng)
    return stop


def _make_route_mock(stops=None, origin_coords=(-30.0, -51.0), destination_coords=(-30.1, -51.1)):
    from src.domains.routes.entity import RouteModel

    route = MagicMock(spec=RouteModel)
    route.origin_address = _make_address_mock(lat=origin_coords[0], lng=origin_coords[1])
    route.destination_address = _make_address_mock(lat=destination_coords[0], lng=destination_coords[1])
    route.stops = stops or []
    return route



def test_compute_route_totals_returns_tuple_when_all_addresses_have_coords():
    """Caso happy path: retorna (distance_km, duration_min) do IRoutingService.get_route_info."""
    from src.domains.routing.dtos import RouteInfoResult
    from src.domains.routing.route_totals import compute_route_totals

    route = _make_route_mock(
        stops=[
            _make_stop_mock(order_index=1, lat=-30.05, lng=-51.05),
            _make_stop_mock(order_index=2, lat=-30.07, lng=-51.07),
        ],
    )

    routing_mock = MagicMock()
    routing_mock.get_route_info.return_value = RouteInfoResult(
        total_distance_km=10.5, estimated_duration_min=32
    )

    distance, duration = compute_route_totals(route, routing_mock)

    assert distance == pytest.approx(10.5)
    assert duration == 32



def test_compute_route_totals_returns_none_when_routing_service_none():
    """routing_service=None → (None, None) sem nenhuma chamada externa."""
    from src.domains.routing.route_totals import compute_route_totals

    route = _make_route_mock()
    distance, duration = compute_route_totals(route, None)

    assert distance is None
    assert duration is None



def test_compute_route_totals_returns_none_when_origin_missing_coords():
    """origin.latitude/longitude None → (None, None) sem chamar routing."""
    from src.domains.routing.route_totals import compute_route_totals

    route = _make_route_mock(origin_coords=(None, None))
    routing_mock = MagicMock()

    distance, duration = compute_route_totals(route, routing_mock)

    assert distance is None
    assert duration is None
    routing_mock.get_route_info.assert_not_called()



def test_compute_route_totals_returns_none_when_destination_missing_coords():
    """destination sem coords → (None, None) sem chamar routing."""
    from src.domains.routing.route_totals import compute_route_totals

    route = _make_route_mock(destination_coords=(None, None))
    routing_mock = MagicMock()

    distance, duration = compute_route_totals(route, routing_mock)

    assert distance is None
    assert duration is None
    routing_mock.get_route_info.assert_not_called()



def test_compute_route_totals_returns_none_when_routing_raises():
    """Exceção em get_route_info → (None, None) sem propagar."""
    from src.domains.routing.route_totals import compute_route_totals

    route = _make_route_mock(stops=[_make_stop_mock(order_index=1)])
    routing_mock = MagicMock()
    routing_mock.get_route_info.side_effect = RuntimeError("mapbox down")

    distance, duration = compute_route_totals(route, routing_mock)

    assert distance is None
    assert duration is None



def test_compute_route_totals_passes_waypoints_in_order_index_order():
    """Stops devem ser enviadas como waypoints na ordem de order_index crescente."""
    from src.domains.routing.dtos import RouteInfoResult
    from src.domains.routing.route_totals import compute_route_totals

    # propositalmente fora de ordem na lista
    route = _make_route_mock(
        stops=[
            _make_stop_mock(order_index=3, lat=-30.30, lng=-51.30),
            _make_stop_mock(order_index=1, lat=-30.10, lng=-51.10),
            _make_stop_mock(order_index=2, lat=-30.20, lng=-51.20),
        ],
    )

    routing_mock = MagicMock()
    routing_mock.get_route_info.return_value = RouteInfoResult(
        total_distance_km=12.0, estimated_duration_min=40
    )

    compute_route_totals(route, routing_mock)

    routing_mock.get_route_info.assert_called_once()
    call = routing_mock.get_route_info.call_args
    waypoints = call.kwargs.get("waypoints") or call.args[1]

    # Esperamos waypoints na ordem 1, 2, 3 (independente da ordem da lista)
    assert len(waypoints) == 3
    assert waypoints[0]["lat"] == pytest.approx(-30.10)
    assert waypoints[1]["lat"] == pytest.approx(-30.20)
    assert waypoints[2]["lat"] == pytest.approx(-30.30)



def test_compute_route_totals_works_without_stops():
    """Rota sem stops (só origem+destino) deve calcular normalmente."""
    from src.domains.routing.dtos import RouteInfoResult
    from src.domains.routing.route_totals import compute_route_totals

    route = _make_route_mock(stops=[])
    routing_mock = MagicMock()
    routing_mock.get_route_info.return_value = RouteInfoResult(
        total_distance_km=5.0, estimated_duration_min=15
    )

    distance, duration = compute_route_totals(route, routing_mock)

    assert distance == pytest.approx(5.0)
    assert duration == 15
    routing_mock.get_route_info.assert_called_once()
    call = routing_mock.get_route_info.call_args
    waypoints = call.kwargs.get("waypoints") or call.args[1]
    assert waypoints == []
