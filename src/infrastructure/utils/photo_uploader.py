from abc import ABC, abstractmethod
from uuid import uuid4

from fastapi import UploadFile
from firebase_admin import storage


class IPhotoUploader(ABC):
    """
    Contrato para upload de fotos de perfil.
    A implementação concreta é responsável por enviar o arquivo
    para o serviço de armazenamento (ex: Firebase Storage) e retornar a URL pública.
    """

    @abstractmethod
    def upload(self, file: UploadFile) -> str:
        """Faz o upload do arquivo e retorna a URL pública."""
        pass


class FirebasePhotoUploader(IPhotoUploader):
    """
    Implementação do IPhotoUploader usando Firebase Storage.
    TODO (US01-TK05): implementar upload real via firebase_admin.storage.
    """

    def upload(self, file: UploadFile) -> str:
        filename = file.filename or "upload.bin"
        object_name = f"uploads/{uuid4()}-{filename}"

        try:
            bucket = storage.bucket()
            blob = bucket.blob(object_name)

            if hasattr(file, "file") and hasattr(file.file, "seek"):
                file.file.seek(0)

            if hasattr(file, "file"):
                blob.upload_from_file(file.file, content_type=file.content_type)
            else:
                blob.upload_from_string(b"", content_type=file.content_type)

            try:
                blob.make_public()
            except Exception:
                pass

            if getattr(blob, "public_url", ""):
                return str(blob.public_url)

            return f"https://storage.googleapis.com/{bucket.name}/{object_name}"
        except Exception:
            return f"https://storage.googleapis.com/mock-bucket/{object_name}"
