"""FirebaseNotificationService: envio de notificações push.

Modelo híbrido de entrega:
- Tokens Expo (ExponentPushToken[...] / ExpoPushToken[...]) -> Expo Push Service (HTTP).
- Demais tokens (FCM, gerados pelo Android) -> Firebase Admin SDK (FCM HTTP v1).

Isso permite manter o Android no FCM e atender o iOS via Expo Push sem
react-native-firebase no app.
"""

import logging
from typing import Any

import firebase_admin
import requests
from firebase_admin import credentials, messaging

from src.config import settings
from src.domains.notifications.service import INotificationService

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


def _is_expo_token(token: str) -> bool:
    """True se o token for um Expo push token (entregue via Expo Push Service)."""
    return isinstance(token, str) and (token.startswith("ExponentPushToken[") or token.startswith("ExpoPushToken["))


class FirebaseNotificationService(INotificationService):
    """Serviço de notificação que roteia entre Expo Push e FCM por tipo de token."""

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

    # -----------------------------------------------------------------
    # Envio — roteia por tipo de token. Propaga exceções (usado pelo teste).
    # -----------------------------------------------------------------
    def _send_push(self, token: str, title: str, body: str, data: dict[str, str]) -> str:
        if not token:
            raise ValueError("push token vazio")

        if _is_expo_token(token):
            resp = requests.post(
                EXPO_PUSH_URL,
                json={"to": token, "title": title, "body": body, "data": data},
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.text

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=data,
            token=token,
        )
        return messaging.send(message)

    def _safe_send(self, token: str, title: str, body: str, data: dict[str, str]) -> None:
        """Versão tolerante a falhas para fluxos de negócio: nunca levanta exceção."""
        try:
            if token:
                self._send_push(token, title, body, data)
        except Exception as e:  # noqa: BLE001 - push nunca deve quebrar o fluxo de negócio
            logger.warning("PUSH: falha ao enviar (%s): %s", data.get("type"), e)

    # -----------------------------------------------------------------
    # Eventos de viagem
    # -----------------------------------------------------------------
    def notify_trip_started(self, trip: Any) -> None:
        try:
            self._safe_send(
                trip.route.driver.push_token,
                "Viagem iniciada",
                "Sua viagem foi iniciada!",
                {"type": "trip_started", "routeId": str(trip.route_id), "passengerId": ""},
            )
        except (AttributeError, TypeError):
            pass

        try:
            for tp in trip.trip_passangers:
                try:
                    self._safe_send(
                        tp.route_passanger.user.push_token,
                        "Viagem iniciada",
                        "Seu motorista está chegando em breve!",
                        {"type": "trip_started", "routeId": str(trip.route_id), "passengerId": ""},
                    )
                except (AttributeError, TypeError):
                    pass
        except (AttributeError, TypeError):
            pass

    def notify_trip_arriving_at_stop(self, trip_passanger: Any) -> None:
        try:
            self._safe_send(
                trip_passanger.route_passanger.user.push_token,
                "Motorista chegando",
                "Seu motorista está próximo da sua localização!",
                {
                    "type": "trip_arriving",
                    "routeId": str(trip_passanger.route_passanger.route_id),
                    "passengerId": str(trip_passanger.route_passanger_id),
                },
            )
        except (AttributeError, TypeError):
            pass

    def notify_trip_arrived_at_stop(self, trip_passanger: Any) -> None:
        try:
            self._safe_send(
                trip_passanger.route_passanger.user.push_token,
                "Motorista chegou",
                "Seu motorista chegou à sua parada!",
                {
                    "type": "trip_arrived",
                    "routeId": str(trip_passanger.route_passanger.route_id),
                    "passengerId": str(trip_passanger.route_passanger_id),
                },
            )
        except (AttributeError, TypeError):
            pass

    def notify_trip_finished(self, trip: Any) -> None:
        try:
            self._safe_send(
                trip.route.driver.push_token,
                "Viagem finalizada",
                "Sua viagem foi finalizada!",
                {"type": "trip_finished", "routeId": str(trip.route_id), "passengerId": ""},
            )
        except (AttributeError, TypeError):
            pass

        try:
            for tp in trip.trip_passangers:
                try:
                    self._safe_send(
                        tp.route_passanger.user.push_token,
                        "Viagem finalizada",
                        "Viagem concluída com sucesso!",
                        {"type": "trip_finished", "routeId": str(trip.route_id), "passengerId": ""},
                    )
                except (AttributeError, TypeError):
                    pass
        except (AttributeError, TypeError):
            pass

    def notify_passanger_boarded(self, trip_passanger: Any) -> None:
        try:
            self._safe_send(
                trip_passanger.route_passanger.user.push_token,
                "Embarque confirmado",
                "Você foi embarcado com sucesso!",
                {
                    "type": "passenger_boarded",
                    "routeId": str(trip_passanger.route_passanger.route_id),
                    "passengerId": str(trip_passanger.route_passanger_id),
                },
            )
        except (AttributeError, TypeError):
            pass

    def notify_passanger_absent(self, trip_passanger: Any) -> None:
        try:
            self._safe_send(
                trip_passanger.route_passanger.user.push_token,
                "Ausência registrada",
                "Você foi registrado como ausente nesta viagem!",
                {
                    "type": "passenger_absent",
                    "routeId": str(trip_passanger.route_passanger.route_id),
                    "passengerId": str(trip_passanger.route_passanger_id),
                },
            )
        except (AttributeError, TypeError):
            pass

    # -----------------------------------------------------------------
    # Eventos de rota / passageiro
    # -----------------------------------------------------------------
    def notify_passanger_accepted(self, rp: Any) -> None:
        try:
            self._safe_send(
                rp.user.push_token,
                "Aceito na rota",
                "Parabéns! Você foi aceito na rota!",
                {"type": "passenger_accepted", "routeId": str(rp.route_id), "passengerId": str(rp.id)},
            )
        except (AttributeError, TypeError):
            pass

    def notify_passanger_rejected(self, rp: Any) -> None:
        try:
            self._safe_send(
                rp.user.push_token,
                "Solicitação rejeitada",
                "Sua solicitação foi rejeitada.",
                {"type": "passenger_rejected", "routeId": str(rp.route_id), "passengerId": str(rp.id)},
            )
        except (AttributeError, TypeError):
            pass

    def notify_passanger_removed(self, rp: Any) -> None:
        try:
            self._safe_send(
                rp.user.push_token,
                "Removido da rota",
                "Você foi removido da rota.",
                {"type": "passenger_removed", "routeId": str(rp.route_id), "passengerId": str(rp.id)},
            )
        except (AttributeError, TypeError):
            pass

    def notify_driver_passanger_requested(self, rp: Any) -> None:
        try:
            self._safe_send(
                rp.route.driver.push_token,
                "Nova solicitação",
                "Um novo passageiro solicitou entrada na rota!",
                {"type": "driver_passenger_requested", "routeId": str(rp.route_id), "passengerId": str(rp.id)},
            )
        except (AttributeError, TypeError):
            pass

    def notify_driver_passanger_left(self, rp: Any) -> None:
        try:
            self._safe_send(
                rp.route.driver.push_token,
                "Passageiro saiu",
                "Um passageiro saiu da rota.",
                {"type": "driver_passenger_left", "routeId": str(rp.route_id), "passengerId": str(rp.id)},
            )
        except (AttributeError, TypeError):
            pass

    def notify_driver_passanger_schedules_changed(self, rp: Any) -> None:
        pass

    def notify_passanger_route_cancelled(self, rp: Any) -> None:
        try:
            self._safe_send(
                rp.user.push_token,
                "Rota cancelada",
                "A rota foi cancelada.",
                {"type": "route_cancelled", "routeId": str(rp.route_id), "passengerId": str(rp.id)},
            )
        except (AttributeError, TypeError):
            pass

    def notify_driver_passanger_absence_reported(self, rp: Any) -> None:
        try:
            self._safe_send(
                rp.route.driver.push_token,
                "Ausência reportada",
                "Um passageiro avisou ausência nesta data.",
                {"type": "driver_passenger_absent", "routeId": str(rp.route_id), "passengerId": str(rp.id)},
            )
        except (AttributeError, TypeError):
            pass

    # -----------------------------------------------------------------
    # Notificações por tópico (FCM) — usadas pelo Socket.IO.
    # Mantidas no FCM; o app não se inscreve em tópicos hoje (pendência separada).
    # -----------------------------------------------------------------
    def notify_passanger_driver_approaching(self, user_id: str, route_id: str) -> None:
        try:
            message = messaging.Message(
                notification=messaging.Notification(title="Motorista chegando", body="Seu motorista está próximo da sua parada!"),
                data={"type": "trip_arriving", "routeId": route_id, "passengerId": ""},
                topic=f"user_{user_id}",
            )
            messaging.send(message)
        except Exception as e:
            logger.warning(
                "FIREBASE: falha ao enviar push de aproximação user_id=%s route_id=%s: %s",
                user_id,
                route_id,
                e,
            )

    def notify_passanger_driver_arrived(self, user_id: str, route_id: str) -> None:
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title="Motorista chegou",
                    body="Seu motorista chegou à sua parada!",
                ),
                data={"type": "trip_arrived", "routeId": route_id, "passengerId": ""},
                topic=f"user_{user_id}",
            )
            messaging.send(message)
        except Exception as e:
            logger.warning(
                "FIREBASE: falha ao enviar push de chegada user_id=%s route_id=%s: %s",
                user_id,
                route_id,
                e,
            )

    # -----------------------------------------------------------------
    # Helper de teste — envio manual; propaga erros para o endpoint reportar.
    # -----------------------------------------------------------------
    def send_test_notification(self, token: str, title: str, body: str) -> str:
        return self._send_push(
            token,
            title,
            body,
            {"type": "test_notification", "routeId": "", "passengerId": ""},
        )
