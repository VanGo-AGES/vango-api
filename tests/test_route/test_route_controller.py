import uuid
from datetime import time
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from src.domains.routes.service import RouteService
from src.infrastructure.dependencies.route_dependencies import get_route_service
from src.main import app

client = TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_route_response_mock(driver_id: uuid.UUID = None):
    from src.domains.routes.dtos import AddressResponse, RouteResponse

    addr = AddressResponse(
        id=uuid.uuid4(),
        label="Casa",
        street="Av. Coronel Marcos",
        number="861",
        neighborhood="Três Figueiras",
        zip="91760-000",
        city="Porto Alegre",
        state="RS",
    )
    return RouteResponse(
        id=uuid.uuid4(),
        name="PUCRS",
        route_type="outbound",
        status="inativa",
        recurrence="seg,ter,qua,qui,sex",
        expected_time=time(8, 0),
        invite_code="A1B2C",
        max_passengers=5,
        origin_address=addr,
        destination_address=addr,
    )


def make_route_payload(**kwargs) -> dict:
    defaults = {
        "name": "PUCRS",
        "route_type": "outbound",
        "origin": {
            "label": "Casa",
            "street": "Av. Coronel Marcos",
            "number": "861",
            "neighborhood": "Três Figueiras",
            "zip": "91760-000",
            "city": "Porto Alegre",
            "state": "RS",
        },
        "destination": {
            "label": "PUCRS",
            "street": "Av. Ipiranga",
            "number": "6681",
            "neighborhood": "Partenon",
            "zip": "90619-900",
            "city": "Porto Alegre",
            "state": "RS",
        },
        "expected_time": "08:00:00",
        "recurrence": "seg,ter,qua,qui,sex",
    }
    defaults.update(kwargs)
    return defaults


DRIVER_HEADERS = {"X-User-Id": str(uuid.uuid4()), "X-User-Role": "driver"}


# ===========================================================================
# US05 - TK04: POST /routes/ — criar rota
# Arquivo:     src/domains/routes/controller.py
# ===========================================================================


