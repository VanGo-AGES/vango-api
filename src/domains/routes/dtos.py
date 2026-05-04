from datetime import time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.domains.addresses.dtos import AddressResponse
from src.domains.stops.dtos import StopResponse

VALID_RECURRENCE_DAYS = {"seg", "ter", "qua", "qui", "sex", "sab", "dom"}


# ---------------------------------------------------------------------------
# Address
# ---------------------------------------------------------------------------


class AddressCreate(BaseModel):
    label: str = Field(..., min_length=1, max_length=100)
    street: str = Field(..., min_length=1)
    number: str = Field(..., min_length=1)
    neighborhood: str = Field(..., min_length=1)
    zip: str = Field(..., pattern=r"^\d{5}-\d{3}$")
    city: str = Field(..., min_length=1)
    state: str = Field(..., min_length=2, max_length=2)

    @field_validator("state")
    @classmethod
    def normalize_state_to_uppercase(cls, v: str) -> str:
        return v.upper()


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------


class RouteCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    route_type: str = Field(..., pattern="^(outbound|inbound)$")
    origin: AddressCreate
    destination: AddressCreate
    expected_time: time
    recurrence: str

    @model_validator(mode="after")
    def validate_origin_differs_from_destination(self) -> "RouteCreate":
        origin = self.origin
        destination = self.destination
        if origin.street == destination.street and origin.number == destination.number and origin.zip == destination.zip:
            raise ValueError("Origem e destino não podem ser o mesmo endereço.")
        return self

    @field_validator("recurrence")
    @classmethod
    def validate_recurrence(cls, v: str) -> str:
        days = [d.strip() for d in v.split(",")]
        if not days or days == [""]:
            raise ValueError("Recorrência deve ter pelo menos um dia.")
        invalid = set(days) - VALID_RECURRENCE_DAYS
        if invalid:
            raise ValueError(f"Dias inválidos: {invalid}. Use: seg, ter, qua, qui, sex, sab, dom.")
        if len(days) != len(set(days)):
            raise ValueError("Recorrência não pode ter dias duplicados.")
        return ",".join(days)


class RouteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    route_type: str
    status: str
    recurrence: str
    expected_time: time
    invite_code: str
    max_passengers: int
    accepted_count: int = Field(default=0, description="Quantidade de passageiros aceitos na rota")
    origin_address: AddressResponse
    destination_address: AddressResponse
    # US07-TK-S05 — paradas da rota (geradas a partir de passageiros aceitos)
    stops: list[StopResponse] = Field(default_factory=list)


# US08-TK01
class RouteInviteSummaryResponse(BaseModel):
    """Resumo da rota retornado ao passageiro durante a busca por invite_code.

    Expõe apenas o que o passageiro precisa para decidir se quer solicitar
    entrada: dados básicos da rota + capacidade e quantos já foram aceitos.
    Não expõe lista de passageiros nem stops.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    route_type: str
    recurrence: str
    expected_time: time
    max_passengers: int
    accepted_count: int = Field(..., description="Contagem de passageiros aceitos (injetado pelo service)")
    origin_address: AddressResponse
    destination_address: AddressResponse


# ---------------------------------------------------------------------------
# RouteUpdate
# ---------------------------------------------------------------------------


class RouteUpdate(BaseModel):
    """DTO de atualização parcial de rota. Todos os campos são opcionais.

    Regras:
    - route_type: "outbound" ou "inbound"
    - recurrence: mesma validação de RouteCreate (dias válidos, sem duplicatas, >=1 dia)
    - origin != destination quando AMBOS estão presentes
    """

    name: str | None = Field(default=None, min_length=1, max_length=255)
    route_type: str | None = Field(default=None, pattern="^(outbound|inbound)$")
    origin: AddressCreate | None = None
    destination: AddressCreate | None = None
    expected_time: time | None = None
    recurrence: str | None = None

    @field_validator("recurrence")
    @classmethod
    def validate_recurrence(cls, v: str | None) -> str | None:
        if v is None:
            return None
        days = [d.strip() for d in v.split(",")]
        if not days or days == [""]:
            raise ValueError("Recorrência deve ter pelo menos um dia.")
        seen = set()
        duplicate = []
        for day in days:
            if day not in VALID_RECURRENCE_DAYS:
                raise ValueError(f"Dia inválido: {day}. Use: seg, ter, qua, qui, sex, sab, dom")
            if day in seen:
                duplicate.append(day)
            seen.add(day)
        if duplicate:
            raise ValueError(f"Dias duplicados: {duplicate}. Recorrência não pode ter dias repetidos.")
        return ",".join(days)

    @model_validator(mode="after")
    def validate_origin_differs_from_destination(self) -> "RouteUpdate":
        origin = self.origin
        destination = self.destination
        if origin is not None and destination is not None:
            if origin.street == destination.street and origin.number == destination.number and origin.zip == destination.zip:
                raise ValueError("Origem e destino não podem ter o mesmo endereço.")
        return self
