from uuid import UUID

from pydantic import BaseModel, ConfigDict


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
