"""
Cloudflare R2 Storage Service
S3-compatible object storage with zero egress costs
"""
import os
import uuid
from datetime import datetime
from typing import Optional, BinaryIO
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


class StorageService:
    """Service for managing file uploads to Cloudflare R2"""
    
    def __init__(self):
        self.account_id = os.getenv("R2_ACCOUNT_ID")
        self.access_key = os.getenv("R2_ACCESS_KEY_ID")
        self.secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
        self.bucket_name = os.getenv("R2_BUCKET_NAME", "crm-files")
        self.public_url = os.getenv("R2_PUBLIC_URL", "")  # e.g., https://files.yourdomain.com
        
        self._client = None
    
    @property
    def client(self):
        """Lazy initialization of S3 client"""
        if self._client is None:
            if not all([self.account_id, self.access_key, self.secret_key]):
                raise ValueError(
                    "Missing R2 configuration. Required env vars: "
                    "R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY"
                )
            
            self._client = boto3.client(
                's3',
                endpoint_url=f'https://{self.account_id}.r2.cloudflarestorage.com',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                config=Config(signature_version='s3v4'),
                region_name='auto'
            )
        return self._client
    
    def _generate_key(self, folder: str, filename: str) -> str:
        """Generate unique file key with folder structure"""
        # Clean filename - keep extension
        ext = filename.rsplit('.', 1)[-1] if '.' in filename else ''
        unique_id = uuid.uuid4().hex[:12]
        timestamp = datetime.now().strftime('%Y%m%d')
        safe_name = f"{timestamp}_{unique_id}"
        if ext:
            safe_name += f".{ext}"
        return f"{folder}/{safe_name}"
    
    async def upload_file(
        self,
        file_data: BinaryIO,
        filename: str,
        folder: str = "general",
        content_type: Optional[str] = None
    ) -> dict:
        """
        Upload a file to R2
        
        Args:
            file_data: File-like object to upload
            filename: Original filename (used for extension)
            folder: Folder path in bucket (e.g., "leads/123", "students/456")
            content_type: MIME type (auto-detected if not provided)
        
        Returns:
            dict with 'key', 'url', 'size'
        """
        key = self._generate_key(folder, filename)
        
        # Auto-detect content type if not provided
        if not content_type:
            content_type = self._guess_content_type(filename)
        
        # Get file size
        file_data.seek(0, 2)  # Seek to end
        size = file_data.tell()
        file_data.seek(0)  # Reset to beginning
        
        # Upload to R2
        extra_args = {'ContentType': content_type} if content_type else {}
        
        self.client.upload_fileobj(
            file_data,
            self.bucket_name,
            key,
            ExtraArgs=extra_args
        )
        
        # Build public URL
        url = f"{self.public_url}/{key}" if self.public_url else None
        
        return {
            'key': key,
            'url': url,
            'size': size,
            'content_type': content_type
        }
    
    async def delete_file(self, key: str) -> bool:
        """
        Delete a file from R2
        
        Args:
            key: The object key in the bucket
            
        Returns:
            True if deleted successfully
        """
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False
    
    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """
        Generate a presigned URL for private file access
        
        Args:
            key: The object key
            expires_in: URL expiration time in seconds (default 1 hour)
            
        Returns:
            Presigned URL string
        """
        return self.client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket_name, 'Key': key},
            ExpiresIn=expires_in
        )
    
    async def file_exists(self, key: str) -> bool:
        """Check if a file exists in the bucket"""
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False
    
    def _guess_content_type(self, filename: str) -> str:
        """Guess content type from filename extension"""
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        
        content_types = {
            # Images
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'svg': 'image/svg+xml',
            # Documents
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xls': 'application/vnd.ms-excel',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'ppt': 'application/vnd.ms-powerpoint',
            'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            # Text
            'txt': 'text/plain',
            'csv': 'text/csv',
            'json': 'application/json',
            'xml': 'application/xml',
            # Archives
            'zip': 'application/zip',
            'rar': 'application/vnd.rar',
        }
        
        return content_types.get(ext, 'application/octet-stream')


# Singleton instance
storage_service = StorageService()
