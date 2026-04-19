"""
US06 — RoutePassangerService.

Cobre TK08 (accept_request), TK10 (reject_request), TK12 (remove_passanger)
e TK14 (list_by_status).

Regras gerais:
- Todas as operações exigem que o driver seja o dono da rota (403 caso contrário).
- Accept, reject e remove bloqueiam se a rota estiver com status='em_andamento' (409).
- Accept valida capacidade máxima do veículo (409 se excedida).
- Accept e reject só operam em solicitações com status='pending' (409 se já processada).
- Sempre que uma operação altera o vínculo, notifica via INotificationService.
- Response resolve nomes de user, dependent e guardian.
"""

from uuid import UUID

from src.domains.dependents.repository import IDependentRepository
from src.domains.notifications.service import INotificationService
from src.domains.route_passangers.dtos import RoutePassangerResponse
from src.domains.route_passangers.entity import RoutePassangerModel
from src.domains.route_passangers.repository import IRoutePassangerRepository
from src.domains.routes.repository import IRouteRepository
from src.domains.users.repository import IUserRepository


class RoutePassangerService:
    def __init__(
        self,
        route_passanger_repository: IRoutePassangerRepository,
        route_repository: IRouteRepository,
        user_repository: IUserRepository,
        dependent_repository: IDependentRepository,
        notification_service: INotificationService,
    ):
        self.route_passanger_repository = route_passanger_repository
        self.route_repository = route_repository
        self.user_repository = user_repository
        self.dependent_repository = dependent_repository
        self.notification_service = notification_service

    # US06-TK08
    def accept_request(self, route_id: UUID, rp_id: UUID, driver_id: UUID) -> RoutePassangerResponse:
        """
        Aceita uma solicitação pending.

        - 404 se rota ou rp não existirem
        - 403 se driver não for dono
        - 409 RouteInProgressError se status='em_andamento'
        - 409 RoutePassangerAlreadyProcessedError se rp.status != 'pending'
        - 409 RouteCapacityExceededError se count_accepted >= max_passengers
        - Atualiza status para 'accepted' e joined_at=now
        - Chama notification_service.notify_passanger_accepted(rp)
        """
        pass

    # US06-TK10
    def reject_request(self, route_id: UUID, rp_id: UUID, driver_id: UUID) -> RoutePassangerResponse:
        """
        Recusa uma solicitação pending.

        - 404 se rota ou rp não existirem
        - 403 se driver não for dono
        - 409 RouteInProgressError se status='em_andamento'
        - 409 RoutePassangerAlreadyProcessedError se rp.status != 'pending'
        - NÃO valida capacidade
        - Atualiza status para 'rejected' (joined_at permanece None)
        - Chama notification_service.notify_passanger_rejected(rp)
        """
        pass

    # US06-TK12
    def remove_passanger(self, route_id: UUID, rp_id: UUID, driver_id: UUID) -> None:
        """
        Remove um passageiro da rota.

        - 404 se rota ou rp não existirem
        - 403 se driver não for dono
        - 409 RouteInProgressError se status='em_andamento'
        - Chama notification_service.notify_passanger_removed(rp) ANTES do delete
        - Chama repository.delete(rp_id)
        - Retorna None
        """
        pass

    # US06-TK14
    def list_by_status(self, route_id: UUID, driver_id: UUID, status: str | None = None) -> list[RoutePassangerResponse]:
        """
        Lista vínculos de passageiros de uma rota, opcionalmente filtrados por status.

        - 404 se rota não existir
        - 403 se driver não for dono
        - ValueError se status não for um dos valores válidos (pending/accepted/rejected/None)
        - Resolve nomes (user_name, dependent_name, guardian_name) em cada response
        """
        pass

    # Helper interno (sem @abstractmethod — não está na interface)
    def _to_response(self, rp: RoutePassangerModel) -> RoutePassangerResponse:
        """Constrói RoutePassangerResponse resolvendo nomes de user/dependent/guardian."""
        pass
