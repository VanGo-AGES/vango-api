from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.infrastructure.dependencies.auth_dependencies import get_current_user
from src.infrastructure.dependencies.vehicle_dependencies import get_vehicle_service

from .dtos import VehicleCreate, VehicleResponse, VehicleUpdate
from .errors import VehicleAccessDeniedError, VehicleNotFoundError, VehicleOwnershipError
from .service import VehicleService

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


@router.post(
    "/",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adicionar veículo",
    description="Permite que um motorista adicione um veículo ao seu perfil.",
)
def create_vehicle(
    body: VehicleCreate,
    service: Annotated[VehicleService, Depends(get_vehicle_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> VehicleResponse:
    try:
        return service.add_vehicle(
            user_id=current_user["id"],
            user_role=current_user["role"],
            data=body,
        )
    except VehicleAccessDeniedError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error


@router.get(
    "/",
    response_model=list[VehicleResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar veículos do usuário",
    description="Retorna todos os veículos cadastrados pelo motorista logado.",
)
def list_vehicles(
    service: Annotated[VehicleService, Depends(get_vehicle_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> list[VehicleResponse]:
    return service.get_vehicles(current_user["id"])


@router.get(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    status_code=status.HTTP_200_OK,
    summary="Buscar veículo por ID",
    description="Retorna um veículo específico do motorista logado.",
)
def get_vehicle(
    vehicle_id: UUID,
    service: Annotated[VehicleService, Depends(get_vehicle_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> VehicleResponse:
    try:
        return service.get_vehicle(current_user["id"], vehicle_id)
    except VehicleNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except VehicleOwnershipError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error


@router.put(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    status_code=status.HTTP_200_OK,
    summary="Atualizar veículo",
    description="Atualiza os dados de um veículo do motorista logado.",
)
def update_vehicle(
    vehicle_id: UUID,
    body: VehicleUpdate,
    service: Annotated[VehicleService, Depends(get_vehicle_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> VehicleResponse:
    try:
        return service.update_vehicle(current_user["id"], vehicle_id, body)
    except VehicleNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except VehicleOwnershipError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error


@router.delete(
    "/{vehicle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir veículo",
    description="Remove um veículo do perfil do motorista logado.",
)
def delete_vehicle(
    vehicle_id: UUID,
    service: Annotated[VehicleService, Depends(get_vehicle_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> None:
    try:
        service.delete_vehicle(current_user["id"], vehicle_id)
    except VehicleNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except VehicleOwnershipError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error
