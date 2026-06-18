from datetime import timedelta
from typing import BinaryIO

from minio import Minio

from core.config import settings

minio_client = Minio(
    f"{settings.MINIO_HOST}:{settings.MINIO_PORT}",
    access_key=settings.MINIO_ROOT_USER,
    secret_key=settings.MINIO_ROOT_PASSWORD,
    secure=settings.MINIO_USE_SSL,
)


def upload_file(
    bucket: str,
    object_name: str,
    file_data: BinaryIO,
    length: int,
    content_type: str,
) -> None:
    minio_client.put_object(bucket, object_name, file_data, length, content_type=content_type)


def download_file(bucket: str, object_name: str) -> bytes:
    response = minio_client.get_object(bucket, object_name)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def get_presigned_url(bucket: str, object_name: str, expires_seconds: int = 3600) -> str:
    return minio_client.presigned_get_object(
        bucket, object_name, expires=timedelta(seconds=expires_seconds)
    )


def delete_file(bucket: str, object_name: str) -> None:
    minio_client.remove_object(bucket, object_name)
