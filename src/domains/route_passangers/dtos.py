from pydantic import BaseModel


# US06-TK05
class RoutePassangerResponse(BaseModel):
    pass


# ---------------------------------------------------------------------------
# US08 — DTOs de join/leave/update schedules
# ---------------------------------------------------------------------------


# US08-TK01
class RoutePassangerScheduleRequest(BaseModel):
    """Item de agendamento enviado pelo passageiro: dia + endereço de embarque."""

    pass


# US08-TK01
class RoutePassangerScheduleResponse(BaseModel):
    """Representação de um agendamento persistido."""

    pass


# US08-TK01
class JoinRouteRequest(BaseModel):
    """Payload para um passageiro solicitar entrada em uma rota.

    Fields esperados:
    - dependent_id: UUID | None  — se o guardian está solicitando para um dependente
    - schedules: list[RoutePassangerScheduleRequest]  — pelo menos 1 agendamento,
      todos com day_of_week pertencente à recurrence da rota.
    """

    pass


# US08-TK01
class UpdateSchedulesRequest(BaseModel):
    """Payload para o passageiro atualizar seus dias de participação.

    Substitui completamente os schedules atuais pelos fornecidos.
    """

    pass


# ---------------------------------------------------------------------------
# US08 — Home do passageiro (minhas rotas)
# ---------------------------------------------------------------------------


# US08-TK13
class PassangerRouteResponse(BaseModel):
    """Item da lista 'Minhas Rotas' da home do passageiro.

    Fields esperados:
    - route_id: UUID
    - route_name: str
    - driver_name: str
    - driver_phone: str            — usado pelo FE pra montar deeplink tel:/wa.me (US13)
    - origin_label: str
    - destination_label: str
    - expected_time: time
    - recurrence: list[str]
    - status: str                 — status da rota (inativa/ativa/em_andamento)
    - membership_status: str      — status do vínculo do passageiro (pending/accepted)
    - schedules: list[RoutePassangerScheduleResponse]
    - joined_at: datetime
    - dependent_name: str | None  — preenchido quando o vínculo é de um dependente
    """

    pass
