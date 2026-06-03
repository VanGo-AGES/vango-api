"""US15 — Controller de Métricas & Relatórios.

Expõe o endpoint consumido pela tela `trip-reports-screen` do motorista.

Obs.: usa o header mock `X-User-Id` (convenção atual do projeto). A migração
para `get_current_user` (JWT) acontece na US17-TK05.
"""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query

from src.domains.metrics.dtos import MetricsReportResponse, ReportPeriod
from src.domains.metrics.service import MetricsService
from src.infrastructure.dependencies.metrics_dependencies import get_metrics_service

router = APIRouter(prefix="/metrics", tags=["Metrics"])


# US15-TK04
@router.get(
    "/reports",
    response_model=MetricsReportResponse,
    summary="Relatório agregado de viagens do motorista",
    description=(
        "Retorna distância (km), duração (min), passageiros transportados e "
        "viagens realizadas do motorista logado no período selecionado "
        "(day/week/month) e intervalo de datas."
    ),
)
def get_reports(
    service: Annotated[MetricsService, Depends(get_metrics_service)],
    period: Annotated[ReportPeriod, Query()],
    start_date: Annotated[date, Query()],
    x_user_id: Annotated[str, Header(alias="X-User-Id")],
    end_date: Annotated[date | None, Query()] = None,
) -> MetricsReportResponse:
    return service.get_report(UUID(x_user_id), period, start_date, end_date)
