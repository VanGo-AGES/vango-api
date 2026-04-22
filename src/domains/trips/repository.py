"""US09 — Interfaces de repositório para o domínio trips.

Cada interface tem impl concreta em src/infrastructure/repositories/ e é
injetada no TripService via Depends.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from src.domains.trips.entity import AbsenceModel, TripModel, TripPassangerModel


class ITripRepository(ABC):
    # US09-TK02
    @abstractmethod
    def save(self, trip: TripModel) -> TripModel:
        """Persiste uma nova trip."""
        pass

    # US09-TK02
    @abstractmethod
    def find_by_id(self, trip_id: UUID) -> TripModel | None:
        """Busca trip por id (com route, vehicle, trip_passangers eager-loaded)."""
        pass

    # US09-TK02
    @abstractmethod
    def find_in_progress_by_route(self, route_id: UUID) -> TripModel | None:
        """Busca a trip com status 'iniciada' de uma rota, se existir.

        Usado para:
        - impedir start_trip quando já existe outra em andamento;
        - permitir que o motorista volte pra viagem em andamento.
        """
        pass

    # US09-TK02
    @abstractmethod
    def update_status(self, trip_id: UUID, status: str, finished_at: datetime | None, total_km: float | None) -> TripModel | None:
        """Atualiza status/finished_at/total_km. Retorna None se não existe."""
        pass


class ITripPassangerRepository(ABC):
    # US09-TK03
    @abstractmethod
    def save_all(self, trip_passangers: list[TripPassangerModel]) -> list[TripPassangerModel]:
        """Persiste em lote (usado pelo start_trip ao pré-criar registros)."""
        pass

    # US09-TK03
    @abstractmethod
    def find_by_id(self, trip_passanger_id: UUID) -> TripPassangerModel | None:
        pass

    # US09-TK03
    @abstractmethod
    def find_by_trip(self, trip_id: UUID) -> list[TripPassangerModel]:
        """Retorna todos os trip_passangers da trip, ordenados pela
        ordem das stops da rota (order_index).
        """
        pass

    # US09-TK03
    @abstractmethod
    def update_status(
        self,
        trip_passanger_id: UUID,
        status: str,
        boarded_at: datetime | None = None,
        alighted_at: datetime | None = None,
    ) -> TripPassangerModel | None:
        """Atualiza status/boarded_at/alighted_at. Retorna None se não existe."""
        pass

    # US09-TK03
    @abstractmethod
    def bulk_alight_presents(self, trip_id: UUID, alighted_at: datetime) -> int:
        """Marca alighted_at para todos os trip_passangers com status='presente'
        que ainda não têm alighted_at. Retorna o número de linhas afetadas.
        Usado pelo finish_trip.
        """
        pass


class IAbsenceRepository(ABC):
    # US09-TK04
    @abstractmethod
    def find_by_route_and_date(self, route_id: UUID, absence_date: datetime) -> list[AbsenceModel]:
        """Retorna todos os avisos de falta para a rota/data indicadas.

        Usado pelo start_trip para pré-marcar trip_passengers ausentes.
        Considera-se data o intervalo [00:00, 23:59] do dia fornecido.
        """
        pass

    # -------------------------------------------------------------------
    # US06-TK18 — criação de Absence pelo passageiro/guardian
    # -------------------------------------------------------------------

    @abstractmethod
    def save(self, absence: AbsenceModel) -> AbsenceModel:
        """Persiste uma nova ausência avisada pelo passageiro/guardian."""
        pass

    @abstractmethod
    def find_for_route_passanger_on_date(
        self,
        route_passanger_id: UUID,
        absence_date: datetime,
    ) -> AbsenceModel | None:
        """Retorna a ausência do RP naquele dia, se existir.

        Usado para bloquear criação duplicada (mesma dupla RP + dia).
        Considera-se data o intervalo [00:00, 23:59] do dia fornecido.
        """
        pass
