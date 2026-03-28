from fastapi import APIRouter, HTTPException, UploadFile, status

router = APIRouter(prefix="/uploads", tags=["Uploads"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post(
    "/photo",
    status_code=status.HTTP_201_CREATED,
    summary="Upload de foto de perfil",
    description="Recebe uma imagem, faz o upload para o serviço de armazenamento e retorna a URL pública.",
)
def upload_photo(file: UploadFile) -> dict[str, str]:
    """
    Endpoint para upload de fotos de perfil de usuários.
    A URL retornada deve ser enviada no campo photo_url de UserCreate ou UserUpdate.
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not Implemented")
