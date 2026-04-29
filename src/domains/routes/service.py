import random
import string
from uuid import UUID

from src.domains.addresses.entity import AddressModel
from src.domains.notifications.service import INotificationService
from src.domains.route_passangers.repository import IRoutePassangerRepository
from src.domains.routes.dtos import (
    RouteCreate,
    RouteInviteSummaryResponse,
    RouteUpdate,
)
from src.domains.routes.entity import RouteModel
from src.domains.routes.errors import (
    NoVehicleError,
    RouteInProgressError,
    RouteNotFoundError,
    RouteOwnershipError,
)
from src.domains.routes.repository import IAddressRepository, IRouteRepository
from src.domains.vehicles.repository import IVehicleRepository


class RouteService:
    def __init__(
        self,
        route_repository: IRouteRepository,
        address_repository: IAddressRepository,
        vehicle_repository: IVehicleRepository,
        route_passanger_repository: IRoutePassangerRepository | None = None,
        notification_service: INotificationService | None = None,
    ):
        self.route_repository = route_repository
        self.address_repository = address_repository
        self.vehicle_repository = vehicle_repository
        # Usado pela US08-TK05 (get_invite_summary). Opcional para não
        # quebrar testes/instanciações pré-US08 que não dependem dele.
        self.route_passanger_repository = route_passanger_repository
        # Usado pela US06-TK18 (delete_route). Opcional pelo mesmo motivo.
        self.notification_service = notification_service

    # US05 - TK03
    def create_route(self, driver_id: UUID, data: RouteCreate) -> RouteModel:
        vehicles = self.vehicle_repository.get_by_driver_id(driver_id)
        if not vehicles:
            raise NoVehicleError()

        vehicle = vehicles[0]

        origin = AddressModel(
            user_id=driver_id,
            label=data.origin.label,
            street=data.origin.street,
            number=data.origin.number,
            neighborhood=data.origin.neighborhood,
            zip=data.origin.zip,
            city=data.origin.city,
            state=data.origin.state,
        )
        destination = AddressModel(
            user_id=driver_id,
            label=data.destination.label,
            street=data.destination.street,
            number=data.destination.number,
            neighborhood=data.destination.neighborhood,
            zip=data.destination.zip,
            city=data.destination.city,
            state=data.destination.state,
        )

        saved_origin = self.address_repository.save(origin)
        saved_destination = self.address_repository.save(destination)

        route = RouteModel(
            driver_id=driver_id,
            origin_address_id=saved_origin.id,
            destination_address_id=saved_destination.id,
            name=data.name,
            route_type=data.route_type,
            recurrence=data.recurrence,
            expected_time=data.expected_time,
            status="inativa",
            invite_code=self._generate_invite_code(),
            max_passengers=vehicle.capacity,
        )

        return self.route_repository.save(route)

    def regenerate_invite_code(self, route_id: UUID, driver_id: UUID) -> RouteModel:
        route = self.route_repository.find_by_id(route_id)
        if route is None:
            raise RouteNotFoundError()
        if route.driver_id != driver_id:
            raise RouteOwnershipError()
        new_code = self._generate_invite_code()
        return self.route_repository.update_invite_code(route_id, new_code)

    def _generate_invite_code(self) -> str:
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=5))

    # US07 - TK03

    def get_routes(self, driver_id: UUID) -> list[RouteModel]:
        """Retorna todas as rotas do motorista independente de status."""
        return self.route_repository.find_all_by_driver_id(driver_id)

    # US06-TK03
    def update_route(self, route_id: UUID, driver_id: UUID, data: RouteUpdate) -> RouteModel:
        route = self.route_repository.find_by_id(route_id)
        if route is None:
            raise RouteNotFoundError()

        if route.driver_id != driver_id:
            raise RouteOwnershipError()

        if route.status == "em_andamento":
            raise RouteInProgressError()

        update_data = data.model_dump(exclude_none=True)

        if not update_data:
            return route

        if "origin" in update_data:
            _origin_data = update_data.pop("origin")
            origin = AddressModel(
                user_id=driver_id,
                label=_origin_data["label"],
                street=_origin_data["street"],
                number=_origin_data["number"],
                neighborhood=_origin_data["neighborhood"],
                zip=_origin_data["zip"],
                city=_origin_data["city"],
                state=_origin_data["state"],
            )
            saved_origin = self.address_repository.save(origin)
            update_data["origin_address_id"] = saved_origin.id

        if "destination" in update_data:
            _destination_data = update_data.pop("destination")
            destination = AddressModel(
                user_id=driver_id,
                label=_destination_data["label"],
                street=_destination_data["street"],
                number=_destination_data["number"],
                neighborhood=_destination_data["neighborhood"],
                zip=_destination_data["zip"],
                city=_destination_data["city"],
                state=_destination_data["state"],
            )
            saved_destination = self.address_repository.save(destination)
            update_data["destination_address_id"] = saved_destination.id

        updated_route = self.route_repository.update(route_id, update_data)
        if updated_route is None:
            raise RouteNotFoundError()

        return updated_route

    # US08-TK05
    def get_by_invite_code(self, invite_code: str) -> RouteModel:
        """Retorna a rota por invite_code.

        - 404 RouteNotFoundError se não existir rota com esse invite_code.
        """
        route = self.route_repository.find_by_invite_code(invite_code)
        if route is None:
            raise RouteNotFoundError()
        return route

    # US08-TK05
    def get_invite_summary(self, invite_code: str) -> RouteInviteSummaryResponse:
        """Retorna o resumo público da rota identificada pelo invite_code,
        já com accepted_count computado.

        - 404 RouteNotFoundError se não existir.
        - accepted_count vem de route_passanger_repository.count_accepted_by_route.
        """
        route = self.get_by_invite_code(invite_code)
        accepted_count = self.route_passanger_repository.count_accepted_by_route(route.id)
        return RouteInviteSummaryResponse.model_construct(
            id=route.id,
            name=route.name,
            route_type=route.route_type,
            recurrence=route.recurrence,
            expected_time=route.expected_time,
            max_passengers=route.max_passengers,
            accepted_count=accepted_count,
            origin_address=route.origin_address,
            destination_address=route.destination_address,
        )

    def get_route(self, route_id: UUID, driver_id: UUID) -> RouteModel:
        """
        Retorna a rota pelo ID.
        Verifica ownership: 404 se não existir, 403 se não for o dono.
        """
        from src.domains.routes.errors import RouteNotFoundError, RouteOwnershipError

        route = self.route_repository.find_by_id(route_id)
        if route is None:
            raise RouteNotFoundError()
        if route.driver_id != driver_id:
            raise RouteOwnershipError()
        return route

    # US06-TK18
    def delete_route(self, route_id: UUID, driver_id: UUID) -> None:
        """
        Exclui permanentemente uma rota do motorista.

        Regras:
        - 404 RouteNotFoundError se não existir
        - 403 RouteOwnershipError se driver não for dono
        - 409 RouteInProgressError se status == 'em_andamento'
        - Notifica todos os passageiros ativos (pending + accepted) via
          notification_service.notify_passanger_route_cancelled(rp) ANTES
          do delete — rejected ficam de fora.
        - Chama route_repository.delete(route_id). A cascade do ORM
          (cascade="all, delete-orphan") remove route_passangers,
          schedules e stops associadas.
        - Retorna None.
        """
        route = self.route_repository.find_by_id(route_id)
        if route is None:
            raise RouteNotFoundError()
        if route.driver_id != driver_id:
            raise RouteOwnershipError()
        if route.status == "em_andamento":
            raise RouteInProgressError()

        active_passengers: dict = {}
        for status in ("pending", "accepted"):
            for rp in self.route_passanger_repository.find_by_route_and_status(route_id, status):
                active_passengers[rp.id] = rp

        for rp in active_passengers.values():
            self.notification_service.notify_passanger_route_cancelled(rp)

        self.route_repository.delete(route_id)
