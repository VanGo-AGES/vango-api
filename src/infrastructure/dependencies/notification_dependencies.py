"""US06-TK07 — DI para INotificationService."""

from src.domains.notifications.service import INotificationService, LoggingNotificationService
from src.infrastructure.notifications.firebase_notification_service import (
    FirebaseNotificationService,
)


def get_notification_service() -> INotificationService:
    return LoggingNotificationService()


# US12-TK03 — factory para FirebaseNotificationService (wiring completo em TK05)
def get_firebase_notification_service() -> INotificationService:
    """Retorna uma instância de FirebaseNotificationService.

    Troca o get_notification_service padrão (Logging) pela implementação FCM.
    Será injetado no get_trip_service e outros serviços em US12-TK05.
    """

    return FirebaseNotificationService()
