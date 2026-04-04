from src.infrastructure.utils.photo_uploader import FirebasePhotoUploader, IPhotoUploader


def get_photo_uploader() -> IPhotoUploader:
    return FirebasePhotoUploader()
