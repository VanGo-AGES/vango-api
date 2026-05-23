"""US09 — Tests unitários do TripService (mocks de repositórios).

Cada sub-sessão corresponde a uma TK (TK06 a TK13). Os testes validam
ordem de chamadas, transição de estado, erros de domínio, e que o service
não acessa o banco diretamente.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from src.domains.notifications.service import INotificationService
from src.domains.route_passangers.entity import RoutePassangerModel
from src.domains.route_passangers.repository import IRoutePassangerRepository
from src.domains.routes.entity import RouteModel
from src.domains.routes.repository import IRouteRepository
from src.domains.stops.entity import StopModel
from src.domains.stops.repository import IStopRepository
from src.domains.trips.dtos import FinishTripRequest, StartTripRequest
from src.domains.trips.entity import AbsenceModel, TripModel, TripPassangerModel
from src.domains.trips.errors import (
    InvalidTripPassangerStatusError,
    NoPassangersToStartError,
    TripAlreadyFinishedError,
    TripAlreadyInProgressError,
    TripNotFoundError,
    TripNotInProgressError,
    TripOwnershipError,
    TripPassangerNotFoundError,
    TripStopNotFoundError,
    VehicleNotOwnedError,
)
from src.domains.trips.repository import (
    IAbsenceRepository,
    ITripPassangerRepository,
    ITripRepository,
)
from src.domains.trips.service import TripService
from src.domains.vehicles.entity import VehicleModel
from src.domains.vehicles.repository import IVehicleRepository


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def make_service(**overrides):
    trip_repo = Mock(spec=ITripRepository)
    tp_repo = Mock(spec=ITripPassangerRepository)
    absence_repo = Mock(spec=IAbsenceRepository)
    route_repo = Mock(spec=IRouteRepository)
    rp_repo = Mock(spec=IRoutePassangerRepository)
    stop_repo = Mock(spec=IStopRepository)
    vehicle_repo = Mock(spec=IVehicleRepository)
    notification = Mock(spec=INotificationService)

    mocks = {
        "trip_repo": trip_repo,
        "tp_repo": tp_repo,
        "absence_repo": absence_repo,
        "route_repo": route_repo,
        "rp_repo": rp_repo,
        "stop_repo": stop_repo,
        "vehicle_repo": vehicle_repo,
        "notification": notification,
    }
    mocks.update(overrides)

    service = TripService(
        mocks["trip_repo"],
        mocks["tp_repo"],
        mocks["absence_repo"],
        mocks["route_repo"],
        mocks["rp_repo"],
        mocks["stop_repo"],
        mocks["vehicle_repo"],
        mocks["notification"],
    )
    return service, mocks


def make_route_mock(driver_id=None, status: str = "ativa") -> RouteModel:
    route = Mock(spec=RouteModel)
    route.id = uuid.uuid4()
    route.driver_id = driver_id or uuid.uuid4()
    route.status = status
    route.name = "PUCRS Manhã"
    return route


def make_vehicle_mock(driver_id=None) -> VehicleModel:
    v = Mock(spec=VehicleModel)
    v.id = uuid.uuid4()
    v.driver_id = driver_id or uuid.uuid4()
    v.capacity = 4
    return v


def make_rp_mock(route_id=None, status: str = "accepted") -> RoutePassangerModel:
    rp = Mock(spec=RoutePassangerModel)
    rp.id = uuid.uuid4()
    rp.route_id = route_id or uuid.uuid4()
    rp.user_id = uuid.uuid4()
    rp.dependent_id = None
    rp.status = status
    return rp


def make_trip_mock(route_id=None, status: str = "iniciada") -> TripModel:
    trip = Mock(spec=TripModel)
    trip.id = uuid.uuid4()
    trip.route_id = route_id or uuid.uuid4()
    trip.vehicle_id = uuid.uuid4()
    trip.trip_date = datetime.now(timezone.utc)
    trip.status = status
    trip.started_at = datetime.now(timezone.utc)
    trip.finished_at = None
    trip.total_km = None
    return trip


def make_tp_mock(trip_id=None, status: str = "pendente") -> TripPassangerModel:
    tp = Mock(spec=TripPassangerModel)
    tp.id = uuid.uuid4()
    tp.trip_id = trip_id or uuid.uuid4()
    tp.route_passanger_id = uuid.uuid4()
    tp.status = status
    tp.boarded_at = None
    tp.alighted_at = None
    return tp


# ===========================================================================
# US09-TK06 — start_trip
# ===========================================================================


def test_start_trip_happy_path_creates_trip_and_trip_passangers() -> None:
    service, mocks = make_service()
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id=driver_id, status="ativa")
    vehicle = make_vehicle_mock(driver_id=driver_id)
    rp1 = make_rp_mock(route_id=route.id, status="accepted")
    rp2 = make_rp_mock(route_id=route.id, status="accepted")
    saved_trip = make_trip_mock(route_id=route.id, status="iniciada")

    mocks["route_repo"].find_by_id.return_value = route
    mocks["vehicle_repo"].find_by_id.return_value = vehicle
    mocks["trip_repo"].find_in_progress_by_route.return_value = None
    mocks["rp_repo"].find_by_route_and_status.return_value = [rp1, rp2]
    mocks["absence_repo"].find_by_route_and_date.return_value = []
    mocks["trip_repo"].save.return_value = saved_trip
    mocks["tp_repo"].save_all.return_value = []

    service.start_trip(route.id, driver_id, StartTripRequest(vehicle_id=vehicle.id))

    mocks["trip_repo"].save.assert_called_once()
    mocks["tp_repo"].save_all.assert_called_once()
    mocks["notification"].notify_trip_started.assert_called_once_with(saved_trip)


def test_start_trip_sets_absent_for_preannounced_absences() -> None:
    service, mocks = make_service()
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id=driver_id)
    vehicle = make_vehicle_mock(driver_id=driver_id)
    rp1 = make_rp_mock(route_id=route.id, status="accepted")
    rp2 = make_rp_mock(route_id=route.id, status="accepted")
    absence = Mock(spec=AbsenceModel)
    absence.route_passanger_id = rp1.id

    mocks["route_repo"].find_by_id.return_value = route
    mocks["vehicle_repo"].find_by_id.return_value = vehicle
    mocks["trip_repo"].find_in_progress_by_route.return_value = None
    mocks["rp_repo"].find_by_route_and_status.return_value = [rp1, rp2]
    mocks["absence_repo"].find_by_route_and_date.return_value = [absence]
    mocks["trip_repo"].save.return_value = make_trip_mock(route_id=route.id)

    service.start_trip(route.id, driver_id, StartTripRequest(vehicle_id=vehicle.id))

    saved_list = mocks["tp_repo"].save_all.call_args.args[0]
    by_rp = {tp.route_passanger_id: tp.status for tp in saved_list}
    assert by_rp[rp1.id] == "ausente"
    assert by_rp[rp2.id] == "pendente"


def test_start_trip_updates_route_status_to_em_andamento() -> None:
    service, mocks = make_service()
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id=driver_id)
    vehicle = make_vehicle_mock(driver_id=driver_id)

    mocks["route_repo"].find_by_id.return_value = route
    mocks["vehicle_repo"].find_by_id.return_value = vehicle
    mocks["trip_repo"].find_in_progress_by_route.return_value = None
    mocks["rp_repo"].find_by_route_and_status.return_value = [make_rp_mock(route_id=route.id)]
    mocks["absence_repo"].find_by_route_and_date.return_value = []
    mocks["trip_repo"].save.return_value = make_trip_mock(route_id=route.id)

    service.start_trip(route.id, driver_id, StartTripRequest(vehicle_id=vehicle.id))

    mocks["route_repo"].update.assert_called_once()
    call = mocks["route_repo"].update.call_args
    assert call.args[0] == route.id
    assert call.args[1].get("status") == "em_andamento"


def test_start_trip_raises_when_route_not_found() -> None:
    service, mocks = make_service()
    mocks["route_repo"].find_by_id.return_value = None
    with pytest.raises(TripNotFoundError):
        service.start_trip(uuid.uuid4(), uuid.uuid4(), StartTripRequest(vehicle_id=uuid.uuid4()))


def test_start_trip_raises_when_driver_is_not_owner() -> None:
    service, mocks = make_service()
    route = make_route_mock(driver_id=uuid.uuid4())
    mocks["route_repo"].find_by_id.return_value = route
    with pytest.raises(TripOwnershipError):
        service.start_trip(route.id, uuid.uuid4(), StartTripRequest(vehicle_id=uuid.uuid4()))


def test_start_trip_raises_when_trip_already_in_progress() -> None:
    service, mocks = make_service()
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id=driver_id)
    vehicle = make_vehicle_mock(driver_id=driver_id)
    mocks["route_repo"].find_by_id.return_value = route
    mocks["vehicle_repo"].find_by_id.return_value = vehicle
    mocks["trip_repo"].find_in_progress_by_route.return_value = make_trip_mock(route_id=route.id)

    with pytest.raises(TripAlreadyInProgressError):
        service.start_trip(route.id, driver_id, StartTripRequest(vehicle_id=vehicle.id))


def test_start_trip_raises_when_vehicle_not_owned() -> None:
    service, mocks = make_service()
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id=driver_id)
    vehicle = make_vehicle_mock(driver_id=uuid.uuid4())  # outro dono
    mocks["route_repo"].find_by_id.return_value = route
    mocks["vehicle_repo"].find_by_id.return_value = vehicle

    with pytest.raises(VehicleNotOwnedError):
        service.start_trip(route.id, driver_id, StartTripRequest(vehicle_id=vehicle.id))


def test_start_trip_raises_when_no_accepted_passangers() -> None:
    service, mocks = make_service()
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id=driver_id)
    vehicle = make_vehicle_mock(driver_id=driver_id)
    mocks["route_repo"].find_by_id.return_value = route
    mocks["vehicle_repo"].find_by_id.return_value = vehicle
    mocks["trip_repo"].find_in_progress_by_route.return_value = None
    mocks["rp_repo"].find_by_route_and_status.return_value = []

    with pytest.raises(NoPassangersToStartError):
        service.start_trip(route.id, driver_id, StartTripRequest(vehicle_id=vehicle.id))


# ===========================================================================
# US09-TK07 — get_current_trip
# ===========================================================================


def test_get_current_trip_returns_response() -> None:
    service, mocks = make_service()
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id=driver_id)
    trip = make_trip_mock(route_id=route.id)
    trip.route = route
    trip.trip_passangers = []

    mocks["trip_repo"].find_by_id.return_value = trip
    result = service.get_current_trip(trip.id, driver_id)

    assert result is not None
    assert result.id == trip.id


def test_get_current_trip_raises_when_not_found() -> None:
    service, mocks = make_service()
    mocks["trip_repo"].find_by_id.return_value = None
    with pytest.raises(TripNotFoundError):
        service.get_current_trip(uuid.uuid4(), uuid.uuid4())


def test_get_current_trip_raises_when_wrong_owner() -> None:
    service, mocks = make_service()
    route = make_route_mock(driver_id=uuid.uuid4())
    trip = make_trip_mock(route_id=route.id)
    trip.route = route
    mocks["trip_repo"].find_by_id.return_value = trip
    with pytest.raises(TripOwnershipError):
        service.get_current_trip(trip.id, uuid.uuid4())


# ===========================================================================
# US09-TK08 — get_next_stop
# ===========================================================================


def test_get_next_stop_returns_first_pending() -> None:
    service, mocks = make_service()
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id=driver_id)
    trip = make_trip_mock(route_id=route.id)
    trip.route = route
    tp_done = make_tp_mock(trip_id=trip.id, status="presente")
    tp_pending = make_tp_mock(trip_id=trip.id, status="pendente")

    mocks["trip_repo"].find_by_id.return_value = trip
    mocks["tp_repo"].find_by_trip.return_value = [tp_done, tp_pending]

    result = service.get_next_stop(trip.id, driver_id)
    assert result is not None
    assert result.trip_passanger_id == tp_pending.id


def test_get_next_stop_returns_none_when_no_pending() -> None:
    service, mocks = make_service()
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id=driver_id)
    trip = make_trip_mock(route_id=route.id)
    trip.route = route
    mocks["trip_repo"].find_by_id.return_value = trip
    mocks["tp_repo"].find_by_trip.return_value = [make_tp_mock(trip_id=trip.id, status="presente")]

    assert service.get_next_stop(trip.id, driver_id) is None


def test_get_next_stop_raises_when_wrong_owner() -> None:
    service, mocks = make_service()
    route = make_route_mock(driver_id=uuid.uuid4())
    trip = make_trip_mock(route_id=route.id)
    trip.route = route
    mocks["trip_repo"].find_by_id.return_value = trip
    with pytest.raises(TripOwnershipError):
        service.get_next_stop(trip.id, uuid.uuid4())


# ===========================================================================
# US09-TK09 — board_passanger
# ===========================================================================


def test_board_passanger_marks_presente_and_boarded_at() -> None:
    service, mocks = make_service()
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id=driver_id)
    trip = make_trip_mock(route_id=route.id, status="iniciada")
    trip.route = route
    tp = make_tp_mock(trip_id=trip.id, status="pendente")
    updated = make_tp_mock(trip_id=trip.id, status="presente")
    updated.boarded_at = datetime.now(timezone.utc)

    mocks["trip_repo"].find_by_id.return_value = trip
    mocks["tp_repo"].find_by_id.return_value = tp
    mocks["tp_repo"].update_status.return_value = updated

    result = service.board_passanger(trip.id, tp.id, driver_id)

    assert result.status == "presente"
    mocks["tp_repo"].update_status.assert_called_once()
    call = mocks["tp_repo"].update_status.call_args
    assert call.args[0] == tp.id
    assert call.args[1] == "presente"


def test_board_passanger_rejects_if_already_absent() -> None:
    service, mocks = make_service()
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id=driver_id)
    trip = make_trip_mock(route_id=route.id, status="iniciada")
    trip.route = route
    tp = make_tp_mock(trip_id=trip.id, status="ausente")
    mocks["trip_repo"].find_by_id.return_value = trip
    mocks["tp_repo"].find_by_id.return_value = tp

    with pytest.raises(InvalidTripPassangerStatusError):
        service.board_passanger(trip.id, tp.id, driver_id)


def test_board_passanger_rejects_if_trip_not_in_progress() -> None:
    service, mocks = make_service()
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id=driver_id)
    trip = make_trip_mock(route_id=route.id, status="finalizada")
    trip.route = route
    mocks["trip_repo"].find_by_id.return_value = trip

    with pytest.raises(TripNotInProgressError):
        service.board_passanger(trip.id, uuid.uuid4(), driver_id)


def test_board_passanger_raises_when_tp_not_found() -> None:
    service, mocks = make_service()
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id=driver_id)
    trip = make_trip_mock(route_id=route.id, status="iniciada")
    trip.route = route
    mocks["trip_repo"].find_by_id.return_value = trip
    mocks["tp_repo"].find_by_id.return_value = None

    with pytest.raises(TripPassangerNotFoundError):
        service.board_passanger(trip.id, uuid.uuid4(), driver_id)


# ===========================================================================
# US09-TK10 — mark_passanger_absent
# ===========================================================================


def test_mark_absent_marks_status() -> None:
    service, mocks = make_service()
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id=driver_id)
    trip = make_trip_mock(route_id=route.id, status="iniciada")
    trip.route = route
    tp = make_tp_mock(trip_id=trip.id, status="pendente")
    updated = make_tp_mock(trip_id=trip.id, status="ausente")

    mocks["trip_repo"].find_by_id.return_value = trip
    mocks["tp_repo"].find_by_id.return_value = tp
    mocks["tp_repo"].update_status.return_value = updated

    result = service.mark_passanger_absent(trip.id, tp.id, driver_id)
    assert result.status == "ausente"


def test_mark_absent_rejects_if_already_presente() -> None:
    service, mocks = make_service()
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id=driver_id)
    trip = make_trip_mock(route_id=route.id, status="iniciada")
    trip.route = route
    tp = make_tp_mock(trip_id=trip.id, status="presente")
    mocks["trip_repo"].find_by_id.return_value = trip
    mocks["tp_repo"].find_by_id.return_value = tp

    with pytest.raises(InvalidTripPassangerStatusError):
        service.mark_passanger_absent(trip.id, tp.id, driver_id)


# ===========================================================================
# US09-TK11 — skip_stop
# ===========================================================================


def test_skip_stop_marks_passangers_of_stop_as_absent() -> None:
    service, mocks = make_service()
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id=driver_id)
    trip = make_trip_mock(route_id=route.id, status="iniciada")
    trip.route = route

    stop = Mock(spec=StopModel)
    stop.id = uuid.uuid4()
    stop.route_id = route.id
    stop.route_passanger_id = uuid.uuid4()

    tp = make_tp_mock(trip_id=trip.id, status="pendente")
    tp.route_passanger_id = stop.route_passanger_id

    mocks["trip_repo"].find_by_id.return_value = trip
    mocks["stop_repo"].find_by_id.return_value = stop
    mocks["tp_repo"].find_by_trip.return_value = [tp]
    mocks["tp_repo"].update_status.return_value = make_tp_mock(trip_id=trip.id, status="ausente")

    result = service.skip_stop(trip.id, stop.id, driver_id)
    assert len(result) == 1
    mocks["tp_repo"].update_status.assert_called_once()


def test_skip_stop_raises_when_stop_not_in_route() -> None:
    service, mocks = make_service()
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id=driver_id)
    trip = make_trip_mock(route_id=route.id, status="iniciada")
    trip.route = route

    stop = Mock(spec=StopModel)
    stop.id = uuid.uuid4()
    stop.route_id = uuid.uuid4()  # outra rota

    mocks["trip_repo"].find_by_id.return_value = trip
    mocks["stop_repo"].find_by_id.return_value = stop

    with pytest.raises(TripStopNotFoundError):
        service.skip_stop(trip.id, stop.id, driver_id)


def test_skip_stop_raises_when_trip_not_found() -> None:
    service, mocks = make_service()
    mocks["trip_repo"].find_by_id.return_value = None

    with pytest.raises(TripNotFoundError):
        service.skip_stop(uuid.uuid4(), uuid.uuid4(), uuid.uuid4())


def test_skip_stop_raises_when_wrong_owner() -> None:
    service, mocks = make_service()
    route = make_route_mock(driver_id=uuid.uuid4())
    trip = make_trip_mock(route_id=route.id, status="iniciada")
    trip.route = route
    mocks["trip_repo"].find_by_id.return_value = trip

    with pytest.raises(TripOwnershipError):
        service.skip_stop(trip.id, uuid.uuid4(), uuid.uuid4())


def test_skip_stop_raises_when_trip_not_in_progress() -> None:
    service, mocks = make_service()
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id=driver_id)
    trip = make_trip_mock(route_id=route.id, status="finalizada")
    trip.route = route
    mocks["trip_repo"].find_by_id.return_value = trip

    with pytest.raises(TripNotInProgressError):
        service.skip_stop(trip.id, uuid.uuid4(), driver_id)


def test_skip_stop_raises_when_stop_not_found() -> None:
    service, mocks = make_service()
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id=driver_id)
    trip = make_trip_mock(route_id=route.id, status="iniciada")
    trip.route = route
    mocks["trip_repo"].find_by_id.return_value = trip
    mocks["stop_repo"].find_by_id.return_value = None

    with pytest.raises(TripStopNotFoundError):
        service.skip_stop(trip.id, uuid.uuid4(), driver_id)


def test_skip_stop_returns_empty_when_no_pending_passangers() -> None:
    service, mocks = make_service()
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id=driver_id)
    trip = make_trip_mock(route_id=route.id, status="iniciada")
    trip.route = route

    stop = Mock(spec=StopModel)
    stop.id = uuid.uuid4()
    stop.route_id = route.id
    stop.route_passanger_id = uuid.uuid4()

    tp = make_tp_mock(trip_id=trip.id, status="ausente")
    tp.route_passanger_id = stop.route_passanger_id

    mocks["trip_repo"].find_by_id.return_value = trip
    mocks["stop_repo"].find_by_id.return_value = stop
    mocks["tp_repo"].find_by_trip.return_value = [tp]

    result = service.skip_stop(trip.id, stop.id, driver_id)

    assert result == []
    mocks["tp_repo"].update_status.assert_not_called()


def test_skip_stop_only_updates_pending_passangers() -> None:
    service, mocks = make_service()
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id=driver_id)
    trip = make_trip_mock(route_id=route.id, status="iniciada")
    trip.route = route

    stop = Mock(spec=StopModel)
    stop.id = uuid.uuid4()
    stop.route_id = route.id
    stop.route_passanger_id = uuid.uuid4()

    tp_pendente = make_tp_mock(trip_id=trip.id, status="pendente")
    tp_pendente.route_passanger_id = stop.route_passanger_id
    tp_presente = make_tp_mock(trip_id=trip.id, status="presente")
    tp_presente.route_passanger_id = stop.route_passanger_id

    mocks["trip_repo"].find_by_id.return_value = trip
    mocks["stop_repo"].find_by_id.return_value = stop
    mocks["tp_repo"].find_by_trip.return_value = [tp_pendente, tp_presente]
    mocks["tp_repo"].update_status.return_value = make_tp_mock(trip_id=trip.id, status="ausente")

    result = service.skip_stop(trip.id, stop.id, driver_id)

    assert len(result) == 1
    mocks["tp_repo"].update_status.assert_called_once_with(tp_pendente.id, "ausente")


# ===========================================================================
# US09-TK12 — alight_passanger
# ===========================================================================


def test_alight_passanger_sets_alighted_at() -> None:
    service, mocks = make_service()
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id=driver_id)
    trip = make_trip_mock(route_id=route.id, status="iniciada")
    trip.route = route
    tp = make_tp_mock(trip_id=trip.id, status="presente")
    tp.boarded_at = datetime.now(timezone.utc)
    updated = make_tp_mock(trip_id=trip.id, status="presente")
    updated.alighted_at = datetime.now(timezone.utc)

    mocks["trip_repo"].find_by_id.return_value = trip
    mocks["tp_repo"].find_by_id.return_value = tp
    mocks["tp_repo"].update_status.return_value = updated

    result = service.alight_passanger(trip.id, tp.id, driver_id)
    assert result.alighted_at is not None


def test_alight_passanger_rejects_if_not_presente() -> None:
    service, mocks = make_service()
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id=driver_id)
    trip = make_trip_mock(route_id=route.id, status="iniciada")
    trip.route = route
    tp = make_tp_mock(trip_id=trip.id, status="pendente")
    mocks["trip_repo"].find_by_id.return_value = trip
    mocks["tp_repo"].find_by_id.return_value = tp

    with pytest.raises(InvalidTripPassangerStatusError):
        service.alight_passanger(trip.id, tp.id, driver_id)


# ===========================================================================
# US09-TK13 — finish_trip
# ===========================================================================


def test_finish_trip_finalizes_and_alights_presents() -> None:
    service, mocks = make_service()
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id=driver_id, status="em_andamento")
    trip = make_trip_mock(route_id=route.id, status="iniciada")
    trip.route = route
    trip.trip_passangers = []
    finished = make_trip_mock(route_id=route.id, status="finalizada")
    finished.total_km = 12.5

    mocks["trip_repo"].find_by_id.return_value = trip
    mocks["tp_repo"].bulk_alight_presents.return_value = 2
    mocks["trip_repo"].update_status.return_value = finished

    result = service.finish_trip(trip.id, driver_id, FinishTripRequest(total_km=12.5))

    assert result.status == "finalizada"
    mocks["tp_repo"].bulk_alight_presents.assert_called_once()
    mocks["trip_repo"].update_status.assert_called_once()
    mocks["route_repo"].update.assert_called_once()
    assert mocks["route_repo"].update.call_args.args[1].get("status") == "ativa"
    mocks["notification"].notify_trip_finished.assert_called_once()


def test_finish_trip_raises_when_already_finished() -> None:
    service, mocks = make_service()
    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id=driver_id)
    trip = make_trip_mock(route_id=route.id, status="finalizada")
    trip.route = route
    mocks["trip_repo"].find_by_id.return_value = trip

    with pytest.raises(TripAlreadyFinishedError):
        service.finish_trip(trip.id, driver_id, FinishTripRequest())


def test_finish_trip_raises_when_wrong_owner() -> None:
    service, mocks = make_service()
    route = make_route_mock(driver_id=uuid.uuid4())
    trip = make_trip_mock(route_id=route.id, status="iniciada")
    trip.route = route
    mocks["trip_repo"].find_by_id.return_value = trip
    with pytest.raises(TripOwnershipError):
        service.finish_trip(trip.id, uuid.uuid4(), FinishTripRequest())


# ===========================================================================
# US11-TK01 — TripService.get_current_trip_for_passanger
# ===========================================================================


def test_get_current_trip_for_passanger_returns_response_when_trip_in_progress() -> None:
    """Passageiro com vínculo ativo e viagem em andamento recebe CurrentTripResponse
    com info do motorista e do veículo."""
    from src.domains.trips.dtos import CurrentTripResponse
    from src.domains.trips.errors import TripNotFoundError

    service, mocks = make_service()
    route = make_route_mock()
    route.driver = Mock(name="João Silva", photo_url="https://cdn.vango.app/u/joao.jpg")
    route.driver.name = "João Silva"
    route.driver.photo_url = "https://cdn.vango.app/u/joao.jpg"
    rp = make_rp_mock(route_id=route.id, status="accepted")
    trip = make_trip_mock(route_id=route.id, status="iniciada")
    trip.vehicle = Mock()
    trip.vehicle.plate = "ABC-1234"

    mocks["route_repo"].find_by_id.return_value = route
    mocks["rp_repo"].find_active_by_user_and_route.return_value = rp
    mocks["trip_repo"].find_in_progress_by_route.return_value = trip

    result = service.get_current_trip_for_passanger(route.id, rp.user_id)

    assert isinstance(result, CurrentTripResponse)
    assert result.trip_id == trip.id
    assert result.status == "iniciada"
    assert result.started_at == trip.started_at
    assert result.driver_name == "João Silva"
    assert result.driver_photo_url == "https://cdn.vango.app/u/joao.jpg"
    assert result.vehicle_plate == "ABC-1234"


def test_get_current_trip_for_passanger_handles_missing_photo_and_plate() -> None:
    """driver_photo_url e vehicle_plate viram None quando o motorista não tem foto
    e o veículo não tem placa."""
    from src.domains.trips.dtos import CurrentTripResponse

    service, mocks = make_service()
    route = make_route_mock()
    route.driver = Mock()
    route.driver.name = "Maria Souza"
    route.driver.photo_url = None
    rp = make_rp_mock(route_id=route.id, status="accepted")
    trip = make_trip_mock(route_id=route.id, status="iniciada")
    trip.vehicle = Mock()
    trip.vehicle.plate = None

    mocks["route_repo"].find_by_id.return_value = route
    mocks["rp_repo"].find_active_by_user_and_route.return_value = rp
    mocks["trip_repo"].find_in_progress_by_route.return_value = trip

    result = service.get_current_trip_for_passanger(route.id, rp.user_id)

    assert isinstance(result, CurrentTripResponse)
    assert result.driver_name == "Maria Souza"
    assert result.driver_photo_url is None
    assert result.vehicle_plate is None


def test_get_current_trip_for_passanger_returns_none_when_no_trip() -> None:
    """Retorna None quando não há viagem em andamento na rota."""
    service, mocks = make_service()
    route = make_route_mock()
    rp = make_rp_mock(route_id=route.id)

    mocks["route_repo"].find_by_id.return_value = route
    mocks["rp_repo"].find_active_by_user_and_route.return_value = rp
    mocks["trip_repo"].find_in_progress_by_route.return_value = None

    result = service.get_current_trip_for_passanger(route.id, rp.user_id)

    assert result is None


def test_get_current_trip_for_passanger_route_not_found_raises() -> None:
    """RouteNotFoundError quando a rota não existe."""
    from src.domains.routes.errors import RouteNotFoundError

    service, mocks = make_service()
    mocks["route_repo"].find_by_id.return_value = None

    with pytest.raises(RouteNotFoundError):
        service.get_current_trip_for_passanger(uuid.uuid4(), uuid.uuid4())


def test_get_current_trip_for_passanger_not_passanger_raises() -> None:
    """NotRoutePassangerError quando o usuário não tem vínculo ativo na rota."""
    from src.domains.route_passangers.errors import NotRoutePassangerError

    service, mocks = make_service()
    route = make_route_mock()
    mocks["route_repo"].find_by_id.return_value = route
    mocks["rp_repo"].find_active_by_user_and_route.return_value = None

    with pytest.raises(NotRoutePassangerError):
        service.get_current_trip_for_passanger(route.id, uuid.uuid4())


def test_get_current_trip_for_passanger_pending_membership_allowed() -> None:
    """Passageiro com status pending também pode consultar a viagem."""
    from src.domains.trips.dtos import CurrentTripResponse

    service, mocks = make_service()
    route = make_route_mock()
    rp = make_rp_mock(route_id=route.id, status="pending")
    trip = make_trip_mock(route_id=route.id)

    mocks["route_repo"].find_by_id.return_value = route
    mocks["rp_repo"].find_active_by_user_and_route.return_value = rp
    mocks["trip_repo"].find_in_progress_by_route.return_value = trip

    result = service.get_current_trip_for_passanger(route.id, rp.user_id)

    assert isinstance(result, CurrentTripResponse)


def test_get_current_trip_for_passanger_forwards_dependent_id() -> None:
    """dependent_id é repassado para find_active_by_user_and_route ao buscar guardian."""
    service, mocks = make_service()
    route = make_route_mock()
    rp = make_rp_mock(route_id=route.id)
    dep_id = uuid.uuid4()

    mocks["route_repo"].find_by_id.return_value = route
    mocks["rp_repo"].find_active_by_user_and_route.return_value = rp
    mocks["trip_repo"].find_in_progress_by_route.return_value = None

    service.get_current_trip_for_passanger(route.id, rp.user_id, dependent_id=dep_id)

    mocks["rp_repo"].find_active_by_user_and_route.assert_called_once_with(
        rp.user_id, dep_id, route.id
    )


# ===========================================================================
# US12-TK05 — wiring de notificações em board_passanger / mark_passanger_absent
# Arquivo: src/domains/trips/service.py
# ===========================================================================



def test_board_passanger_calls_notify_passanger_boarded():
    """board_passanger deve chamar notification_service.notify_passanger_boarded."""
    service, mocks = make_service()

    driver_id = uuid.uuid4()
    trip_id = uuid.uuid4()
    tp_id = uuid.uuid4()

    route = Mock(spec=__import__("src.domains.routes.entity", fromlist=["RouteModel"]).RouteModel)
    route.driver_id = driver_id

    trip = Mock(spec=TripModel)
    trip.id = trip_id
    trip.route = route
    trip.status = "iniciada"

    tp = Mock(spec=TripPassangerModel)
    tp.id = tp_id
    tp.trip_id = trip_id
    tp.status = "pendente"
    tp.route_passanger = Mock()
    tp.route_passanger.dependent_id = None
    tp.route_passanger.user = Mock(name="Alice", phone="51999990000")
    tp.route_passanger.pickup_address = Mock(label="Rua X")
    tp.boarded_at = None
    tp.alighted_at = None

    updated_tp = Mock(spec=TripPassangerModel)
    updated_tp.id = tp_id
    updated_tp.trip_id = trip_id
    updated_tp.status = "presente"
    updated_tp.boarded_at = datetime.now(timezone.utc)
    updated_tp.alighted_at = None
    updated_tp.route_passanger = tp.route_passanger
    updated_tp.route_passanger_id = uuid.uuid4()

    mocks["trip_repo"].find_by_id.return_value = trip
    mocks["tp_repo"].find_by_id.return_value = tp
    mocks["tp_repo"].update_status.return_value = updated_tp

    service.board_passanger(trip_id, tp_id, driver_id)

    mocks["notification"].notify_passanger_boarded.assert_called_once_with(updated_tp)



def test_mark_passanger_absent_calls_notify_passanger_absent():
    """mark_passanger_absent deve chamar notification_service.notify_passanger_absent."""
    service, mocks = make_service()

    driver_id = uuid.uuid4()
    trip_id = uuid.uuid4()
    tp_id = uuid.uuid4()

    route = Mock(spec=__import__("src.domains.routes.entity", fromlist=["RouteModel"]).RouteModel)
    route.driver_id = driver_id

    trip = Mock(spec=TripModel)
    trip.id = trip_id
    trip.route = route
    trip.status = "iniciada"

    tp = Mock(spec=TripPassangerModel)
    tp.id = tp_id
    tp.trip_id = trip_id
    tp.status = "pendente"
    tp.route_passanger = Mock()
    tp.route_passanger.dependent_id = None
    tp.route_passanger.user = Mock(name="Alice", phone="51999990000")
    tp.route_passanger.pickup_address = Mock(label="Rua X")
    tp.boarded_at = None
    tp.alighted_at = None

    updated_tp = Mock(spec=TripPassangerModel)
    updated_tp.id = tp_id
    updated_tp.trip_id = trip_id
    updated_tp.status = "ausente"
    updated_tp.boarded_at = None
    updated_tp.alighted_at = None
    updated_tp.route_passanger = tp.route_passanger
    updated_tp.route_passanger_id = uuid.uuid4()

    mocks["trip_repo"].find_by_id.return_value = trip
    mocks["tp_repo"].find_by_id.return_value = tp
    mocks["tp_repo"].update_status.return_value = updated_tp

    service.mark_passanger_absent(trip_id, tp_id, driver_id)

    mocks["notification"].notify_passanger_absent.assert_called_once_with(updated_tp)



def test_notification_service_interface_has_passanger_boarded():
    """INotificationService deve expor notify_passanger_boarded."""
    from src.domains.notifications.service import INotificationService

    assert hasattr(INotificationService, "notify_passanger_boarded")



def test_notification_service_interface_has_passanger_absent():
    """INotificationService deve expor notify_passanger_absent."""
    from src.domains.notifications.service import INotificationService

    assert hasattr(INotificationService, "notify_passanger_absent")


# ===========================================================================
# US11-TK05 — board_passanger chama emit_passenger_boarded
# ===========================================================================



def test_board_passanger_calls_emit_passenger_boarded() -> None:
    """board_passanger deve chamar emit_passenger_boarded após atualizar o status."""
    from unittest.mock import patch, AsyncMock

    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id=driver_id)
    route.status = "em_andamento"

    trip = Mock(spec=TripModel)
    trip.id = uuid.uuid4()
    trip.status = "iniciada"
    trip.route = route
    trip.route_id = route.id

    tp = Mock(spec=TripPassangerModel)
    tp.id = uuid.uuid4()
    tp.trip_id = trip.id
    tp.status = "pendente"
    tp.route_passanger_id = uuid.uuid4()

    updated_tp = Mock(spec=TripPassangerModel)
    updated_tp.id = tp.id
    updated_tp.trip_id = trip.id
    updated_tp.status = "presente"
    updated_tp.boarded_at = datetime.now(timezone.utc)
    updated_tp.route_passanger_id = tp.route_passanger_id

    service, mocks = make_service()
    mocks["trip_repo"].find_by_id.return_value = trip
    mocks["tp_repo"].find_by_id.return_value = tp
    mocks["tp_repo"].update_status.return_value = updated_tp

    with patch(
        "src.infrastructure.socketio.server.emit_passenger_boarded",
        new_callable=AsyncMock,
    ) as mock_emit:
        service.board_passanger(trip.id, tp.id, driver_id)
        mock_emit.assert_called_once()
        call_args = mock_emit.call_args[0]
        assert str(trip.id) in call_args



def test_board_passanger_emit_not_called_on_invalid_status() -> None:
    """board_passanger não deve chamar emit se o status do tp não for pendente."""
    from unittest.mock import patch, AsyncMock

    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id=driver_id)
    route.status = "em_andamento"

    trip = Mock(spec=TripModel)
    trip.id = uuid.uuid4()
    trip.status = "iniciada"
    trip.route = route
    trip.route_id = route.id

    tp = Mock(spec=TripPassangerModel)
    tp.id = uuid.uuid4()
    tp.trip_id = trip.id
    tp.status = "ausente"  # já processado

    service, mocks = make_service()
    mocks["trip_repo"].find_by_id.return_value = trip
    mocks["tp_repo"].find_by_id.return_value = tp

    with patch(
        "src.infrastructure.socketio.server.emit_passenger_boarded",
        new_callable=AsyncMock,
    ) as mock_emit:
        with pytest.raises(InvalidTripPassangerStatusError):
            service.board_passanger(trip.id, tp.id, driver_id)
        mock_emit.assert_not_called()


# ===========================================================================
# US11-TK06 — mark_passanger_absent e skip_stop chamam emit_passenger_absent
# ===========================================================================



def test_mark_passanger_absent_calls_emit_passenger_absent() -> None:
    """mark_passanger_absent deve chamar emit_passenger_absent após atualizar o status."""
    from unittest.mock import patch, AsyncMock

    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id=driver_id)
    route.status = "em_andamento"

    trip = Mock(spec=TripModel)
    trip.id = uuid.uuid4()
    trip.status = "iniciada"
    trip.route = route
    trip.route_id = route.id

    tp = Mock(spec=TripPassangerModel)
    tp.id = uuid.uuid4()
    tp.trip_id = trip.id
    tp.status = "pendente"
    tp.route_passanger_id = uuid.uuid4()

    updated_tp = Mock(spec=TripPassangerModel)
    updated_tp.id = tp.id
    updated_tp.trip_id = trip.id
    updated_tp.status = "ausente"
    updated_tp.boarded_at = None
    updated_tp.route_passanger_id = tp.route_passanger_id

    service, mocks = make_service()
    mocks["trip_repo"].find_by_id.return_value = trip
    mocks["tp_repo"].find_by_id.return_value = tp
    mocks["tp_repo"].update_status.return_value = updated_tp

    with patch(
        "src.infrastructure.socketio.server.emit_passenger_absent",
        new_callable=AsyncMock,
    ) as mock_emit:
        service.mark_passanger_absent(trip.id, tp.id, driver_id)
        mock_emit.assert_called_once()
        call_args = mock_emit.call_args[0]
        assert str(trip.id) in call_args



def test_skip_stop_calls_emit_passenger_absent_for_each_pending_tp() -> None:
    """skip_stop deve chamar emit_passenger_absent para cada passageiro pendente na parada."""
    from unittest.mock import patch, AsyncMock

    driver_id = uuid.uuid4()
    route = make_route_mock(driver_id=driver_id)
    route.status = "em_andamento"

    trip = Mock(spec=TripModel)
    trip.id = uuid.uuid4()
    trip.status = "iniciada"
    trip.route = route
    trip.route_id = route.id

    rp_id = uuid.uuid4()
    stop = Mock(spec=StopModel)
    stop.id = uuid.uuid4()
    stop.route_id = route.id
    stop.route_passanger_id = rp_id

    tp1 = Mock(spec=TripPassangerModel)
    tp1.id = uuid.uuid4()
    tp1.trip_id = trip.id
    tp1.status = "pendente"
    tp1.route_passanger_id = rp_id

    tp2 = Mock(spec=TripPassangerModel)
    tp2.id = uuid.uuid4()
    tp2.trip_id = trip.id
    tp2.status = "pendente"
    tp2.route_passanger_id = rp_id

    updated_tp = Mock(spec=TripPassangerModel)
    updated_tp.id = uuid.uuid4()
    updated_tp.trip_id = trip.id
    updated_tp.status = "ausente"
    updated_tp.boarded_at = None
    updated_tp.route_passanger_id = rp_id

    service, mocks = make_service()
    mocks["trip_repo"].find_by_id.return_value = trip
    mocks["stop_repo"].find_by_id.return_value = stop
    mocks["tp_repo"].find_by_trip.return_value = [tp1, tp2]
    mocks["tp_repo"].update_status.return_value = updated_tp

    with patch(
        "src.infrastructure.socketio.server.emit_passenger_absent",
        new_callable=AsyncMock,
    ) as mock_emit:
        service.skip_stop(trip.id, stop.id, driver_id)
        assert mock_emit.call_count == 2
