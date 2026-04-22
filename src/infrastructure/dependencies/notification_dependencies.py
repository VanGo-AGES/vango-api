"""US06-TK07 — DI para INotificationService."""

from src.domains.notifications.service import INotificationService, LoggingNotificationService


def get_notification_service() -> INotificationService:
    return LoggingNotificationService()
