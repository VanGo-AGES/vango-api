"""US07 — DTOs de Stop."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.domains.addresses.dtos import AddressResponse


class StopResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    route_id: UUID
    route_passanger_id: UUID
    address_id: UUID
    order_index: int
    type: str
    updated_at: datetime
    address: AddressResponse
