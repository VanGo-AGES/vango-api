"""US10-TK06 / TK07 — Testes do IRoutingService e MapboxRoutingService."""

from unittest.mock import MagicMock, patch

import pytest


# ===========================================================================
# US10-TK06 — IRoutingService interface + DTOs + config + DI
# ===========================================================================


def test_irouting_service_is_abstract():
    """IRoutingService deve ser abstrata (não instanciável diretamente)."""
    from src.domains.routing.service import IRoutingService

    with pytest.raises(TypeError):
        IRoutingService()  # type: ignore[abstract]


def test_irouting_service_has_optimize_stop_order():
    """IRoutingService deve expor optimize_stop_order."""
    from src.domains.routing.service import IRoutingService

    assert hasattr(IRoutingService, "optimize_stop_order")


def test_irouting_service_has_get_route_info():
    """IRoutingService deve expor get_route_info."""
    from src.domains.routing.service import IRoutingService

    assert hasattr(IRoutingService, "get_route_info")


def test_route_info_result_valid():
    """RouteInfoResult deve ser instanciável com os campos esperados."""
    from src.domains.routing.dtos import RouteInfoResult

    result = RouteInfoResult(total_distance_km=12.5, estimated_duration_min=20)
    assert result.total_distance_km == 12.5
    assert result.estimated_duration_min == 20


def test_mapbox_routing_service_implements_interface():
    """MapboxRoutingService deve implementar IRoutingService."""
    from src.domains.routing.service import IRoutingService
    from src.infrastructure.routing.mapbox_routing_service import MapboxRoutingService

    service = MapboxRoutingService(api_key="test-key")
    assert isinstance(service, IRoutingService)


def test_mapbox_api_key_in_settings():
    """Settings deve expor mapbox_api_key."""
    from src.config import Settings

    assert hasattr(Settings.model_fields, "mapbox_api_key") or hasattr(Settings, "mapbox_api_key")


def test_get_routing_service_returns_instance():
    """get_routing_service deve retornar uma instância de IRoutingService."""
    from src.domains.routing.service import IRoutingService
    from src.infrastructure.dependencies.routing_dependencies import get_routing_service

    service = get_routing_service()
    assert isinstance(service, IRoutingService)


# ===========================================================================
# US10-TK07 — MapboxRoutingService: optimize_stop_order + get_route_info
# ===========================================================================


def test_optimize_stop_order_calls_mapbox_optimization_api():
    """optimize_stop_order deve chamar a Mapbox Optimization API v1."""
    from src.infrastructure.routing.mapbox_routing_service import MapboxRoutingService

    service = MapboxRoutingService(api_key="test-key")
    stops = [
        {"id": 0, "lat": -30.0, "lng": -51.2},
        {"id": 1, "lat": -30.1, "lng": -51.3},
        {"id": 2, "lat": -30.2, "lng": -51.1},
    ]

    with patch("requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "trips": [{"geometry": {}}],
                "waypoints": [
                    {"waypoint_index": 0},
                    {"waypoint_index": 2},
                    {"waypoint_index": 1},
                ],
            },
        )
        result = service.optimize_stop_order(stops)

    mock_get.assert_called_once()
    assert isinstance(result, list)
    assert len(result) == 3


def test_get_route_info_calls_mapbox_directions_api():
    """get_route_info deve chamar a Mapbox Directions API."""
    from src.infrastructure.routing.mapbox_routing_service import MapboxRoutingService

    service = MapboxRoutingService(api_key="test-key")
    origin = {"lat": -30.0, "lng": -51.0}
    destination = {"lat": -30.5, "lng": -51.5}
    waypoints = [{"lat": -30.2, "lng": -51.2}]

    with patch("requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "routes": [{"distance": 15000, "duration": 1200}]  # metros e segundos
            },
        )
        result = service.get_route_info(origin, waypoints, destination)

    mock_get.assert_called_once()
    assert result.total_distance_km == pytest.approx(15.0, rel=0.01)
    assert result.estimated_duration_min == 20


def test_get_route_info_returns_route_info_result():
    """get_route_info deve retornar uma instância de RouteInfoResult."""
    from src.domains.routing.dtos import RouteInfoResult
    from src.infrastructure.routing.mapbox_routing_service import MapboxRoutingService

    service = MapboxRoutingService(api_key="test-key")

    with patch("requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"routes": [{"distance": 8000, "duration": 600}]},
        )
        result = service.get_route_info(
            {"lat": -30.0, "lng": -51.0},
            [],
            {"lat": -30.1, "lng": -51.1},
        )

    assert isinstance(result, RouteInfoResult)
