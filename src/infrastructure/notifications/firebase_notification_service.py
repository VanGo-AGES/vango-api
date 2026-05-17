"""FirebaseNotificationService: inicializa Firebase Admin SDK e implementa INotificationService.

US12-TK03: inicialização do SDK e wiring DI.
US12-TK04: envio real de mensagens FCM.
"""

import logging
from typing import Any

import firebase_admin
from firebase_admin import credentials, messaging

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

    # Implementação que envia mensagens reais via FCM
    def notify_trip_started(self, trip: Any) -> None:
        try:
            # Notifica o driver
            try:
                push_token = trip.route.driver.push_token
                if push_token:
                    message = messaging.Message(
                        notification=messaging.Notification(title="Viagem iniciada", body="Sua viagem foi iniciada!"),
                        token=push_token,
                    )
                    messaging.send(message)
            except (AttributeError, TypeError):
                pass

            # Notifica os passageiros
            try:
                for tp in trip.trip_passangers:
                    try:
                        push_token = tp.route_passanger.user.push_token
                        if push_token:
                            message = messaging.Message(
                                notification=messaging.Notification(title="Viagem iniciada", body="Seu motorista está chegando em breve!"),
                                token=push_token,
                            )
                            messaging.send(message)
                    except (AttributeError, TypeError):
                        pass
            except (AttributeError, TypeError):
                pass
        except (AttributeError, TypeError):
            pass

    def notify_trip_arriving_at_stop(self, trip_passanger: Any) -> None:
        try:
            push_token = trip_passanger.route_passanger.user.push_token
            if push_token:
                message = messaging.Message(
                    notification=messaging.Notification(title="Motorista chegando", body="Seu motorista está próximo da sua localização!"),
                    token=push_token,
                )
                messaging.send(message)
        except (AttributeError, TypeError):
            pass

    def notify_trip_arrived_at_stop(self, trip_passanger: Any) -> None:
        try:
            push_token = trip_passanger.route_passanger.user.push_token
            if push_token:
                message = messaging.Message(
                    notification=messaging.Notification(title="Motorista chegou", body="Seu motorista chegou à sua parada!"),
                    token=push_token,
                )
                messaging.send(message)
        except (AttributeError, TypeError):
            pass

    def notify_trip_finished(self, trip: Any) -> None:
        try:
            # Notifica o driver
            try:
                push_token = trip.route.driver.push_token
                if push_token:
                    message = messaging.Message(
                        notification=messaging.Notification(title="Viagem finalizada", body="Sua viagem foi finalizada!"),
                        token=push_token,
                    )
                    messaging.send(message)
            except (AttributeError, TypeError):
                pass

            # Notifica os passageiros
            try:
                for tp in trip.trip_passangers:
                    try:
                        push_token = tp.route_passanger.user.push_token
                        if push_token:
                            message = messaging.Message(
                                notification=messaging.Notification(title="Viagem finalizada", body="Viagem concluída com sucesso!"),
                                token=push_token,
                            )
                            messaging.send(message)
                    except (AttributeError, TypeError):
                        pass
            except (AttributeError, TypeError):
                pass
        except (AttributeError, TypeError):
            pass

    def notify_passanger_boarded(self, trip_passanger: Any) -> None:
        try:
            push_token = trip_passanger.route_passanger.user.push_token
            if push_token:
                message = messaging.Message(
                    notification=messaging.Notification(title="Embarque confirmado", body="Você foi embarcado com sucesso!"),
                    token=push_token,
                )
                messaging.send(message)
        except (AttributeError, TypeError):
            pass

    def notify_passanger_absent(self, trip_passanger: Any) -> None:
        try:
            push_token = trip_passanger.route_passanger.user.push_token
            if push_token:
                message = messaging.Message(
                    notification=messaging.Notification(title="Ausência registrada", body="Você foi registrado como ausente nesta viagem!"),
                    token=push_token,
                )
                messaging.send(message)
        except (AttributeError, TypeError):
            pass

    def notify_passanger_accepted(self, rp: Any) -> None:
        try:
            push_token = rp.user.push_token
            if push_token:
                message = messaging.Message(
                    notification=messaging.Notification(title="Aceito na rota", body="Parabéns! Você foi aceito na rota!"),
                    token=push_token,
                )
                messaging.send(message)
        except (AttributeError, TypeError):
            pass

    def notify_passanger_rejected(self, rp: Any) -> None:
        try:
            push_token = rp.user.push_token
            if push_token:
                message = messaging.Message(
                    notification=messaging.Notification(title="Solicitação rejeitada", body="Sua solicitação foi rejeitada."),
                    token=push_token,
                )
                messaging.send(message)
        except (AttributeError, TypeError):
            pass

    def notify_passanger_removed(self, rp: Any) -> None:
        try:
            push_token = rp.user.push_token
            if push_token:
                message = messaging.Message(
                    notification=messaging.Notification(title="Removido da rota", body="Você foi removido da rota."),
                    token=push_token,
                )
                messaging.send(message)
        except (AttributeError, TypeError):
            pass

    def notify_driver_passanger_requested(self, rp: Any) -> None:
        try:
            push_token = rp.route.driver.push_token
            if push_token:
                message = messaging.Message(
                    notification=messaging.Notification(title="Nova solicitação", body="Um novo passageiro solicitou entrada na rota!"),
                    token=push_token,
                )
                messaging.send(message)
        except (AttributeError, TypeError):
            pass

    def notify_driver_passanger_left(self, rp: Any) -> None:
        try:
            push_token = rp.route.driver.push_token
            if push_token:
                message = messaging.Message(
                    notification=messaging.Notification(title="Passageiro saiu", body="Um passageiro saiu da rota."),
                    token=push_token,
                )
                messaging.send(message)
        except (AttributeError, TypeError):
            pass

    def notify_driver_passanger_schedules_changed(self, rp: Any) -> None:
        pass

    def notify_passanger_route_cancelled(self, rp: Any) -> None:
        try:
            push_token = rp.user.push_token
            if push_token:
                message = messaging.Message(
                    notification=messaging.Notification(title="Rota cancelada", body="A rota foi cancelada."),
                    token=push_token,
                )
                messaging.send(message)
        except (AttributeError, TypeError):
            pass

    def notify_driver_passanger_absence_reported(self, rp: Any) -> None:
        try:
            push_token = rp.route.driver.push_token
            if push_token:
                message = messaging.Message(
                    notification=messaging.Notification(title="Ausência reportada", body="Um passageiro avisou ausência nesta data."),
                    token=push_token,
                )
                messaging.send(message)
        except (AttributeError, TypeError):
            pass

    def notify_passanger_driver_approaching(self, user_id: str, route_id: str) -> None:
        try:
            message = messaging.Message(
                notification=messaging.Notification(title="Motorista chegando", body="Seu motorista está próximo da sua parada!"),
                topic=f"user_{user_id}",
            )
            messaging.send(message)
        except Exception:
            pass

    def notify_passanger_driver_arrived(self, user_id: str, route_id: str) -> None:
        try:
            message = messaging.Message(
                notification=messaging.Notification(title="Motorista chegou", body="Seu motorista chegou à sua parada!"),
                topic=f"user_{user_id}",
            )
            messaging.send(message)
        except Exception:
            pass
