"""
Interface abstrata INotificationService + implementação concreta stub
LoggingNotificationService (apenas loga, não persiste). A implementação
real (push via Firebase, e-mail, etc.) ficará para sprints futuras.
"""

import logging
from abc import ABC, abstractmethod

from src.domains.route_passangers.entity import RoutePassangerModel
from src.domains.trips.entity import TripModel, TripPassangerModel

logger = logging.getLogger(__name__)


class INotificationService(ABC):
    @abstractmethod
    def notify_passanger_accepted(self, rp: RoutePassangerModel) -> None:
        pass

    @abstractmethod
    def notify_passanger_rejected(self, rp: RoutePassangerModel) -> None:
        pass

    @abstractmethod
    def notify_passanger_removed(self, rp: RoutePassangerModel) -> None:
        pass

    # -----------------------------------------------------------------
    # US08-TK04 — eventos originados pelo passageiro
    # -----------------------------------------------------------------

    @abstractmethod
    def notify_driver_passanger_requested(self, rp: RoutePassangerModel) -> None:
        """Notifica o motorista que há uma nova solicitação de passageiro."""
        pass

    @abstractmethod
    def notify_driver_passanger_left(self, rp: RoutePassangerModel) -> None:
        """Notifica o motorista que um passageiro saiu da rota."""
        pass

    @abstractmethod
    def notify_driver_passanger_schedules_changed(self, rp: RoutePassangerModel) -> None:
        """Notifica o motorista que o passageiro alterou seus dias de participação."""
        pass

    # -----------------------------------------------------------------
    # US06-TK16 — exclusão da rota pelo motorista
    # -----------------------------------------------------------------

    @abstractmethod
    def notify_passanger_route_cancelled(self, rp: RoutePassangerModel) -> None:
        """Notifica passageiro (pending/accepted) que a rota foi excluída pelo motorista."""
        pass

    # -----------------------------------------------------------------
    # US06-TK19 — aviso de ausência originado pelo passageiro/guardian
    # -----------------------------------------------------------------

    @abstractmethod
    def notify_driver_passanger_absence_reported(self, rp: RoutePassangerModel) -> None:
        """Notifica o motorista que o passageiro avisou ausência numa data."""
        pass

    # -----------------------------------------------------------------
    # US09-TK05 — eventos de execução de viagem
    # -----------------------------------------------------------------

    @abstractmethod
    def notify_trip_started(self, trip: TripModel) -> None:
        """Notifica todos os passageiros da trip que a viagem começou."""
        pass

    @abstractmethod
    def notify_trip_arriving_at_stop(self, trip_passanger: TripPassangerModel) -> None:
        """Notifica o passageiro da próxima parada que a van está chegando."""
        pass

    @abstractmethod
    def notify_trip_finished(self, trip: TripModel) -> None:
        """Notifica passageiros/guardians que a viagem foi finalizada."""
        pass


class LoggingNotificationService(INotificationService):
    """Implementação stub que apenas registra as notificações em log."""

    def notify_passanger_accepted(self, rp: RoutePassangerModel) -> None:
        pass

    def notify_passanger_rejected(self, rp: RoutePassangerModel) -> None:
        pass

    def notify_passanger_removed(self, rp: RoutePassangerModel) -> None:
        pass

    # US08-TK04
    def notify_driver_passanger_requested(self, rp: RoutePassangerModel) -> None:
        pass

    def notify_driver_passanger_left(self, rp: RoutePassangerModel) -> None:
        pass

    def notify_driver_passanger_schedules_changed(self, rp: RoutePassangerModel) -> None:
        pass

    # US06-TK16
    def notify_passanger_route_cancelled(self, rp: RoutePassangerModel) -> None:
        logger.info(
            "notify_passanger_route_cancelled: rota cancelada, passageiro notificado " "[rp_id=%s, user_id=%s, status=%s]",
            rp.id,
            rp.user_id,
            rp.status,
        )

    # US06-TK19
    def notify_driver_passanger_absence_reported(self, rp: RoutePassangerModel) -> None:
        pass

    # US09-TK05
    def notify_trip_started(self, trip: TripModel) -> None:
        logger.info(
            "notify_trip_started: viagem iniciada [trip_id=%s, route_id=%s]",
            trip.id,
            trip.route_id,
        )

    def notify_trip_arriving_at_stop(self, trip_passanger: TripPassangerModel) -> None:
        logger.info(
            "notify_trip_arriving_at_stop: van chegando à parada [trip_passanger_id=%s, trip_id=%s]",
            trip_passanger.id,
            trip_passanger.trip_id,
        )

    def notify_trip_finished(self, trip: TripModel) -> None:
        logger.info(
            "notify_trip_finished: viagem finalizada [trip_id=%s, route_id=%s]",
            trip.id,
            trip.route_id,
        )
