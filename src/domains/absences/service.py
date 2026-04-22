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

from uuid import UUID

from src.domains.absences.dtos import AbsenceResponse, CreateAbsenceRequest
from src.domains.notifications.service import INotificationService
from src.domains.route_passangers.repository import IRoutePassangerRepository
from src.domains.routes.repository import IRouteRepository
from src.domains.trips.repository import IAbsenceRepository


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
        pass
