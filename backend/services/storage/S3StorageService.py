"""S3-backed storage implementation of IStorageManager."""
import os
import boto3
from botocore.exceptions import ClientError
from typing import Optional, List
from abstractions.IStorageManager import IStorageManager
from abstractions.IServiceManagerBase import IServiceManagerBase


class S3StorageService(IStorageManager, IServiceManagerBase):
    """S3 storage service implementing IStorageManager interface."""

    def __init__(self, config: dict = None):
        self._bucket = (config or {}).get("bucket_name", os.getenv("UPLOADS_BUCKET", ""))
        self._region = (config or {}).get("region", os.getenv("AWS_REGION_NAME", "us-east-1"))
        self._s3 = None

    def initialize(self):
        """Initialize S3 client."""
        self._s3 = boto3.client("s3", region_name=self._region)
        return self

    def _get_client(self):
        if not self._s3:
            self.initialize()
        return self._s3

    def upload_file(self, file_path: str, content: bytes, content_type: Optional[str] = None) -> str:
        """Upload file to S3. Returns the S3 key."""
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
        self._get_client().put_object(
            Bucket=self._bucket,
            Key=file_path,
            Body=content,
            **extra_args
        )
        return file_path

    def download_file(self, file_path: str) -> bytes:
        """Download file from S3. Returns file content as bytes."""
        response = self._get_client().get_object(Bucket=self._bucket, Key=file_path)
        return response["Body"].read()

    def delete_file(self, file_path: str) -> bool:
        """Delete file from S3."""
        try:
            self._get_client().delete_object(Bucket=self._bucket, Key=file_path)
            return True
        except ClientError:
            return False

    def file_exists(self, file_path: str) -> bool:
        """Check if file exists in S3."""
        try:
            self._get_client().head_object(Bucket=self._bucket, Key=file_path)
            return True
        except ClientError:
            return False

    def list_files(self, prefix: str = "") -> List[str]:
        """List files in S3 under the given prefix."""
        response = self._get_client().list_objects_v2(
            Bucket=self._bucket,
            Prefix=prefix
        )
        return [obj["Key"] for obj in response.get("Contents", [])]

    def get_file_size(self, file_path: str) -> int:
        """Get file size in S3."""
        response = self._get_client().head_object(Bucket=self._bucket, Key=file_path)
        return response["ContentLength"]
