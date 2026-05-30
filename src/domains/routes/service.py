import secrets
import string
from datetime import datetime
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
from src.domains.routing.route_totals import compute_route_totals
from src.domains.routing.service import IGeocodingService, IRoutingService
from src.domains.trips.repository import IAbsenceRepository, ITripRepository
from src.domains.vehicles.repository import IVehicleRepository


class RouteService:
    def __init__(
        self,
        route_repository: IRouteRepository,
        address_repository: IAddressRepository,
        vehicle_repository: IVehicleRepository,
        route_passanger_repository: IRoutePassangerRepository | None = None,
        notification_service: INotificationService | None = None,
        absence_repository: IAbsenceRepository | None = None,
        geocoding_service: IGeocodingService | None = None,
        routing_service: IRoutingService | None = None,
        trip_repository: ITripRepository | None = None,
    ):
        self.route_repository = route_repository
        self.address_repository = address_repository
        self.vehicle_repository = vehicle_repository
        # Usado pela US08-TK05 (get_invite_summary). Opcional para não
        # quebrar testes/instanciações pré-US08 que não dependem dele.
        self.route_passanger_repository = route_passanger_repository
        # Usado pela US06-TK18 (delete_route). Opcional pelo mesmo motivo.
        self.notification_service = notification_service
        # US10-TK19: usado pra calcular total_distance_km e
        # estimated_duration_min dos RouteResponse devolvidos por get_route
        # e get_routes. Opcional pra não quebrar testes existentes.
        self.routing_service = routing_service
        # Usado pelo GET /routes/{route_id}/absences (view do motorista).
        self.absence_repository = absence_repository
        # US10-TK18: usado para preencher lat/lng dos AddressModel criados
        # em create_route (origin e destination). Opcional para não quebrar
        # testes/instanciações que não dependem de geocoding.
        self.geocoding_service = geocoding_service
        # US09 — usado para popular active_trip_id em RouteResponse.
        self.trip_repository = trip_repository

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
        self._geocode_address(origin)
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
        self._geocode_address(destination)

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
        alphabet = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(5))

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
            self._geocode_address(origin)
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
            self._geocode_address(destination)
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

    def get_accepted_count(self, route_id: UUID) -> int:
        """Retorna a quantidade de passageiros com status='accepted' na rota."""
        if self.route_passanger_repository is None:
            return 0
        return self.route_passanger_repository.count_accepted_by_route(route_id)

    def get_active_trip_id(self, route_id: UUID) -> UUID | None:
        """Retorna o id da trip com status='iniciada' da rota, ou None se não houver.

        Usado pelo controller para popular active_trip_id em RouteResponse.
        Silenciosamente retorna None se trip_repository não foi injetado.
        """
        if self.trip_repository is None:
            return None
        trip = self.trip_repository.find_in_progress_by_route(route_id)
        return trip.id if trip is not None else None

    # US10-TK19
    def get_route_totals(self, route: RouteModel) -> tuple[float | None, int | None]:
        """Devolve (total_distance_km, estimated_duration_min) da rota planejada.

        Usado pelos endpoints GET /routes e GET /routes/{id} no controller
        (via model_copy(update={...}), mesmo padrão de get_accepted_count) pra
        popular RouteResponse.total_distance_km e RouteResponse.estimated_duration_min.

        Retorna (None, None) se self.routing_service for None ou se o
        compute_route_totals do helper compartilhado retornar (None, None).
        Nunca propaga exceção — totais são best-effort.
        """
        return compute_route_totals(route, self.routing_service)

    def get_route_absences(self, route_id: UUID, caller_id: UUID, absence_date: datetime) -> list:
        """Retorna ausências avisadas para a rota numa data específica.

        - 404 RouteNotFoundError se rota não existir
        - 403 RouteOwnershipError se o caller não for dono nem passageiro ativo
        Acessível tanto pelo motorista quanto por passageiros (pending/accepted).
        Cada item inclui user_name e dependent_name para exibição direta pelo frontend.
        """
        from src.domains.absences.dtos import RouteAbsenceResponse

        route = self.route_repository.find_by_id(route_id)
        if route is None:
            raise RouteNotFoundError()

        is_driver = route.driver_id == caller_id
        is_passanger = False
        if not is_driver and self.route_passanger_repository is not None:
            rps = self.route_passanger_repository.find_by_user_and_route_id(caller_id, route_id)
            is_passanger = any(rp.status in ("pending", "accepted") for rp in rps)

        if not is_driver and not is_passanger:
            raise RouteOwnershipError()

        absences = self.absence_repository.find_by_route_and_date_with_passangers(route_id, absence_date)

        return [
            RouteAbsenceResponse.model_construct(
                route_passanger_id=a.route_passanger_id,
                user_id=a.route_passanger.user_id,
                user_name=a.route_passanger.user.name,
                dependent_id=a.route_passanger.dependent_id,
                dependent_name=a.route_passanger.dependent.name if a.route_passanger.dependent else None,
                absence_date=a.absence_date,
                reason=a.reason,
            )
            for a in absences
        ]

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
        if self.route_passanger_repository is not None:
            for status in ("pending", "accepted"):
                for rp in self.route_passanger_repository.find_by_route_and_status(route_id, status):
                    active_passengers[rp.id] = rp

        if self.notification_service is not None:
            for rp in active_passengers.values():
                self.notification_service.notify_passanger_route_cancelled(rp)

        self.route_repository.delete(route_id)

    # US10-TK18
    def _geocode_address(self, address: AddressModel) -> None:
        """Tenta resolver as coordenadas do endereço via geocoding_service e
        popula address.latitude/longitude in-place. Silenciosamente ignorado
        se geocoding_service for None ou se a API retornar None — endereço
        permanece sem coords (FE pode optar por mostrar placeholder no mapa).

        Chamado por create_route e update_route logo após instanciar o
        AddressModel e antes do address_repository.save.
        """
        if self.geocoding_service is None:
            return

        result = self.geocoding_service.geocode_address(
            street=address.street,
            number=address.number,
            neighborhood=address.neighborhood,
            zip_code=address.zip,
            city=address.city,
            state=address.state,
        )
        if result is None:
            return

        address.latitude = result.latitude
        address.longitude = result.longitude
