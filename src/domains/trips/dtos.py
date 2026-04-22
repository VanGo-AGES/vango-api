"""US09 — DTOs de execução de viagem.

Contratos Pydantic usados nos endpoints da US09 (motorista gerenciando a
viagem em andamento). Todos os DTOs começam com `pass` e serão
implementados pelas TKs correspondentes.
"""

from pydantic import BaseModel


# US09-TK01
class StartTripRequest(BaseModel):
    """Payload enviado pelo motorista para iniciar a viagem.

    Fields esperados:
    - vehicle_id: UUID — veículo que vai executar a viagem (precisa pertencer
      ao motorista dono da rota)
    - trip_date: datetime | None — data/hora da viagem. Default: now()
    """

    pass


# US09-TK01
class FinishTripRequest(BaseModel):
    """Payload enviado pelo motorista ao finalizar a viagem.

    Fields esperados:
    - total_km: float | None — distância total percorrida (opcional)
    """

    pass


# US09-TK01
class TripPassangerResponse(BaseModel):
    """Representação do vínculo (passageiro x trip) durante/após a execução.

    Fields esperados:
    - id: UUID
    - route_passanger_id: UUID
    - passanger_name: str          — nome do usuário ou dependente
    - status: str                  — "pendente" | "presente" | "ausente"
    - pickup_address_label: str    — endereço esperado de embarque
    - boarded_at: datetime | None
    - alighted_at: datetime | None
    - user_phone: str              — usado pelo FE para deeplink (US13)
    """

    pass


# US09-TK01
class TripResponse(BaseModel):
    """Representação completa da viagem em andamento.

    Fields esperados:
    - id: UUID
    - route_id: UUID
    - route_name: str
    - vehicle_id: UUID
    - trip_date: datetime
    - status: str                  — "iniciada" | "finalizada" | "cancelada"
    - total_km: float | None
    - started_at: datetime | None
    - finished_at: datetime | None
    - trip_passangers: list[TripPassangerResponse]
    """

    pass


# US09-TK01
class TripNextStopResponse(BaseModel):
    """Próxima parada da viagem em andamento.

    Fields esperados:
    - stop_id: UUID
    - order_index: int
    - address_label: str
    - passanger_name: str
    - passanger_phone: str          — telefone pra contato direto (US13)
    - trip_passanger_id: UUID
    - trip_passanger_status: str    — "pendente" | "presente" | "ausente"
    """

    pass
