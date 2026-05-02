"""US06-TK20 — Testes do AbsenceController (POST /absences).

Cobre:
- unit tests (mockando AbsenceService via app.dependency_overrides)
- integration tests (stack real com db em memória)
"""

import uuid
from datetime import date, datetime, time, timezone, timedelta
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from src.domains.absences.service import AbsenceService
from src.domains.addresses.entity import AddressModel
from src.domains.route_passangers.entity import RoutePassangerModel
from src.domains.routes.entity import RouteModel
from src.domains.users.entity import UserModel
from src.infrastructure.database import get_db
from src.infrastructure.dependencies.absence_dependencies import get_absence_service
from src.main import app

client = TestClient(app, raise_server_exceptions=False)

PASSENGER_HEADERS = {"X-User-Id": str(uuid.uuid4()), "X-User-Role": "guardian"}


def future_weekday_iso():
    target = date.today() + timedelta(days=5)

    while target.weekday() > 4:  # seg-sex
        target += timedelta(days=1)

    return target.isoformat()


def make_absence_response(reason: str | None = "Consulta"):
    from src.domains.absences.dtos import AbsenceResponse

    return AbsenceResponse(
        id=uuid.uuid4(),
        route_passanger_id=uuid.uuid4(),
        absence_date=datetime(2026, 4, 27, 0, 0, tzinfo=timezone.utc),
        reason=reason,
        created_at=datetime.now(tz=timezone.utc),
    )


def valid_payload(**overrides) -> dict:
    payload = {
        "route_id": str(uuid.uuid4()),
        "absence_date": date(2026, 4, 27).isoformat(),
    }
    payload.update(overrides)
    return payload


# ===========================================================================
# US06-TK20 — unit (mocked service)
# ===========================================================================


