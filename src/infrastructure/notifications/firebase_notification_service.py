"""FirebaseNotificationService: inicializa Firebase Admin SDK e implementa INotificationService stubs.

US12-TK03: inicialização do SDK e wiring DI. Não enviaremos notificações reais aqui.
"""

import logging
from typing import Any

import firebase_admin
from firebase_admin import credentials

from src.config import settings
from src.domains.notifications.service import INotificationService

logger = logging.getLogger(__name__)


class FirebaseNotificationService(INotificationService):
    """Serviço de notificação que inicializa o Firebase Admin SDK.

    Os métodos de envio permanecem como stubs nesta tarefa (TK03).
    """

    def __init__(self) -> None:
        # Inicializa o Firebase Admin SDK apenas se não houver apps já inicializadas
        try:
            if not getattr(firebase_admin, "_apps", None):
                cred = credentials.Certificate(settings.firebase_credentials_path)
                firebase_admin.initialize_app(cred)
                logger.info("FIREBASE: Admin SDK inicializado com %s", settings.firebase_credentials_path)
            else:
                logger.debug("FIREBASE: Admin SDK já inicializado, pulando inicialização")
        except Exception as e:  # pragma: no cover - captura problemas de ambiente/credenciais
            logger.warning("FIREBASE: falha ao inicializar Admin SDK: %s", e)

    # Implementação de stubs que cumprem a interface
    def notify_passanger_accepted(self, rp: Any) -> None:
        pass

    def notify_passanger_rejected(self, rp: Any) -> None:
        pass

    def notify_passanger_removed(self, rp: Any) -> None:
        pass

    def notify_driver_passanger_requested(self, rp: Any) -> None:
        pass

    def notify_driver_passanger_left(self, rp: Any) -> None:
        pass

    def notify_driver_passanger_schedules_changed(self, rp: Any) -> None:
        pass

    def notify_passanger_route_cancelled(self, rp: Any) -> None:
        pass

    def notify_driver_passanger_absence_reported(self, rp: Any) -> None:
        pass

    def notify_trip_started(self, trip: Any) -> None:
        pass

    def notify_trip_arriving_at_stop(self, trip_passanger: Any) -> None:
        pass

    def notify_trip_finished(self, trip: Any) -> None:
        pass

    def notify_passanger_boarded(self, trip_passanger: Any) -> None:
        pass

    def notify_passanger_absent(self, trip_passanger: Any) -> None:
        pass