@pytest.mark.skip(reason="US05-TK04")
def test_create_route_success_returns_201() -> None:
    """POST /routes/ com payload válido deve retornar 201 e a rota criada."""
    mock_service = Mock(spec=RouteService)
    mock_service.create_route.return_value = make_route_response_mock()
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.post("/routes/", json=make_route_payload(), headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 201
    assert response.json()["invite_code"] == "A1B2C"


@pytest.mark.skip(reason="US05-TK04")
def test_create_route_missing_name_returns_422() -> None:
    """POST /routes/ sem nome deve retornar 422."""
    payload = make_route_payload()
    del payload["name"]
    response = client.post("/routes/", json=payload, headers=DRIVER_HEADERS)
    assert response.status_code == 422


@pytest.mark.skip(reason="US05-TK04")
def test_create_route_invalid_route_type_returns_422() -> None:
    """POST /routes/ com route_type inválido deve retornar 422."""
    response = client.post("/routes/", json=make_route_payload(route_type="ambos"), headers=DRIVER_HEADERS)
    assert response.status_code == 422


@pytest.mark.skip(reason="US05-TK04")
def test_create_route_invalid_recurrence_returns_422() -> None:
    """POST /routes/ com dias de recorrência inválidos deve retornar 422."""
    response = client.post("/routes/", json=make_route_payload(recurrence="monday,tuesday"), headers=DRIVER_HEADERS)
    assert response.status_code == 422


@pytest.mark.skip(reason="US05-TK04")
def test_create_route_no_vehicle_returns_400() -> None:
    """POST /routes/ quando motorista não tem veículo deve retornar 400."""
    from src.domains.routes.errors import NoVehicleError

    mock_service = Mock(spec=RouteService)
    mock_service.create_route.side_effect = NoVehicleError()
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.post("/routes/", json=make_route_payload(), headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 400


@pytest.mark.skip(reason="US05-TK04")
def test_create_route_response_has_correct_fields() -> None:
    """A resposta deve conter todos os campos esperados incluindo endereços aninhados."""
    mock_service = Mock(spec=RouteService)
    mock_service.create_route.return_value = make_route_response_mock()
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.post("/routes/", json=make_route_payload(), headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    body = response.json()
    assert "invite_code" in body
    assert "origin_address" in body
    assert "destination_address" in body
    assert "status" in body
    assert body["status"] == "inativa"


# ===========================================================================
# US05 - TK05: POST /routes/{id}/invite-code/regenerate
# Arquivo:     src/domains/routes/controller.py
# ===========================================================================


@pytest.mark.skip(reason="US05-TK05")
def test_regenerate_invite_code_success_returns_200() -> None:
    """POST /routes/{id}/invite-code/regenerate deve retornar 200 com novo código."""
    route_id = uuid.uuid4()
    updated = make_route_response_mock()
    updated.invite_code = "NEW99"

    mock_service = Mock(spec=RouteService)
    mock_service.regenerate_invite_code.return_value = updated
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.post(f"/routes/{route_id}/invite-code/regenerate", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["invite_code"] == "NEW99"


@pytest.mark.skip(reason="US05-TK05")
def test_regenerate_invite_code_not_found_returns_404() -> None:
    """POST /routes/{id}/invite-code/regenerate com rota inexistente deve retornar 404."""
    from src.domains.routes.errors import RouteNotFoundError

    mock_service = Mock(spec=RouteService)
    mock_service.regenerate_invite_code.side_effect = RouteNotFoundError()
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.post(f"/routes/{uuid.uuid4()}/invite-code/regenerate", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 404


@pytest.mark.skip(reason="US05-TK05")
def test_regenerate_invite_code_wrong_owner_returns_403() -> None:
    """POST /routes/{id}/invite-code/regenerate por motorista que não é dono deve retornar 403."""
    from src.domains.routes.errors import RouteOwnershipError

    mock_service = Mock(spec=RouteService)
    mock_service.regenerate_invite_code.side_effect = RouteOwnershipError()
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.post(f"/routes/{uuid.uuid4()}/invite-code/regenerate", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 403


# ===========================================================================
# US07 - TK04: GET /routes/ e GET /routes/{id}
# Arquivo:     src/domains/routes/controller.py
# ===========================================================================


@pytest.mark.skip(reason="US07-TK04")
def test_list_routes_success_returns_200() -> None:
    """GET /routes/ deve retornar 200 e lista de rotas do motorista."""
    mock_service = Mock(spec=RouteService)
    mock_service.get_routes.return_value = [make_route_response_mock(), make_route_response_mock()]
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.get("/routes/", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.skip(reason="US07-TK04")
def test_list_routes_empty_returns_empty_list() -> None:
    """GET /routes/ sem rotas deve retornar 200 com lista vazia."""
    mock_service = Mock(spec=RouteService)
    mock_service.get_routes.return_value = []
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.get("/routes/", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.skip(reason="US07-TK04")
def test_get_route_success_returns_200() -> None:
    """GET /routes/{id} deve retornar 200 com dados completos da rota."""
    route_id = uuid.uuid4()
    mock_service = Mock(spec=RouteService)
    mock_service.get_route.return_value = make_route_response_mock()
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.get(f"/routes/{route_id}", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert "origin_address" in body
    assert "destination_address" in body


@pytest.mark.skip(reason="US07-TK04")
def test_get_route_not_found_returns_404() -> None:
    """GET /routes/{id} com rota inexistente deve retornar 404."""
    from src.domains.routes.errors import RouteNotFoundError

    mock_service = Mock(spec=RouteService)
    mock_service.get_route.side_effect = RouteNotFoundError()
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.get(f"/routes/{uuid.uuid4()}", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 404


@pytest.mark.skip(reason="US07-TK04")
def test_get_route_wrong_owner_returns_403() -> None:
    """GET /routes/{id} por motorista que não é dono deve retornar 403."""
    from src.domains.routes.errors import RouteOwnershipError

    mock_service = Mock(spec=RouteService)
    mock_service.get_route.side_effect = RouteOwnershipError()
    app.dependency_overrides[get_route_service] = lambda: mock_service

    response = client.get(f"/routes/{uuid.uuid4()}", headers=DRIVER_HEADERS)

    app.dependency_overrides.clear()
    assert response.status_code == 403
