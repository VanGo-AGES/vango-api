import io

import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app, raise_server_exceptions=False)

# ===========================================================================
# US01 - TK05: upload de foto de perfil
# Arquivo:     src/infrastructure/utils/photo_uploader.py
#              src/domains/uploads/controller.py
# Critérios:   IPhotoUploader define contrato upload(file) -> str
#              FirebasePhotoUploader implementa a interface
#              POST /uploads/photo aceita imagem e retorna {"url": "..."}
#              Arquivo não-imagem retorna 422
# ===========================================================================


# --- US01-TK05: IPhotoUploader — interface e implementação concreta ---


def test_photo_uploader_interface_defines_upload_method() -> None:
    """IPhotoUploader deve declarar o método upload(file) -> str."""
    from src.infrastructure.utils.photo_uploader import IPhotoUploader

    assert hasattr(IPhotoUploader, "upload")


def test_firebase_photo_uploader_implements_interface() -> None:
    """FirebasePhotoUploader deve ser subclasse de IPhotoUploader."""
    from src.infrastructure.utils.photo_uploader import FirebasePhotoUploader, IPhotoUploader

    assert issubclass(FirebasePhotoUploader, IPhotoUploader)


def test_firebase_photo_uploader_upload_returns_url() -> None:
    """FirebasePhotoUploader.upload deve retornar uma URL pública não-vazia."""
    from unittest.mock import MagicMock

    from src.infrastructure.utils.photo_uploader import FirebasePhotoUploader

    fake_file = MagicMock()
    fake_file.filename = "foto.jpg"
    fake_file.content_type = "image/jpeg"

    uploader = FirebasePhotoUploader()
    url = uploader.upload(fake_file)

    assert isinstance(url, str)
    assert url.startswith("https://")


# --- US01-TK05: POST /uploads/photo — endpoint ---


def test_upload_photo_returns_201_with_url() -> None:
    """POST /uploads/photo com imagem válida deve retornar 201 e {"url": "..."}."""
    image_bytes = io.BytesIO(b"fake-image-content")
    response = client.post(
        "/uploads/photo",
        files={"file": ("foto.jpg", image_bytes, "image/jpeg")},
    )

    assert response.status_code == 201
    body = response.json()
    assert "url" in body
    assert body["url"].startswith("https://")


def test_upload_photo_invalid_content_type_returns_422() -> None:
    """POST /uploads/photo com arquivo não-imagem deve retornar 422."""
    pdf_bytes = io.BytesIO(b"%PDF-fake")
    response = client.post(
        "/uploads/photo",
        files={"file": ("doc.pdf", pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 422


def test_upload_photo_missing_file_returns_422() -> None:
    """POST /uploads/photo sem campo file deve retornar 422."""
    response = client.post("/uploads/photo")

    assert response.status_code == 422
