"""US06-TK19 — AbsenceService.

Cobre a criação de Absence pelo passageiro/guardian a partir da tela 2.3
("Avisar ausência?").

Regras gerais:
- Requer vínculo ATIVO (pending/accepted) do user (ou guardian do dependente)
  com a rota; caso contrário, 403.
- Bloqueia criação duplicada (mesmo RP + mesma data) com 409.
- Bloqueia data inválida (no passado / fora da recorrência da rota) com 409.
- Não bloqueia quando a rota está em_andamento — o passageiro ainda pode avisar
  ausência futura.
- Notifica o motorista via INotificationService.
"""

from datetime import UTC, date, datetime
from uuid import UUID

from src.domains.absences.dtos import AbsenceResponse, CreateAbsenceRequest
from src.domains.absences.errors import AbsenceAlreadyReportedError, AbsenceDateNotAllowedError
from src.domains.notifications.service import INotificationService
from src.domains.route_passangers.errors import NotRoutePassangerError
from src.domains.route_passangers.repository import IRoutePassangerRepository
from src.domains.routes.errors import RouteNotFoundError
from src.domains.routes.repository import IRouteRepository
from src.domains.trips.entity import AbsenceModel
from src.domains.trips.repository import IAbsenceRepository

_RECURRENCE_MAP = {
    "seg": 0,
    "ter": 1,
    "qua": 2,
    "qui": 3,
    "sex": 4,
    "sab": 5,
    "dom": 6,
}


class AbsenceService:
    def __init__(
        self,
        absence_repository: IAbsenceRepository,
        route_repository: IRouteRepository,
        route_passanger_repository: IRoutePassangerRepository,
        notification_service: INotificationService,
    ):
        self.absence_repository = absence_repository
        self.route_repository = route_repository
        self.route_passanger_repository = route_passanger_repository
        self.notification_service = notification_service

    # US06-TK19
    def create_absence(
        self,
        user_id: UUID,
        data: CreateAbsenceRequest,
    ) -> AbsenceResponse:
        """Registra o aviso de ausência do passageiro/guardian.

        - 404 RouteNotFoundError se rota não existir
        - 403 NotRoutePassangerError se o user (ou guardian do dependente) não
          tiver vínculo ativo com a rota
        - 409 AbsenceDateNotAllowedError se a data for no passado ou fora da
          recorrência da rota
        - 409 AbsenceAlreadyReportedError se já existir ausência para o mesmo
          RP naquela data
        - Persiste AbsenceModel(route_passanger_id, absence_date, reason)
        - Notifica o motorista via notify_driver_passanger_absence_reported
        """
        route = self.route_repository.find_by_id(data.route_id)
        if route is None:
            raise RouteNotFoundError()

        rp = self.route_passanger_repository.find_active_by_user_and_route(user_id, data.dependent_id, data.route_id)
        if rp is None:
            raise NotRoutePassangerError()

        # Bloqueia datas anteriores ao mês corrente
        current_month_start = date.today().replace(day=1)
        if data.absence_date < current_month_start:
            raise AbsenceDateNotAllowedError()

        # Bloqueia datas fora da recorrência da rota
        allowed_weekdays = {_RECURRENCE_MAP[day.strip()] for day in route.recurrence.split(",") if day.strip() in _RECURRENCE_MAP}
        if data.absence_date.weekday() not in allowed_weekdays:
            raise AbsenceDateNotAllowedError()

        absence_datetime = datetime.combine(data.absence_date, datetime.min.time(), UTC)
        existing = self.absence_repository.find_for_route_passanger_on_date(rp.id, absence_datetime)
        if existing is not None:
            raise AbsenceAlreadyReportedError()

        absence = AbsenceModel(
            route_passanger_id=rp.id,
            absence_date=absence_datetime,
            reason=data.reason,
        )
        saved = self.absence_repository.save(absence)
        self.notification_service.notify_driver_passanger_absence_reported(rp)

        return AbsenceResponse.model_construct(
            id=saved.id,
            trip_id=saved.trip_id,
            route_passanger_id=saved.route_passanger_id,
            absence_date=saved.absence_date,
            reason=saved.reason,
            created_at=saved.created_at,
        )
