from datetime import time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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


class AddressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    label: str
    street: str
    number: str
    neighborhood: str
    zip: str
    city: str
    state: str
    latitude: float | None = None
    longitude: float | None = None


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
    origin_address: AddressResponse
    destination_address: AddressResponse
