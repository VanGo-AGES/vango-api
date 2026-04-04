import random
import string
from uuid import UUID

from src.domains.addresses.entity import AddressModel
from src.domains.routes.dtos import RouteCreate
from src.domains.routes.entity import RouteModel
from src.domains.routes.errors import NoVehicleError, RouteNotFoundError, RouteOwnershipError
from src.domains.routes.repository import IAddressRepository, IRouteRepository
from src.domains.vehicles.repository import IVehicleRepository


class RouteService:
    def __init__(
        self,
        route_repository: IRouteRepository,
        address_repository: IAddressRepository,
        vehicle_repository: IVehicleRepository,
    ):
        self.route_repository = route_repository
        self.address_repository = address_repository
        self.vehicle_repository = vehicle_repository

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
