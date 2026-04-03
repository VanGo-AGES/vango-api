from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from src.infrastructure.dependencies.upload_dependencies import get_photo_uploader
from src.infrastructure.utils.photo_uploader import IPhotoUploader

router = APIRouter(prefix="/uploads", tags=["Uploads"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post(
    "/photo",
    status_code=status.HTTP_201_CREATED,
    summary="Upload de foto de perfil",
    description="Recebe uma imagem, faz o upload para o serviço de armazenamento e retorna a URL pública.",
)
def upload_photo(
    file: UploadFile,
    uploader: Annotated[IPhotoUploader, Depends(get_photo_uploader)],
) -> dict[str, str]:
    """
    Endpoint para upload de fotos de perfil de usuários.
    A URL retornada deve ser enviada no campo photo_url de UserCreate ou UserUpdate.
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid image content type")

    return {"url": uploader.upload(file)}
