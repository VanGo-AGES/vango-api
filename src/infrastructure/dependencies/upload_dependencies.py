from src.infrastructure.utils.photo_uploader import IPhotoUploader, S3PhotoUploader


def get_photo_uploader() -> IPhotoUploader:
    return S3PhotoUploader()