def test_create_absence_success_returns_201() -> None:
    mock_service = Mock(spec=AbsenceService)
    mock_service.create_absence.return_value = make_absence_response()
    app.dependency_overrides[get_absence_service] = lambda: mock_service

    response = client.post("/absences", json=valid_payload(), headers=PASSENGER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 201
    assert response.json()["reason"] == "Consulta"


def test_create_absence_route_not_found_returns_404() -> None:
    from src.domains.routes.errors import RouteNotFoundError

    mock_service = Mock(spec=AbsenceService)
    mock_service.create_absence.side_effect = RouteNotFoundError()
    app.dependency_overrides[get_absence_service] = lambda: mock_service

    response = client.post("/absences", json=valid_payload(), headers=PASSENGER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 404


def test_create_absence_not_passanger_returns_403() -> None:
    from src.domains.route_passangers.errors import NotRoutePassangerError

    mock_service = Mock(spec=AbsenceService)
    mock_service.create_absence.side_effect = NotRoutePassangerError()
    app.dependency_overrides[get_absence_service] = lambda: mock_service

    response = client.post("/absences", json=valid_payload(), headers=PASSENGER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 403


def test_create_absence_duplicate_returns_409() -> None:
    from src.domains.absences.errors import AbsenceAlreadyReportedError

    mock_service = Mock(spec=AbsenceService)
    mock_service.create_absence.side_effect = AbsenceAlreadyReportedError()
    app.dependency_overrides[get_absence_service] = lambda: mock_service

    response = client.post("/absences", json=valid_payload(), headers=PASSENGER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 409


def test_create_absence_invalid_date_returns_409() -> None:
    from src.domains.absences.errors import AbsenceDateNotAllowedError

    mock_service = Mock(spec=AbsenceService)
    mock_service.create_absence.side_effect = AbsenceDateNotAllowedError()
    app.dependency_overrides[get_absence_service] = lambda: mock_service

    response = client.post("/absences", json=valid_payload(), headers=PASSENGER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 409


def test_create_absence_missing_body_fields_returns_422() -> None:
    mock_service = Mock(spec=AbsenceService)
    app.dependency_overrides[get_absence_service] = lambda: mock_service

    response = client.post("/absences", json={}, headers=PASSENGER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 422


def test_create_absence_forwards_user_id_from_header() -> None:
    mock_service = Mock(spec=AbsenceService)
    mock_service.create_absence.return_value = make_absence_response()
    app.dependency_overrides[get_absence_service] = lambda: mock_service

    user_id = uuid.uuid4()
    headers = {"X-User-Id": str(user_id), "X-User-Role": "guardian"}
    client.post("/absences", json=valid_payload(), headers=headers)

    app.dependency_overrides.clear()
    call = mock_service.create_absence.call_args
    assert user_id in call.args or call.kwargs.get("user_id") == user_id


# ===========================================================================
# US06-TK20 — integração (stack real)
# ===========================================================================


@pytest.fixture
def integration_client(db_session):
    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def make_integration_driver(db_session):
    driver = UserModel(
        name="Motorista Int",
        email=f"driver_{uuid.uuid4()}@test.com",
        phone="11999999999",
        password_hash="hashed",
        role="driver",
    )
    db_session.add(driver)
    db_session.flush()
    return driver


def make_integration_passenger(db_session, name: str = "Passageiro"):
    user = UserModel(
        name=name,
        email=f"pass_{uuid.uuid4()}@test.com",
        phone="11999999999",
        password_hash="hashed",
        role="guardian",
    )
    db_session.add(user)
    db_session.flush()
    return user


def make_integration_route(db_session, driver_id, recurrence: str = "seg,ter,qua,qui,sex"):
    origin = AddressModel(
        user_id=driver_id,
        label="Casa",
        street="R. A",
        number="1",
        neighborhood="N",
        zip="90000-000",
        city="Porto Alegre",
        state="RS",
    )
    dest = AddressModel(
        user_id=driver_id,
        label="PUCRS",
        street="R. B",
        number="2",
        neighborhood="N",
        zip="90000-000",
        city="Porto Alegre",
        state="RS",
    )
    db_session.add_all([origin, dest])
    db_session.flush()

    route = RouteModel(
        driver_id=driver_id,
        origin_address_id=origin.id,
        destination_address_id=dest.id,
        name="PUCRS",
        route_type="outbound",
        recurrence=recurrence,
        max_passengers=4,
        expected_time=time(8, 0),
        status="ativa",
        invite_code=f"IT{str(uuid.uuid4())[:3].upper()}",
    )
    db_session.add(route)
    db_session.flush()
    return route


def make_integration_rp(db_session, route_id, user_id, status: str = "accepted"):
    pickup = AddressModel(
        user_id=user_id,
        label="Casa Passageiro",
        street="R. X",
        number="100",
        neighborhood="C",
        zip="90000-000",
        city="Porto Alegre",
        state="RS",
    )
    db_session.add(pickup)
    db_session.flush()
    rp = RoutePassangerModel(
        route_id=route_id,
        user_id=user_id,
        status=status,
        pickup_address_id=pickup.id,
    )
    db_session.add(rp)
    db_session.flush()
    return rp


def test_integration_create_absence_success(integration_client, db_session) -> None:
    driver = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session)
    route = make_integration_route(db_session, driver.id)
    make_integration_rp(db_session, route.id, passenger.id, status="accepted")

    headers = {"X-User-Id": str(passenger.id), "X-User-Role": "guardian"}
    response = integration_client.post(
        "/absences",
        json={
            "route_id": str(route.id),
            "absence_date": future_weekday_iso(),
            "reason": "Consulta",
        },
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["reason"] == "Consulta"


def test_integration_create_absence_route_not_found_returns_404(
    integration_client, db_session
) -> None:
    passenger = make_integration_passenger(db_session)
    headers = {"X-User-Id": str(passenger.id), "X-User-Role": "guardian"}

    response = integration_client.post(
        "/absences",
        json={"route_id": str(uuid.uuid4()), "absence_date": future_weekday_iso()},
        headers=headers,
    )

    assert response.status_code == 404


def test_integration_create_absence_outsider_returns_403(
    integration_client, db_session
) -> None:
    driver = make_integration_driver(db_session)
    outsider = make_integration_passenger(db_session, "Outsider")
    route = make_integration_route(db_session, driver.id)

    headers = {"X-User-Id": str(outsider.id), "X-User-Role": "guardian"}
    response = integration_client.post(
        "/absences",
        json={"route_id": str(route.id), "absence_date": future_weekday_iso()},
        headers=headers,
    )

    assert response.status_code == 403


def test_integration_create_absence_duplicate_returns_409(
    integration_client, db_session
) -> None:
    driver = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session)
    route = make_integration_route(db_session, driver.id)
    make_integration_rp(db_session, route.id, passenger.id, status="accepted")

    headers = {"X-User-Id": str(passenger.id), "X-User-Role": "guardian"}
    payload = {"route_id": str(route.id), "absence_date": future_weekday_iso()}

    first = integration_client.post("/absences", json=payload, headers=headers)
    assert first.status_code == 201

    second = integration_client.post("/absences", json=payload, headers=headers)
    assert second.status_code == 409


def test_integration_create_absence_persists_in_db(
    integration_client, db_session
) -> None:
    from src.domains.trips.entity import AbsenceModel

    driver = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session)
    route = make_integration_route(db_session, driver.id)
    rp = make_integration_rp(db_session, route.id, passenger.id, status="accepted")

    headers = {"X-User-Id": str(passenger.id), "X-User-Role": "guardian"}
    integration_client.post(
        "/absences",
        json={"route_id": str(route.id), "absence_date": future_weekday_iso()},
        headers=headers,
    )

    stored = db_session.query(AbsenceModel).filter_by(route_passanger_id=rp.id).all()
    assert len(stored) == 1


def test_integration_create_absence_invalid_recurrence_returns_409(
    integration_client, db_session
) -> None:
    """Rota recorre só em segundas; avisar ausência em sábado deve dar 409."""
    driver = make_integration_driver(db_session)
    passenger = make_integration_passenger(db_session)
    route = make_integration_route(db_session, driver.id, recurrence="seg")
    make_integration_rp(db_session, route.id, passenger.id, status="accepted")

    headers = {"X-User-Id": str(passenger.id), "X-User-Role": "guardian"}
    response = integration_client.post(
        "/absences",
        json={"route_id": str(route.id), "absence_date": "2026-04-25"},  # sábado
        headers=headers,
    )

    assert response.status_code == 409
