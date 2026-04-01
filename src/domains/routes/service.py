from uuid import UUID

from src.domains.routes.dtos import RouteCreate
from src.domains.routes.entity import RouteModel
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
        """
        Cria uma nova rota para o motorista.
        - Busca o veículo do motorista para obter max_passengers.
        - Persiste os endereços de origem e destino.
        - Gera o código de convite único.
        - Salva a rota com status 'inativa'.
        """
        pass

    def regenerate_invite_code(self, route_id: UUID, driver_id: UUID) -> RouteModel:
        """
        Gera um novo código de convite para a rota.
        O código anterior é invalidado imediatamente.
        Verifica ownership: apenas o motorista dono da rota pode revogar.
        """
        pass

    def _generate_invite_code(self) -> str:
        """Gera um código alfanumérico único de 5 caracteres (maiúsculas + dígitos)."""
        pass

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
