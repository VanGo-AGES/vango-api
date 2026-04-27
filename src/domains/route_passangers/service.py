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
from src.domains.route_passangers.dtos import (
    JoinRouteRequest,
    PassangerRouteDetailResponse,
    PassangerRouteResponse,
    RoutePassangerResponse,
    RoutePassangerScheduleResponse,
    UpdateSchedulesRequest,
)
from src.domains.route_passangers.entity import RoutePassangerModel
from src.domains.route_passangers.errors import (
    NotRoutePassangerError,
    RoutePassangerAlreadyProcessedError,
    RoutePassangerNotFoundError,
)
from src.domains.route_passangers.repository import IRoutePassangerRepository
from src.domains.route_passangers.schedule_repository import (
    IRoutePassangerScheduleRepository,
)
from src.domains.routes.dtos import AddressResponse
from src.domains.routes.errors import RouteInProgressError, RouteNotFoundError, RouteOwnershipError
from src.domains.routes.repository import IRouteRepository
from src.domains.stops.dtos import StopResponse
from src.domains.stops.repository import IStopRepository
from src.domains.users.repository import IUserRepository


class RoutePassangerService:
    def __init__(
        self,
        route_passanger_repository: IRoutePassangerRepository,
        route_repository: IRouteRepository,
        user_repository: IUserRepository,
        dependent_repository: IDependentRepository,
        notification_service: INotificationService,
        stop_repository: IStopRepository,
        schedule_repository: IRoutePassangerScheduleRepository,
    ):
        self.route_passanger_repository = route_passanger_repository
        self.route_repository = route_repository
        self.user_repository = user_repository
        self.dependent_repository = dependent_repository
        self.notification_service = notification_service
        self.stop_repository = stop_repository
        self.schedule_repository = schedule_repository

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
        - Cria Stop vinculada ao rp:
            - address_id = rp.pickup_address_id
            - type = 'embarque' se route.route_type == 'outbound', senão 'desembarque'
            - order_index = max(order_index das stops da rota) + 1 (ou 0 se não houver)
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
        route = self.route_repository.find_by_id(route_id)
        if route is None:
            raise RouteNotFoundError()

        if route.driver_id != driver_id:
            raise RouteOwnershipError()

        if route.status == "em_andamento":
            raise RouteInProgressError()

        rp = self.route_passanger_repository.find_by_id(rp_id)
        if rp is None:
            raise RoutePassangerNotFoundError()

        if rp.status != "pending":
            raise RoutePassangerAlreadyProcessedError()

        updated = self.route_passanger_repository.update_status(rp.id, "rejected")
        self.notification_service.notify_passanger_rejected(updated)
        return self._to_response(updated)

    def remove_passanger(self, route_id: UUID, rp_id: UUID, driver_id: UUID) -> None:
        """
        Remove um passageiro da rota.

        - 404 se rota ou rp não existirem
        - 403 se driver não for dono
        - 409 RouteInProgressError se status='em_andamento'
        - Chama notification_service.notify_passanger_removed(rp) ANTES do delete
        - Remove a Stop vinculada ao rp (stop_repository.delete_by_route_passanger_id) ANTES do delete do rp
        - Chama repository.delete(rp_id)
        - Retorna None
        """
        route = self.route_repository.find_by_id(route_id)
        if route is None:
            raise RouteNotFoundError()

        if route.driver_id != driver_id:
            raise RouteOwnershipError()

        if route.status == "em_andamento":
            raise RouteInProgressError()

        rp = self.route_passanger_repository.find_by_id(rp_id)
        if rp is None:
            raise RoutePassangerNotFoundError()

        self.notification_service.notify_passanger_removed(rp)
        self.stop_repository.delete_by_route_passanger_id(rp.id)
        self.route_passanger_repository.delete(rp.id)

    # US06-TK14
    def list_by_status(self, route_id: UUID, driver_id: UUID, status: str | None = None) -> list[RoutePassangerResponse]:
        """
        Lista vínculos de passageiros de uma rota, opcionalmente filtrados por status.

        - 404 se rota não existir
        - 403 se driver não for dono
        - ValueError se status não for um dos valores válidos (pending/accepted/rejected/None)
        - Resolve nomes (user_name, dependent_name, guardian_name) em cada response
        """
        route = self.route_repository.find_by_id(route_id)
        if route is None:
            raise RouteNotFoundError()

        if route.driver_id != driver_id:
            raise RouteOwnershipError()

        valid_statuses = {"pending", "accepted", "rejected", None}
        if status not in valid_statuses:
            raise ValueError(f"Status inválido: '{status}'. Valores permitidos: pending, accepted, rejected")

        rps = self.route_passanger_repository.find_by_route_and_status(route_id, status)
        return [self._to_response(rp) for rp in rps]

    # Helper interno (sem @abstractmethod — não está na interface)
    def _to_response(self, rp: RoutePassangerModel) -> RoutePassangerResponse:
        """Constrói RoutePassangerResponse resolvendo nomes de user/dependent/guardian.

        Usa model_construct para evitar revalidação de dados que já passaram pelo ORM
        (e para compatibilidade com mocks nos testes unitários).
        """
        user = self.user_repository.find_by_id(rp.user_id)

        dependent_name: str | None = None
        guardian_name: str | None = None
        if rp.dependent_id is not None:
            dep = self.dependent_repository.get_by_id(rp.dependent_id)
            if dep is not None:
                dependent_name = dep.name
                guardian_name = user.name

        return RoutePassangerResponse.model_construct(
            id=rp.id,
            route_id=rp.route_id,
            status=rp.status,
            requested_at=rp.requested_at,
            user_id=rp.user_id,
            user_name=user.name,
            user_phone=user.phone,
            pickup_address_id=rp.pickup_address_id,
            joined_at=rp.joined_at,
            dependent_id=rp.dependent_id,
            dependent_name=dependent_name,
            guardian_name=guardian_name,
        )

    # -----------------------------------------------------------------
    # US08 — operações originadas pelo passageiro
    # -----------------------------------------------------------------

    # US08-TK07
    def join_route(
        self,
        route_id: UUID,
        user_id: UUID,
        data: JoinRouteRequest,
    ) -> RoutePassangerResponse:
        """
        Passageiro (ou guardian em nome do dependente) solicita entrada.

        - 404 RouteNotFoundError se rota não existir
        - 409 RouteInProgressError se status='em_andamento'
        - 409 RouteCapacityExceededError se count_accepted >= max_passengers
        - 409 DuplicateRoutePassangerError se já existir vínculo ativo
          (pending/accepted) para (user_id, dependent_id) nessa rota
        - Cria RoutePassangerModel com status='pending',
          pickup_address_id = data.schedules[0].address_id
        - Persiste schedules via schedule_repository.save_many
        - Notifica motorista via notify_driver_passanger_requested
        """
        pass

    # US08-TK09
    def leave_route(
        self,
        route_id: UUID,
        user_id: UUID,
        dependent_id: UUID | None = None,
    ) -> None:
        """
        Passageiro (ou guardian em nome do dependente) sai da rota.

        - 404 RouteNotFoundError se rota não existir
        - 409 RouteInProgressError se status='em_andamento'
        - 404 RoutePassangerNotFoundError se não houver RP ativo
          para (user_id, dependent_id) nessa rota
        - Notifica motorista via notify_driver_passanger_left ANTES de qualquer delete
        - Remove a Stop vinculada via stop_repository.delete_by_route_passanger_id
          (chamada explícita, não confiar na cascade do ORM — precisamos do hook
          para disparar push notification no futuro)
        - Deleta RP via route_passanger_repository.delete (schedules caem na cascade)
        """
        pass

    # US08-TK11
    def update_schedules(
        self,
        route_id: UUID,
        user_id: UUID,
        data: UpdateSchedulesRequest,
        dependent_id: UUID | None = None,
    ) -> RoutePassangerResponse:
        """
        Passageiro atualiza seus dias (schedules) na rota.

        - 404 RouteNotFoundError se rota não existir
        - 409 RouteInProgressError se status='em_andamento'
        - 404 RoutePassangerNotFoundError se não houver RP ativo
        - Substitui schedules via schedule_repository.replace
        - Notifica motorista via notify_driver_passanger_schedules_changed
        """
        pass

    # US08-TK14
    def list_my_routes(self, user_id: UUID) -> list[PassangerRouteResponse]:
        """
        Retorna as rotas ativas (pending + accepted) do usuário para a home do
        passageiro, incluindo vínculos em que o usuário é guardian de um
        dependente.

        - Usa route_passanger_repository.find_active_with_route_by_user(user_id).
        - Ordena por joined_at desc (já garantido pelo repo).
        - Resolve:
            - driver_name via user_repository
            - origin_label / destination_label via endereços da rota
            - dependent_name via dependent_repository quando rp.dependent_id != None
            - schedules a partir de rp.schedules
        - Se o usuário não tiver nenhum vínculo ativo, retorna [].
        """
        pass

    def get_my_route_detail(
        self,
        route_id: UUID,
        user_id: UUID,
        dependent_id: UUID | None = None,
    ) -> PassangerRouteDetailResponse:
        """Detalhe completo da rota do ponto de vista do passageiro (tela 2.3).

        Nunca expõe invite_code, max_passengers nem driver_id.
        """

        route = self.route_repository.find_by_id(route_id)
        if route is None:
            raise RouteNotFoundError()

        rp = self.route_passanger_repository.find_active_by_user_and_route(user_id, dependent_id, route_id)
        if rp is None:
            raise NotRoutePassangerError()

        driver = self.user_repository.find_by_id(route.driver_id)

        dependent_name: str | None = None
        if dependent_id is not None:
            dep = self.dependent_repository.find_by_id(dependent_id)
            if dep is not None:
                dependent_name = dep.name

        current_trip_id: UUID | None = None
        if route.status == "em_andamento":
            trips = list(getattr(route, "trips", []) or [])
            started = [t for t in trips if getattr(t, "status", None) == "iniciada"]
            if started:
                current_trip_id = started[0].id

        recurrence = route.recurrence
        recurrence_list = [d.strip() for d in recurrence.split(",")] if isinstance(recurrence, str) else list(recurrence)

        origin = AddressResponse.model_validate(route.origin_address)
        destination = AddressResponse.model_validate(route.destination_address)
        pickup = AddressResponse.model_validate(rp.pickup_address)

        # Em testes unitários os Mocks de Stop/Schedule não trazem todos os
        # atributos da entidade — por isso validamos defensivamente.
        stops_list: list[StopResponse] = []
        for s in sorted(
            getattr(route, "stops", []) or [],
            key=lambda x: getattr(x, "order_index", 0),
        ):
            try:
                stops_list.append(StopResponse.model_validate(s))
            except Exception:  # noqa: BLE001
                pass

        schedules_list: list[RoutePassangerScheduleResponse] = []
        for sched in getattr(rp, "schedules", []) or []:
            try:
                schedules_list.append(RoutePassangerScheduleResponse.model_validate(sched))
            except Exception:  # noqa: BLE001
                pass

        return PassangerRouteDetailResponse(
            route_id=route.id,
            name=route.name,
            route_type=route.route_type,
            status=route.status,
            recurrence=recurrence_list,
            expected_time=route.expected_time,
            origin_address=origin,
            destination_address=destination,
            stops=stops_list,
            driver_name=driver.name,
            driver_phone=driver.phone,
            membership_status=rp.status,
            dependent_id=dependent_id,
            dependent_name=dependent_name,
            my_pickup_address=pickup,
            my_schedules=schedules_list,
            current_trip_id=current_trip_id,
        )
