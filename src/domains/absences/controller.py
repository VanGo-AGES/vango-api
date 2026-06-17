"""US06-TK20 — Controller de absences.

Endpoints:
- POST /absences   (aviso de ausência originado pelo passageiro/guardian,
  acionado pela tela 2.3 "Avisar ausência?")
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.domains.absences.dtos import AbsenceResponse, CreateAbsenceRequest
from src.domains.absences.errors import AbsenceAlreadyReportedError, AbsenceDateNotAllowedError
from src.domains.absences.service import AbsenceService
from src.domains.route_passangers.errors import NotRoutePassangerError
from src.domains.routes.errors import RouteNotFoundError
from src.domains.users.entity import UserModel
from src.infrastructure.auth.dependencies import get_current_user
from src.infrastructure.dependencies.absence_dependencies import get_absence_service

router = APIRouter(prefix="/absences", tags=["Absences"])


@router.post(
    "",
    response_model=AbsenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Avisar ausência numa rota",
    description=(
        "Passageiro (ou guardian em nome de dependente) registra o aviso de "
        "ausência numa data específica da rota. Erros: 404 se a rota não "
        "existir; 403 se o usuário não tiver vínculo ativo; 409 se já houver "
        "ausência pro mesmo RP na data ou se a data for inválida."
    ),
)
def create_absence(
    body: CreateAbsenceRequest,
    service: Annotated[AbsenceService, Depends(get_absence_service)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
) -> AbsenceResponse:
    try:
        return service.create_absence(user_id=current_user.id, data=body)
    except RouteNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except NotRoutePassangerError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error
    except AbsenceAlreadyReportedError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except AbsenceDateNotAllowedError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
