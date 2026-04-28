"""US06-TK06 — Interface do repositório de route_passangers."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domains.route_passangers.entity import RoutePassangerModel


class IRoutePassangerRepository(ABC):
    @abstractmethod
    def save(self, rp: RoutePassangerModel) -> RoutePassangerModel:
        """Persiste um novo vínculo e retorna a instância salva (com id preenchido)."""
        pass

    @abstractmethod
    def find_by_id(self, rp_id: UUID) -> RoutePassangerModel | None:
        pass

    @abstractmethod
    def find_by_route_and_status(self, route_id: UUID, status: str | None = None) -> list[RoutePassangerModel]:
        pass

    @abstractmethod
    def update_status(self, rp_id: UUID, new_status: str) -> RoutePassangerModel | None:
        pass

    @abstractmethod
    def count_accepted_by_route(self, route_id: UUID) -> int:
        pass

    @abstractmethod
    def delete(self, rp_id: UUID) -> bool:
        pass

    # -------------------------------------------------------------------
    # US08-TK03
    # -------------------------------------------------------------------

    @abstractmethod
    def find_active_by_user_and_route(
        self,
        user_id: UUID,
        dependent_id: UUID | None,
        route_id: UUID,
    ) -> RoutePassangerModel | None:
        """Retorna o vínculo ATIVO (status pending ou accepted) do par
        (user_id, dependent_id) na rota, ou None. Usado para detectar
        duplicatas no join e localizar o RP corrente no leave/update.
        """
        pass

    @abstractmethod
    def find_by_user_and_route_id(
        self,
        user_id: UUID,
        route_id: UUID,
    ) -> list[RoutePassangerModel]:
        """Retorna todos os vínculos do user_id naquela rota (self +
        dependentes, qualquer status). Usado para queries auxiliares.
        """
        pass

    # -------------------------------------------------------------------
    # US08-TK13 — home do passageiro (minhas rotas)
    # -------------------------------------------------------------------

    @abstractmethod
    def find_active_with_route_by_user(
        self,
        user_id: UUID,
    ) -> list[RoutePassangerModel]:
        """Retorna todos os vínculos ativos (status pending ou accepted) do
        usuário, seja como passageiro (user_id) ou como guardian de algum
        dependente, com RouteModel (e schedules) já carregados.

        Ordenação: joined_at desc.
        """
        pass
