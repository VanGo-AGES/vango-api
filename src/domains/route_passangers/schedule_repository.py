"""US08-TK02 — Interface do repositório de route_passanger_schedules."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domains.route_passangers.schedule_entity import RoutePassangerScheduleModel


class IRoutePassangerScheduleRepository(ABC):
    @abstractmethod
    def save_many(self, schedules: list[RoutePassangerScheduleModel]) -> list[RoutePassangerScheduleModel]:
        """Persiste uma lista de schedules em lote e retorna as instâncias persistidas."""
        pass

    @abstractmethod
    def find_by_route_passanger_id(self, rp_id: UUID) -> list[RoutePassangerScheduleModel]:
        """Retorna todos os schedules de um vínculo route_passanger."""
        pass

    @abstractmethod
    def delete_by_route_passanger_id(self, rp_id: UUID) -> int:
        """Deleta todos os schedules de um route_passanger. Retorna a quantidade removida."""
        pass

    @abstractmethod
    def replace(
        self,
        rp_id: UUID,
        new_schedules: list[RoutePassangerScheduleModel],
    ) -> list[RoutePassangerScheduleModel]:
        """Substitui atomicamente todos os schedules do route_passanger pelos novos."""
        pass
