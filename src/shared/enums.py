"""US00-TK14 — Enums de status (eliminar magic strings).

Herdam de `str` para manter compatibilidade total com as colunas `String`
e com a serialização JSON. Os valores devem ser idênticos às strings hoje
espalhadas pelo código — a TK consiste em trocar as strings cruas por estes
enums sem alterar nenhum valor persistido.
"""

from enum import StrEnum


class TripStatus(StrEnum):
    INICIADA = "iniciada"
    FINALIZADA = "finalizada"
    CANCELADA = "cancelada"


class TripPassangerStatus(StrEnum):
    PENDENTE = "pendente"
    PRESENTE = "presente"
    AUSENTE = "ausente"


class RoutePassangerStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class RouteStatus(StrEnum):
    # ciclo de vida: criada INATIVA -> viagem inicia EM_ANDAMENTO -> viagem finaliza ATIVA
    ATIVA = "ativa"
    INATIVA = "inativa"
    EM_ANDAMENTO = "em_andamento"
