from abc import ABC, abstractmethod

from fastapi import UploadFile


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
        pass
