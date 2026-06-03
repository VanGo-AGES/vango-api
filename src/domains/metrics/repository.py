"""US15 — Interface do repositório de métricas.

A implementação concreta fica em
`src/infrastructure/repositories/trip_metrics_repository.py` (US15-TK02).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class MetricsAggregate:
    """Resultado bruto da agregação no banco (uma passada por intervalo)."""

    total_km: float
    total_duration_seconds: int
    passengers: int
    trips: int


class ITripMetricsRepository(ABC):
    # US15-TK02
    @abstractmethod
    def aggregate_driver_metrics(self, driver_id: UUID, start: datetime, end: datetime) -> MetricsAggregate:
        """Agrega as métricas das viagens finalizadas do motorista no intervalo.

        - Soma `trips.total_km` (distância).
        - Soma a duração (`finished_at - started_at`) em segundos.
        - Conta os `trip_passangers` embarcados/presentes.
        - Conta as trips finalizadas.
        Filtra por `routes.driver_id` (join trips→routes) e `[start, end]`.
        Retorna zeros (não None) quando não há registros.
        """
        ...
