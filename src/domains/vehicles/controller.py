from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.domains.users.entity import UserModel
from src.infrastructure.auth.dependencies import get_current_user
from src.infrastructure.dependencies.vehicle_dependencies import get_vehicle_service

from .dtos import VehicleCreate, VehicleResponse, VehicleUpdate
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
    current_user: Annotated[UserModel, Depends(get_current_user)],
) -> VehicleResponse:
    return service.add_vehicle(
        user_id=str(current_user.id),
        user_role=current_user.role,
        data=body,
    )


@router.get(
    "/",
    response_model=list[VehicleResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar veículos do usuário",
    description="Retorna todos os veículos cadastrados pelo motorista logado.",
)
def list_vehicles(
    service: Annotated[VehicleService, Depends(get_vehicle_service)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
) -> list[VehicleResponse]:
    return service.get_vehicles(str(current_user.id))


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
    current_user: Annotated[UserModel, Depends(get_current_user)],
) -> VehicleResponse:
    return service.get_vehicle(str(current_user.id), vehicle_id)


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
    current_user: Annotated[UserModel, Depends(get_current_user)],
) -> VehicleResponse:
    return service.update_vehicle(str(current_user.id), vehicle_id, body)


@router.delete(
    "/{vehicle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir veículo",
    description="Remove um veículo do perfil do motorista logado.",
)
def delete_vehicle(
    vehicle_id: UUID,
    service: Annotated[VehicleService, Depends(get_vehicle_service)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
) -> None:
    service.delete_vehicle(str(current_user.id), vehicle_id)
