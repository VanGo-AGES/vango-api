import io
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app, raise_server_exceptions=False)

# ===========================================================================
# US01 - TK05: upload de foto de perfil
# Arquivo:     src/infrastructure/utils/photo_uploader.py
#              src/domains/uploads/controller.py
# Critérios:   IPhotoUploader define contrato upload(file) -> str
#              S3PhotoUploader implementa a interface
#              POST /uploads/photo aceita imagem e retorna {"url": "..."}
#              Arquivo não-imagem retorna 422
# ===========================================================================


# --- US01-TK05: IPhotoUploader — interface e implementação concreta ---


def test_photo_uploader_interface_defines_upload_method() -> None:
    """IPhotoUploader deve declarar o método upload(file) -> str."""
    from src.infrastructure.utils.photo_uploader import IPhotoUploader

    assert hasattr(IPhotoUploader, "upload")


def test_s3_photo_uploader_implements_interface() -> None:
    """S3PhotoUploader deve ser subclasse de IPhotoUploader."""
    from src.infrastructure.utils.photo_uploader import IPhotoUploader, S3PhotoUploader

    assert issubclass(S3PhotoUploader, IPhotoUploader)


def test_s3_photo_uploader_upload_returns_url() -> None:
    """S3PhotoUploader.upload deve retornar uma URL pública do S3 não-vazia."""
    from src.infrastructure.utils.photo_uploader import S3PhotoUploader

    fake_file = MagicMock()
    fake_file.filename = "foto.jpg"
    fake_file.content_type = "image/jpeg"
    fake_file.file = MagicMock()

    env_vars = {
        "AWS_ACCESS_KEY_ID": "fake-key",
        "AWS_SECRET_ACCESS_KEY": "fake-secret",
        "AWS_REGION": "us-east-1",
        "AWS_S3_BUCKET_NAME": "test-bucket",
    }

    with patch("src.infrastructure.utils.photo_uploader.boto3") as mock_boto, \
         patch.dict("os.environ", env_vars):
        mock_boto.client.return_value = MagicMock()

        uploader = S3PhotoUploader()
        url = uploader.upload(fake_file)

    assert isinstance(url, str)
    assert url.startswith("https://")
    assert "test-bucket" in url
    assert "amazonaws.com" in url


def test_s3_photo_uploader_upload_calls_upload_fileobj() -> None:
    """S3PhotoUploader.upload deve chamar upload_fileobj no cliente S3."""
    from src.infrastructure.utils.photo_uploader import S3PhotoUploader

    fake_file = MagicMock()
    fake_file.filename = "foto.jpg"
    fake_file.content_type = "image/jpeg"
    fake_file.file = MagicMock()

    env_vars = {
        "AWS_ACCESS_KEY_ID": "fake-key",
        "AWS_SECRET_ACCESS_KEY": "fake-secret",
        "AWS_REGION": "us-east-1",
        "AWS_S3_BUCKET_NAME": "test-bucket",
    }

    with patch("src.infrastructure.utils.photo_uploader.boto3") as mock_boto, \
         patch.dict("os.environ", env_vars):
        mock_s3_client = MagicMock()
        mock_boto.client.return_value = mock_s3_client

        uploader = S3PhotoUploader()
        uploader.upload(fake_file)

        mock_s3_client.upload_fileobj.assert_called_once()


def test_s3_photo_uploader_upload_raises_on_s3_error() -> None:
    """S3PhotoUploader.upload deve propagar a exceção quando o S3 falha."""
    from src.infrastructure.utils.photo_uploader import S3PhotoUploader

    fake_file = MagicMock()
    fake_file.filename = "foto.jpg"
    fake_file.content_type = "image/jpeg"
    fake_file.file = MagicMock()

    env_vars = {
        "AWS_ACCESS_KEY_ID": "fake-key",
        "AWS_SECRET_ACCESS_KEY": "fake-secret",
        "AWS_REGION": "us-east-1",
        "AWS_S3_BUCKET_NAME": "test-bucket",
    }

    with patch("src.infrastructure.utils.photo_uploader.boto3") as mock_boto, \
         patch.dict("os.environ", env_vars):
        mock_s3_client = MagicMock()
        mock_s3_client.upload_fileobj.side_effect = Exception("S3 connection error")
        mock_boto.client.return_value = mock_s3_client

        uploader = S3PhotoUploader()

        with pytest.raises(Exception, match="S3 connection error"):
            uploader.upload(fake_file)


# --- US01-TK05: POST /uploads/photo — endpoint ---


def _make_mock_uploader(url: str = "https://test-bucket.s3.us-east-1.amazonaws.com/uploads/foto.jpg") -> MagicMock:
    mock = MagicMock()
    mock.upload.return_value = url
    return mock


def test_upload_photo_returns_201_with_url() -> None:
    """POST /uploads/photo com imagem válida deve retornar 201 e {"url": "..."}."""
    from src.infrastructure.dependencies.upload_dependencies import get_photo_uploader

    app.dependency_overrides[get_photo_uploader] = lambda: _make_mock_uploader()

    try:
        image_bytes = io.BytesIO(b"fake-image-content")
        response = client.post(
            "/uploads/photo",
            files={"file": ("foto.jpg", image_bytes, "image/jpeg")},
        )
    finally:
        app.dependency_overrides.clear()

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
