from functools import lru_cache

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import get_settings


class StorageService:
    def __init__(self) -> None:
        settings = get_settings()
        self.bucket = settings.minio_bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=f"{'https' if settings.minio_secure else 'http'}://{settings.minio_endpoint}",
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )

    def ensure_bucket(self) -> None:
        try:
            self._client.head_bucket(Bucket=self.bucket)
        except ClientError:
            self._client.create_bucket(Bucket=self.bucket)

    def upload_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        self.ensure_bucket()
        self._client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
        return key

    def get_object(self, key: str) -> tuple[bytes, str]:
        obj = self._client.get_object(Bucket=self.bucket, Key=key)
        content_type = obj.get("ContentType") or "application/octet-stream"
        return obj["Body"].read(), content_type

    def copy_object(self, source_key: str, dest_key: str) -> str:
        self.ensure_bucket()
        self._client.copy_object(
            Bucket=self.bucket,
            CopySource={"Bucket": self.bucket, "Key": source_key},
            Key=dest_key,
        )
        return dest_key

    def object_exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False

    def ping(self) -> bool:
        try:
            self._client.list_buckets()
            return True
        except (BotoCoreError, ClientError, Exception):
            return False


@lru_cache
def get_storage() -> StorageService:
    return StorageService()
