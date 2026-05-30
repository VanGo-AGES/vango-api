"""Smoke test do pipeline de push (FCM).

Envia uma notificação de teste para um device token, usando o mesmo
service account e o mesmo formato de payload do backend real
(notification + data com type/routeId), para validar que a entrega
funciona ponta a ponta — independente do código de roteamento.

Uso:
    python scripts/send_test_push.py "<DEVICE_TOKEN>"

O DEVICE_TOKEN é o valor da coluna users.push_token registrado pelo app.
"""

import os
import sys

import firebase_admin
from firebase_admin import credentials, messaging

CRED_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase_service_account.json")


def main() -> None:
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        print('Erro: passe o device token como argumento.\n  python scripts/send_test_push.py "<DEVICE_TOKEN>"')
        sys.exit(1)

    token = sys.argv[1].strip()

    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.Certificate(CRED_PATH))
        print(f"Firebase Admin inicializado com {CRED_PATH}")

    # Mesmo formato dos envios reais (ver firebase_notification_service.py)
    message = messaging.Message(
        notification=messaging.Notification(
            title="Teste de push VanGo",
            body="Se você está vendo isso, o pipeline FCM funciona.",
        ),
        data={"type": "driver_passenger_requested", "routeId": "smoke-test", "passengerId": ""},
        token=token,
    )

    try:
        message_id = messaging.send(message)
        print(f"OK — mensagem enviada. message_id={message_id}")
        print("Confira a bandeja de notificações do dispositivo.")
    except messaging.UnregisteredError:
        print("FALHA — token inválido/não registrado (UnregisteredError).")
        print("Provável: token errado, ou google-services.json não bate com o projeto, ou o build não tem a config nativa do Firebase.")
        sys.exit(2)
    except Exception as e:  # noqa: BLE001
        print(f"FALHA no envio: {type(e).__name__}: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
