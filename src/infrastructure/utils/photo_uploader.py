import os
from abc import ABC, abstractmethod
from uuid import uuid4

import boto3
from fastapi import UploadFile


class IPhotoUploader(ABC):
    """
    Contrato para upload de fotos de perfil.
    A implementação concreta é responsável por enviar o arquivo
    para o serviço de armazenamento e retornar a URL pública.
    """

    @abstractmethod
    def upload(self, file: UploadFile) -> str:
        """Faz o upload do arquivo e retorna a URL pública."""
        pass


class S3PhotoUploader(IPhotoUploader):
    """
    Implementação do IPhotoUploader usando AWS S3.
    """

    def __init__(self):
        # Apenas pega o nome do bucket, sem inicializar o Boto3 ainda
        self.bucket_name = os.getenv("AWS_S3_BUCKET_NAME")

    def upload(self, file: UploadFile) -> str:
        # INICIALIZAÇÃO LAZY: O cliente só é criado quando o upload realmente vai acontecer
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION"),
        )

        # Mantém o padrão de nomenclatura original com UUID para evitar conflitos
        filename = file.filename or "upload.bin"
        object_name = f"uploads/{uuid4()}-{filename}"

        try:
            # Garante que o cursor do arquivo esteja no início antes do upload
            file.file.seek(0)

            # Faz o upload para o S3 definindo permissão de leitura pública
            s3_client.upload_fileobj(
                file.file, self.bucket_name, object_name, ExtraArgs={"ACL": "public-read", "ContentType": file.content_type}
            )

            # Retorna a URL estruturada do S3
            return f"https://{self.bucket_name}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{object_name}"

        except Exception as e:
            # Log de erro para debug no terminal do Docker (EC2)
            print(f"Erro ao fazer upload para o S3: {e}")
            raise e
