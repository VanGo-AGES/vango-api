"""US07 — DTOs de Stop.

StopResponse espelha a tabela `stops` do banco:
- id, route_id, route_passanger_id, address_id, order_index, type, updated_at.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class StopResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    route_id: UUID
    route_passanger_id: UUID
    address_id: UUID
    order_index: int
    type: str
    updated_at: datetime
