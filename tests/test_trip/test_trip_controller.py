"""US09 — Controller de trips (unidade + integração).

Camada HTTP da execução de viagem. Os testes unitários mockam
TripService via dependency_override; os de integração exercitam HTTP
→ controller → service → repositórios → SQLite real.

Convenções:
- Headers: X-User-Id / X-User-Role = 'driver'
- Integration client sobrescreve apenas get_db.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from src.domains.trips.service import TripService
from src.infrastructure.database import get_db
from src.infrastructure.dependencies.trip_dependencies import get_trip_service
from src.main import app
from tests.test_trip._helpers import (
    make_address,
    make_driver,
    make_passenger,
    make_route,
    make_rp,
    make_stop,
    make_trip,
    make_trip_passanger,
    make_vehicle,
)

client = TestClient(app, raise_server_exceptions=False)
DRIVER_HEADERS = {"X-User-Id": str(uuid.uuid4()), "X-User-Role": "driver"}


# ===========================================================================
# Factories de DTO mock (para unidade)
# ===========================================================================


def make_trip_response(status: str = "iniciada"):
    from src.domains.trips.dtos import TripResponse

    payload = {
        "id": uuid.uuid4(),
        "route_id": uuid.uuid4(),
        "route_name": "PUCRS Manhã",
        "vehicle_id": uuid.uuid4(),
        "trip_date": datetime(2026, 4, 22, 7, 30, tzinfo=timezone.utc),
        "status": status,
        "total_km": None if status != "finalizada" else 12.5,
        "started_at": datetime(2026, 4, 22, 7, 30, tzinfo=timezone.utc),
        "finished_at": None
        if status != "finalizada"
        else datetime(2026, 4, 22, 8, 45, tzinfo=timezone.utc),
        "trip_passangers": [],
    }
    return TripResponse(**payload)


def make_trip_passanger_response(status: str = "pendente"):
    from src.domains.trips.dtos import TripPassangerResponse

    payload = {
        "id": uuid.uuid4(),
        "route_passanger_id": uuid.uuid4(),
        "passanger_name": "Maria Silva",
        "status": status,
        "pickup_address_label": "Rua X, 100",
        "boarded_at": datetime(2026, 4, 22, 7, 45, tzinfo=timezone.utc)
        if status == "presente"
        else None,
        "alighted_at": None,
        "user_phone": "51999990000",
    }
    return TripPassangerResponse(**payload)


def make_next_stop_response():
    from src.domains.trips.dtos import TripNextStopResponse

    payload = {
        "stop_id": uuid.uuid4(),
        "order_index": 1,
        "address_label": "Av. Ipiranga, 6681",
        "passanger_name": "João Silva",
        "passanger_phone": "51988887777",
        "trip_passanger_id": uuid.uuid4(),
        "trip_passanger_status": "pendente",
    }
    return TripNextStopResponse(**payload)


# ===========================================================================
# TK14 — POST /routes/{route_id}/trips (UNIDADE)
# ===========================================================================


@pytest.mark.skip(reason="US09-TK14")
def test_start_trip_success_returns_201() -> None:
    mock_service = Mock(spec=TripService)
    mock_service.start_trip.return_value = make_trip_response(status="iniciada")
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.post(
        f"/routes/{uuid.uuid4()}/trips",
        json={"vehicle_id": str(uuid.uuid4())},
        headers=DRIVER_HEADERS,
    )

    app.dependency_overrides.clear()
    assert response.status_code == 201
    assert response.json()["status"] == "iniciada"


@pytest.mark.skip(reason="US09-TK14")
def test_start_trip_route_not_found_returns_404() -> None:
    from src.domains.routes.errors import RouteNotFoundError

    mock_service = Mock(spec=TripService)
    mock_service.start_trip.side_effect = RouteNotFoundError()
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.post(
        f"/routes/{uuid.uuid4()}/trips",
        json={"vehicle_id": str(uuid.uuid4())},
        headers=DRIVER_HEADERS,
    )

    app.dependency_overrides.clear()
    assert response.status_code == 404


@pytest.mark.skip(reason="US09-TK14")
def test_start_trip_wrong_owner_returns_403() -> None:
    from src.domains.routes.errors import RouteOwnershipError

    mock_service = Mock(spec=TripService)
    mock_service.start_trip.side_effect = RouteOwnershipError()
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.post(
        f"/routes/{uuid.uuid4()}/trips",
        json={"vehicle_id": str(uuid.uuid4())},
        headers=DRIVER_HEADERS,
    )

    app.dependency_overrides.clear()
    assert response.status_code == 403


@pytest.mark.skip(reason="US09-TK14")
def test_start_trip_already_in_progress_returns_409() -> None:
    from src.domains.trips.errors import TripAlreadyInProgressError

    mock_service = Mock(spec=TripService)
    mock_service.start_trip.side_effect = TripAlreadyInProgressError()
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.post(
        f"/routes/{uuid.uuid4()}/trips",
        json={"vehicle_id": str(uuid.uuid4())},
        headers=DRIVER_HEADERS,
    )

    app.dependency_overrides.clear()
    assert response.status_code == 409


@pytest.mark.skip(reason="US09-TK14")
def test_start_trip_no_passangers_returns_409() -> None:
    from src.domains.trips.errors import NoPassangersToStartError

    mock_service = Mock(spec=TripService)
    mock_service.start_trip.side_effect = NoPassangersToStartError()
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.post(
        f"/routes/{uuid.uuid4()}/trips",
        json={"vehicle_id": str(uuid.uuid4())},
        headers=DRIVER_HEADERS,
    )

    app.dependency_overrides.clear()
    assert response.status_code == 409


@pytest.mark.skip(reason="US09-TK14")
def test_start_trip_vehicle_not_owned_returns_403() -> None:
    from src.domains.trips.errors import VehicleNotOwnedError

    mock_service = Mock(spec=TripService)
    mock_service.start_trip.side_effect = VehicleNotOwnedError()
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.post(
        f"/routes/{uuid.uuid4()}/trips",
        json={"vehicle_id": str(uuid.uuid4())},
        headers=DRIVER_HEADERS,
    )

    app.dependency_overrides.clear()
    assert response.status_code == 403


@pytest.mark.skip(reason="US09-TK14")
def test_start_trip_invalid_payload_returns_422() -> None:
    mock_service = Mock(spec=TripService)
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.post(
        f"/routes/{uuid.uuid4()}/trips",
        json={},  # vehicle_id obrigatório
        headers=DRIVER_HEADERS,
    )

    app.dependency_overrides.clear()
    assert response.status_code == 422


# ===========================================================================
# TK15 — GET /trips/{trip_id} (UNIDADE)
# ===========================================================================


@pytest.mark.skip(reason="US09-TK15")
def test_get_trip_success_returns_200() -> None:
    mock_service = Mock(spec=TripService)
    mock_service.get_current_trip.return_value = make_trip_response(status="iniciada")
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.get(f"/trips/{uuid.uuid4()}", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["status"] == "iniciada"


@pytest.mark.skip(reason="US09-TK15")
def test_get_trip_not_found_returns_404() -> None:
    from src.domains.trips.errors import TripNotFoundError

    mock_service = Mock(spec=TripService)
    mock_service.get_current_trip.side_effect = TripNotFoundError()
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.get(f"/trips/{uuid.uuid4()}", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 404


@pytest.mark.skip(reason="US09-TK15")
def test_get_trip_wrong_owner_returns_403() -> None:
    from src.domains.trips.errors import TripOwnershipError

    mock_service = Mock(spec=TripService)
    mock_service.get_current_trip.side_effect = TripOwnershipError()
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.get(f"/trips/{uuid.uuid4()}", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 403


# ===========================================================================
# TK16 — GET /trips/{trip_id}/next-stop (UNIDADE)
# ===========================================================================


@pytest.mark.skip(reason="US09-TK16")
def test_get_next_stop_success_returns_200() -> None:
    mock_service = Mock(spec=TripService)
    mock_service.get_next_stop.return_value = make_next_stop_response()
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.get(f"/trips/{uuid.uuid4()}/next-stop", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert "stop_id" in body
    assert "passanger_phone" in body


@pytest.mark.skip(reason="US09-TK16")
def test_get_next_stop_none_when_no_pending_returns_200() -> None:
    """Quando todos os passageiros já foram atendidos, retorna null (200)."""
    mock_service = Mock(spec=TripService)
    mock_service.get_next_stop.return_value = None
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.get(f"/trips/{uuid.uuid4()}/next-stop", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.skip(reason="US09-TK16")
def test_get_next_stop_trip_not_found_returns_404() -> None:
    from src.domains.trips.errors import TripNotFoundError

    mock_service = Mock(spec=TripService)
    mock_service.get_next_stop.side_effect = TripNotFoundError()
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.get(f"/trips/{uuid.uuid4()}/next-stop", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 404


@pytest.mark.skip(reason="US09-TK16")
def test_get_next_stop_wrong_owner_returns_403() -> None:
    from src.domains.trips.errors import TripOwnershipError

    mock_service = Mock(spec=TripService)
    mock_service.get_next_stop.side_effect = TripOwnershipError()
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.get(f"/trips/{uuid.uuid4()}/next-stop", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 403


# ===========================================================================
# TK17 — POST /trips/{trip_id}/passangers/{trip_passanger_id}/board (UNIDADE)
# ===========================================================================


@pytest.mark.skip(reason="US09-TK17")
def test_board_passanger_success_returns_200() -> None:
    mock_service = Mock(spec=TripService)
    mock_service.board_passanger.return_value = make_trip_passanger_response(status="presente")
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.post(
        f"/trips/{uuid.uuid4()}/passangers/{uuid.uuid4()}/board", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["status"] == "presente"


@pytest.mark.skip(reason="US09-TK17")
def test_board_passanger_trip_passanger_not_found_returns_404() -> None:
    from src.domains.trips.errors import TripPassangerNotFoundError

    mock_service = Mock(spec=TripService)
    mock_service.board_passanger.side_effect = TripPassangerNotFoundError()
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.post(
        f"/trips/{uuid.uuid4()}/passangers/{uuid.uuid4()}/board", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 404


@pytest.mark.skip(reason="US09-TK17")
def test_board_passanger_wrong_owner_returns_403() -> None:
    from src.domains.trips.errors import TripOwnershipError

    mock_service = Mock(spec=TripService)
    mock_service.board_passanger.side_effect = TripOwnershipError()
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.post(
        f"/trips/{uuid.uuid4()}/passangers/{uuid.uuid4()}/board", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 403


@pytest.mark.skip(reason="US09-TK17")
def test_board_passanger_trip_not_in_progress_returns_409() -> None:
    from src.domains.trips.errors import TripNotInProgressError

    mock_service = Mock(spec=TripService)
    mock_service.board_passanger.side_effect = TripNotInProgressError()
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.post(
        f"/trips/{uuid.uuid4()}/passangers/{uuid.uuid4()}/board", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 409


@pytest.mark.skip(reason="US09-TK17")
def test_board_passanger_invalid_status_returns_409() -> None:
    from src.domains.trips.errors import InvalidTripPassangerStatusError

    mock_service = Mock(spec=TripService)
    mock_service.board_passanger.side_effect = InvalidTripPassangerStatusError()
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.post(
        f"/trips/{uuid.uuid4()}/passangers/{uuid.uuid4()}/board", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 409


# ===========================================================================
# TK18 — POST /trips/{trip_id}/passangers/{trip_passanger_id}/absent (UNIDADE)
# ===========================================================================


def test_mark_absent_success_returns_200() -> None:
    mock_service = Mock(spec=TripService)
    mock_service.mark_passanger_absent.return_value = make_trip_passanger_response(status="ausente")
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.post(
        f"/trips/{uuid.uuid4()}/passangers/{uuid.uuid4()}/absent", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["status"] == "ausente"


def test_mark_absent_trip_passanger_not_found_returns_404() -> None:
    from src.domains.trips.errors import TripPassangerNotFoundError

    mock_service = Mock(spec=TripService)
    mock_service.mark_passanger_absent.side_effect = TripPassangerNotFoundError()
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.post(
        f"/trips/{uuid.uuid4()}/passangers/{uuid.uuid4()}/absent", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 404


def test_mark_absent_wrong_owner_returns_403() -> None:
    from src.domains.trips.errors import TripOwnershipError

    mock_service = Mock(spec=TripService)
    mock_service.mark_passanger_absent.side_effect = TripOwnershipError()
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.post(
        f"/trips/{uuid.uuid4()}/passangers/{uuid.uuid4()}/absent", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 403


def test_mark_absent_trip_not_in_progress_returns_409() -> None:
    from src.domains.trips.errors import TripNotInProgressError

    mock_service = Mock(spec=TripService)
    mock_service.mark_passanger_absent.side_effect = TripNotInProgressError()
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.post(
        f"/trips/{uuid.uuid4()}/passangers/{uuid.uuid4()}/absent", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 409


# ===========================================================================
# TK19 — POST /trips/{trip_id}/stops/{stop_id}/skip (UNIDADE)
# ===========================================================================


@pytest.mark.skip(reason="US09-TK19")
def test_skip_stop_success_returns_200_with_list() -> None:
    mock_service = Mock(spec=TripService)
    mock_service.skip_stop.return_value = [
        make_trip_passanger_response(status="ausente"),
    ]
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.post(
        f"/trips/{uuid.uuid4()}/stops/{uuid.uuid4()}/skip", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert body[0]["status"] == "ausente"


@pytest.mark.skip(reason="US09-TK19")
def test_skip_stop_stop_not_found_returns_404() -> None:
    from src.domains.trips.errors import TripStopNotFoundError

    mock_service = Mock(spec=TripService)
    mock_service.skip_stop.side_effect = TripStopNotFoundError()
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.post(
        f"/trips/{uuid.uuid4()}/stops/{uuid.uuid4()}/skip", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 404


@pytest.mark.skip(reason="US09-TK19")
def test_skip_stop_wrong_owner_returns_403() -> None:
    from src.domains.trips.errors import TripOwnershipError

    mock_service = Mock(spec=TripService)
    mock_service.skip_stop.side_effect = TripOwnershipError()
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.post(
        f"/trips/{uuid.uuid4()}/stops/{uuid.uuid4()}/skip", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 403


@pytest.mark.skip(reason="US09-TK19")
def test_skip_stop_trip_not_in_progress_returns_409() -> None:
    from src.domains.trips.errors import TripNotInProgressError

    mock_service = Mock(spec=TripService)
    mock_service.skip_stop.side_effect = TripNotInProgressError()
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.post(
        f"/trips/{uuid.uuid4()}/stops/{uuid.uuid4()}/skip", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 409


# ===========================================================================
# TK20 — POST /trips/{trip_id}/passangers/{trip_passanger_id}/alight (UNIDADE)
# ===========================================================================


@pytest.mark.skip(reason="US09-TK20")
def test_alight_passanger_success_returns_200() -> None:
    mock_service = Mock(spec=TripService)
    response_dto = make_trip_passanger_response(status="presente")
    response_dto.alighted_at = datetime(2026, 4, 22, 8, 0, tzinfo=timezone.utc)
    mock_service.alight_passanger.return_value = response_dto
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.post(
        f"/trips/{uuid.uuid4()}/passangers/{uuid.uuid4()}/alight", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["alighted_at"] is not None


@pytest.mark.skip(reason="US09-TK20")
def test_alight_passanger_not_found_returns_404() -> None:
    from src.domains.trips.errors import TripPassangerNotFoundError

    mock_service = Mock(spec=TripService)
    mock_service.alight_passanger.side_effect = TripPassangerNotFoundError()
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.post(
        f"/trips/{uuid.uuid4()}/passangers/{uuid.uuid4()}/alight", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 404


@pytest.mark.skip(reason="US09-TK20")
def test_alight_passanger_invalid_status_returns_409() -> None:
    from src.domains.trips.errors import InvalidTripPassangerStatusError

    mock_service = Mock(spec=TripService)
    mock_service.alight_passanger.side_effect = InvalidTripPassangerStatusError()
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.post(
        f"/trips/{uuid.uuid4()}/passangers/{uuid.uuid4()}/alight", headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 409


# ===========================================================================
# TK21 — POST /trips/{trip_id}/finish (UNIDADE)
# ===========================================================================


@pytest.mark.skip(reason="US09-TK21")
def test_finish_trip_success_returns_200() -> None:
    mock_service = Mock(spec=TripService)
    mock_service.finish_trip.return_value = make_trip_response(status="finalizada")
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.post(
        f"/trips/{uuid.uuid4()}/finish", json={"total_km": 12.5}, headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["status"] == "finalizada"


@pytest.mark.skip(reason="US09-TK21")
def test_finish_trip_without_total_km_returns_200() -> None:
    """total_km é opcional."""
    mock_service = Mock(spec=TripService)
    mock_service.finish_trip.return_value = make_trip_response(status="finalizada")
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.post(
        f"/trips/{uuid.uuid4()}/finish", json={}, headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200


@pytest.mark.skip(reason="US09-TK21")
def test_finish_trip_not_found_returns_404() -> None:
    from src.domains.trips.errors import TripNotFoundError

    mock_service = Mock(spec=TripService)
    mock_service.finish_trip.side_effect = TripNotFoundError()
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.post(
        f"/trips/{uuid.uuid4()}/finish", json={"total_km": 10.0}, headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 404


@pytest.mark.skip(reason="US09-TK21")
def test_finish_trip_wrong_owner_returns_403() -> None:
    from src.domains.trips.errors import TripOwnershipError

    mock_service = Mock(spec=TripService)
    mock_service.finish_trip.side_effect = TripOwnershipError()
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.post(
        f"/trips/{uuid.uuid4()}/finish", json={"total_km": 10.0}, headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 403


@pytest.mark.skip(reason="US09-TK21")
def test_finish_trip_already_finished_returns_409() -> None:
    from src.domains.trips.errors import TripAlreadyFinishedError

    mock_service = Mock(spec=TripService)
    mock_service.finish_trip.side_effect = TripAlreadyFinishedError()
    app.dependency_overrides[get_trip_service] = lambda: mock_service

    response = client.post(
        f"/trips/{uuid.uuid4()}/finish", json={"total_km": 10.0}, headers=DRIVER_HEADERS
    )

    app.dependency_overrides.clear()
    assert response.status_code == 409


# ===========================================================================
# INTEGRAÇÃO — testes ponta a ponta (HTTP → controller → service → repo → DB)
# Não mocka service nem repositório. Apenas get_db.
# ===========================================================================


@pytest.fixture
def integration_client(db_session):
    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def _driver_headers(driver_id) -> dict:
    return {"X-User-Id": str(driver_id), "X-User-Role": "driver"}


# ---------------------------------------------------------------------------
# TK14 — POST /routes/{route_id}/trips (INTEGRAÇÃO)
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US09-TK14")
def test_integration_start_trip_success(integration_client, db_session) -> None:
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    passenger = make_passenger(db_session)
    route = make_route(db_session, driver.id)
    rp = make_rp(db_session, route.id, passenger.id, status="accepted")
    addr = make_address(db_session, passenger.id, "Casa")
    make_stop(db_session, route.id, rp.id, addr.id)

    response = integration_client.post(
        f"/routes/{route.id}/trips",
        json={"vehicle_id": str(vehicle.id)},
        headers=_driver_headers(driver.id),
    )

    assert response.status_code == 201
    assert response.json()["status"] == "iniciada"


@pytest.mark.skip(reason="US09-TK14")
def test_integration_start_trip_persists_trip_passangers(integration_client, db_session) -> None:
    """Ao iniciar, trip_passangers deve ser pré-preenchido a partir dos rp aceitos."""
    from src.domains.trips.entity import TripPassangerModel

    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    p1 = make_passenger(db_session, "A")
    p2 = make_passenger(db_session, "B")
    route = make_route(db_session, driver.id)
    rp1 = make_rp(db_session, route.id, p1.id, status="accepted")
    rp2 = make_rp(db_session, route.id, p2.id, status="accepted")
    addr1 = make_address(db_session, p1.id)
    addr2 = make_address(db_session, p2.id)
    make_stop(db_session, route.id, rp1.id, addr1.id, order_index=1)
    make_stop(db_session, route.id, rp2.id, addr2.id, order_index=2)

    response = integration_client.post(
        f"/routes/{route.id}/trips",
        json={"vehicle_id": str(vehicle.id)},
        headers=_driver_headers(driver.id),
    )

    assert response.status_code == 201
    trip_id = uuid.UUID(response.json()["id"])
    tps = (
        db_session.query(TripPassangerModel)
        .filter(TripPassangerModel.trip_id == trip_id)
        .all()
    )
    assert len(tps) == 2


@pytest.mark.skip(reason="US09-TK14")
def test_integration_start_trip_already_in_progress_returns_409(
    integration_client, db_session
) -> None:
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)
    passenger = make_passenger(db_session)
    rp = make_rp(db_session, route.id, passenger.id, status="accepted")
    addr = make_address(db_session, passenger.id)
    make_stop(db_session, route.id, rp.id, addr.id)
    make_trip(db_session, route.id, vehicle.id, status="iniciada")

    response = integration_client.post(
        f"/routes/{route.id}/trips",
        json={"vehicle_id": str(vehicle.id)},
        headers=_driver_headers(driver.id),
    )

    assert response.status_code == 409


@pytest.mark.skip(reason="US09-TK14")
def test_integration_start_trip_no_passangers_returns_409(integration_client, db_session) -> None:
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)

    response = integration_client.post(
        f"/routes/{route.id}/trips",
        json={"vehicle_id": str(vehicle.id)},
        headers=_driver_headers(driver.id),
    )

    assert response.status_code == 409


@pytest.mark.skip(reason="US09-TK14")
def test_integration_start_trip_wrong_owner_returns_403(integration_client, db_session) -> None:
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    other_driver = make_driver(db_session, name="Outro")
    route = make_route(db_session, driver.id)

    response = integration_client.post(
        f"/routes/{route.id}/trips",
        json={"vehicle_id": str(vehicle.id)},
        headers=_driver_headers(other_driver.id),
    )

    assert response.status_code == 403


@pytest.mark.skip(reason="US09-TK14")
def test_integration_start_trip_vehicle_not_owned_returns_403(
    integration_client, db_session
) -> None:
    driver = make_driver(db_session)
    other_driver = make_driver(db_session, name="Outro")
    vehicle = make_vehicle(db_session, other_driver.id)
    route = make_route(db_session, driver.id)

    response = integration_client.post(
        f"/routes/{route.id}/trips",
        json={"vehicle_id": str(vehicle.id)},
        headers=_driver_headers(driver.id),
    )

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# TK15 — GET /trips/{trip_id} (INTEGRAÇÃO)
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US09-TK15")
def test_integration_get_trip_success(integration_client, db_session) -> None:
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)
    trip = make_trip(db_session, route.id, vehicle.id)

    response = integration_client.get(
        f"/trips/{trip.id}", headers=_driver_headers(driver.id)
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(trip.id)


@pytest.mark.skip(reason="US09-TK15")
def test_integration_get_trip_not_found_returns_404(integration_client, db_session) -> None:
    driver = make_driver(db_session)

    response = integration_client.get(
        f"/trips/{uuid.uuid4()}", headers=_driver_headers(driver.id)
    )

    assert response.status_code == 404


@pytest.mark.skip(reason="US09-TK15")
def test_integration_get_trip_wrong_owner_returns_403(integration_client, db_session) -> None:
    driver = make_driver(db_session)
    other = make_driver(db_session, name="Outro")
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)
    trip = make_trip(db_session, route.id, vehicle.id)

    response = integration_client.get(
        f"/trips/{trip.id}", headers=_driver_headers(other.id)
    )

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# TK16 — GET /trips/{trip_id}/next-stop (INTEGRAÇÃO)
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US09-TK16")
def test_integration_next_stop_returns_first_pending(integration_client, db_session) -> None:
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)
    passenger = make_passenger(db_session)
    rp = make_rp(db_session, route.id, passenger.id, status="accepted")
    addr = make_address(db_session, passenger.id, "Rua Casa")
    make_stop(db_session, route.id, rp.id, addr.id, order_index=1)
    trip = make_trip(db_session, route.id, vehicle.id)
    make_trip_passanger(db_session, trip.id, rp.id, status="pendente")

    response = integration_client.get(
        f"/trips/{trip.id}/next-stop", headers=_driver_headers(driver.id)
    )

    assert response.status_code == 200
    body = response.json()
    assert body is not None
    assert body["trip_passanger_status"] == "pendente"


@pytest.mark.skip(reason="US09-TK16")
def test_integration_next_stop_returns_null_when_all_done(integration_client, db_session) -> None:
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)
    passenger = make_passenger(db_session)
    rp = make_rp(db_session, route.id, passenger.id, status="accepted")
    addr = make_address(db_session, passenger.id)
    make_stop(db_session, route.id, rp.id, addr.id, order_index=1)
    trip = make_trip(db_session, route.id, vehicle.id)
    make_trip_passanger(db_session, trip.id, rp.id, status="presente")

    response = integration_client.get(
        f"/trips/{trip.id}/next-stop", headers=_driver_headers(driver.id)
    )

    assert response.status_code == 200
    assert response.json() is None


# ---------------------------------------------------------------------------
# TK17 — POST /trips/{trip_id}/passangers/{trip_passanger_id}/board (INTEGRAÇÃO)
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US09-TK17")
def test_integration_board_passanger_success(integration_client, db_session) -> None:
    from src.domains.trips.entity import TripPassangerModel

    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)
    passenger = make_passenger(db_session)
    rp = make_rp(db_session, route.id, passenger.id, status="accepted")
    trip = make_trip(db_session, route.id, vehicle.id)
    tp = make_trip_passanger(db_session, trip.id, rp.id, status="pendente")

    response = integration_client.post(
        f"/trips/{trip.id}/passangers/{tp.id}/board",
        headers=_driver_headers(driver.id),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "presente"
    refreshed = db_session.query(TripPassangerModel).filter_by(id=tp.id).first()
    assert refreshed.boarded_at is not None


@pytest.mark.skip(reason="US09-TK17")
def test_integration_board_trip_finished_returns_409(integration_client, db_session) -> None:
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)
    passenger = make_passenger(db_session)
    rp = make_rp(db_session, route.id, passenger.id, status="accepted")
    trip = make_trip(db_session, route.id, vehicle.id, status="finalizada")
    tp = make_trip_passanger(db_session, trip.id, rp.id, status="pendente")

    response = integration_client.post(
        f"/trips/{trip.id}/passangers/{tp.id}/board",
        headers=_driver_headers(driver.id),
    )

    assert response.status_code == 409


# ---------------------------------------------------------------------------
# TK18 — POST /trips/{trip_id}/passangers/{trip_passanger_id}/absent (INTEGRAÇÃO)
# ---------------------------------------------------------------------------


def test_integration_mark_absent_success(integration_client, db_session) -> None:
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)
    passenger = make_passenger(db_session)
    rp = make_rp(db_session, route.id, passenger.id, status="accepted")
    trip = make_trip(db_session, route.id, vehicle.id)
    tp = make_trip_passanger(db_session, trip.id, rp.id, status="pendente")

    response = integration_client.post(
        f"/trips/{trip.id}/passangers/{tp.id}/absent",
        headers=_driver_headers(driver.id),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ausente"


def test_integration_mark_absent_wrong_owner_returns_403(integration_client, db_session) -> None:
    driver = make_driver(db_session)
    other = make_driver(db_session, name="Outro")
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)
    passenger = make_passenger(db_session)
    rp = make_rp(db_session, route.id, passenger.id, status="accepted")
    trip = make_trip(db_session, route.id, vehicle.id)
    tp = make_trip_passanger(db_session, trip.id, rp.id, status="pendente")

    response = integration_client.post(
        f"/trips/{trip.id}/passangers/{tp.id}/absent",
        headers=_driver_headers(other.id),
    )

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# TK19 — POST /trips/{trip_id}/stops/{stop_id}/skip (INTEGRAÇÃO)
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US09-TK19")
def test_integration_skip_stop_marks_passangers_absent(integration_client, db_session) -> None:
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)
    passenger = make_passenger(db_session)
    rp = make_rp(db_session, route.id, passenger.id, status="accepted")
    addr = make_address(db_session, passenger.id)
    stop = make_stop(db_session, route.id, rp.id, addr.id, order_index=1)
    trip = make_trip(db_session, route.id, vehicle.id)
    make_trip_passanger(db_session, trip.id, rp.id, status="pendente")

    response = integration_client.post(
        f"/trips/{trip.id}/stops/{stop.id}/skip",
        headers=_driver_headers(driver.id),
    )

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 1
    assert body[0]["status"] == "ausente"


@pytest.mark.skip(reason="US09-TK19")
def test_integration_skip_stop_not_found_returns_404(integration_client, db_session) -> None:
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)
    trip = make_trip(db_session, route.id, vehicle.id)

    response = integration_client.post(
        f"/trips/{trip.id}/stops/{uuid.uuid4()}/skip",
        headers=_driver_headers(driver.id),
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# TK20 — POST /trips/{trip_id}/passangers/{trip_passanger_id}/alight (INTEGRAÇÃO)
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US09-TK20")
def test_integration_alight_passanger_success(integration_client, db_session) -> None:
    from src.domains.trips.entity import TripPassangerModel

    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)
    passenger = make_passenger(db_session)
    rp = make_rp(db_session, route.id, passenger.id, status="accepted")
    trip = make_trip(db_session, route.id, vehicle.id)
    tp = make_trip_passanger(db_session, trip.id, rp.id, status="presente")
    tp.boarded_at = datetime.now(timezone.utc)
    db_session.flush()

    response = integration_client.post(
        f"/trips/{trip.id}/passangers/{tp.id}/alight",
        headers=_driver_headers(driver.id),
    )

    assert response.status_code == 200
    refreshed = db_session.query(TripPassangerModel).filter_by(id=tp.id).first()
    assert refreshed.alighted_at is not None


@pytest.mark.skip(reason="US09-TK20")
def test_integration_alight_when_absent_returns_409(integration_client, db_session) -> None:
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)
    passenger = make_passenger(db_session)
    rp = make_rp(db_session, route.id, passenger.id, status="accepted")
    trip = make_trip(db_session, route.id, vehicle.id)
    tp = make_trip_passanger(db_session, trip.id, rp.id, status="ausente")

    response = integration_client.post(
        f"/trips/{trip.id}/passangers/{tp.id}/alight",
        headers=_driver_headers(driver.id),
    )

    assert response.status_code == 409


# ---------------------------------------------------------------------------
# TK21 — POST /trips/{trip_id}/finish (INTEGRAÇÃO)
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="US09-TK21")
def test_integration_finish_trip_success(integration_client, db_session) -> None:
    from src.domains.trips.entity import TripModel

    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)
    trip = make_trip(db_session, route.id, vehicle.id, status="iniciada")

    response = integration_client.post(
        f"/trips/{trip.id}/finish",
        json={"total_km": 12.5},
        headers=_driver_headers(driver.id),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "finalizada"
    refreshed = db_session.query(TripModel).filter_by(id=trip.id).first()
    assert refreshed.finished_at is not None
    assert refreshed.total_km == 12.5


@pytest.mark.skip(reason="US09-TK21")
def test_integration_finish_trip_auto_alights_presents(integration_client, db_session) -> None:
    """Ao finalizar, passageiros 'presente' sem alighted_at devem ser auto-desembarcados."""
    from src.domains.trips.entity import TripPassangerModel

    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)
    passenger = make_passenger(db_session)
    rp = make_rp(db_session, route.id, passenger.id, status="accepted")
    trip = make_trip(db_session, route.id, vehicle.id, status="iniciada")
    tp = make_trip_passanger(db_session, trip.id, rp.id, status="presente")
    tp.boarded_at = datetime.now(timezone.utc)
    db_session.flush()

    response = integration_client.post(
        f"/trips/{trip.id}/finish",
        json={},
        headers=_driver_headers(driver.id),
    )

    assert response.status_code == 200
    refreshed = db_session.query(TripPassangerModel).filter_by(id=tp.id).first()
    assert refreshed.alighted_at is not None


@pytest.mark.skip(reason="US09-TK21")
def test_integration_finish_trip_already_finished_returns_409(
    integration_client, db_session
) -> None:
    driver = make_driver(db_session)
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)
    trip = make_trip(db_session, route.id, vehicle.id, status="finalizada")

    response = integration_client.post(
        f"/trips/{trip.id}/finish",
        json={"total_km": 8.0},
        headers=_driver_headers(driver.id),
    )

    assert response.status_code == 409


@pytest.mark.skip(reason="US09-TK21")
def test_integration_finish_trip_wrong_owner_returns_403(integration_client, db_session) -> None:
    driver = make_driver(db_session)
    other = make_driver(db_session, name="Outro")
    vehicle = make_vehicle(db_session, driver.id)
    route = make_route(db_session, driver.id)
    trip = make_trip(db_session, route.id, vehicle.id, status="iniciada")

    response = integration_client.post(
        f"/trips/{trip.id}/finish",
        json={"total_km": 10.0},
        headers=_driver_headers(other.id),
    )

    assert response.status_code == 403
