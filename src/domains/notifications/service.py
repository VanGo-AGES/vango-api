"""
Interface abstrata INotificationService + implementação concreta stub
LoggingNotificationService (apenas loga, não persiste). A implementação
real (push via Firebase, e-mail, etc.) ficará para sprints futuras.
"""

from abc import ABC, abstractmethod

from src.domains.route_passangers.entity import RoutePassangerModel


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
        pass
