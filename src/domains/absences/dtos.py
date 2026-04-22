"""US06 — DTOs do domínio absences.

Usados pelo fluxo de aviso de ausência do passageiro/guardian na tela 2.3.
"""

from pydantic import BaseModel, ConfigDict


class CreateAbsenceRequest(BaseModel):
    """Payload enviado pelo passageiro (ou guardian) pra avisar ausência numa rota."""

    pass


class AbsenceResponse(BaseModel):
    """Representação de uma ausência persistida."""

    model_config = ConfigDict(from_attributes=True)

    # campos serão preenchidos na implementação (TK18)
