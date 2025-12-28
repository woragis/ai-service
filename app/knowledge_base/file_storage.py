"""
File storage abstraction for knowledge base documents.

Supports multiple storage providers: local filesystem, S3, Azure Blob, GCS, and custom plugins.
"""

import os
from abc import ABC, abstractmethod
from typing import List, Optional
from pathlib import Path
from app.logger import get_logger

logger = get_logger()

# Global file storage instance
_file_storage: Optional["FileStorageProvider"] = None


class FileStorageProvider(ABC):
    """Abstract base class for file storage providers."""
    
    @abstractmethod
    def read_file(self, path: str) -> Optional[str]:
        """
        Read file content.
        
        Args:
            path: File path
        
        Returns:
            File content as string, or None if not found
        """
        pass
    
    @abstractmethod
    def list_files(self, path: str, pattern: str = "*.md") -> List[str]:
        """
        List files matching pattern.
        
        Args:
            path: Directory path
            pattern: File pattern (e.g., "*.md")
        
        Returns:
            List of file paths
        """
        pass
    
    @abstractmethod
    def file_exists(self, path: str) -> bool:
        """
        Check if file exists.
        
        Args:
            path: File path
        
        Returns:
            True if file exists
        """
        pass


class LocalFileStorage(FileStorageProvider):
    """Local filesystem storage provider."""
    
    def __init__(self, base_path: str = "/app/knowledge"):
        self.base_path = Path(base_path)
        self.logger = get_logger()
        self.logger.info("Local file storage initialized", base_path=str(self.base_path))
    
    def read_file(self, path: str) -> Optional[str]:
        """Read file from local filesystem."""
        try:
            file_path = self.base_path / path.lstrip("/")
            if not file_path.exists():
                return None
            
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            self.logger.error("Failed to read file", error=str(e), path=path)
            return None
    
    def list_files(self, path: str, pattern: str = "*.md") -> List[str]:
        """List files matching pattern."""
        try:
            dir_path = self.base_path / path.lstrip("/")
            if not dir_path.exists():
                return []
            
            files = []
            for file_path in dir_path.rglob(pattern):
                relative_path = file_path.relative_to(self.base_path)
                files.append(str(relative_path))
            
            return files
        except Exception as e:
            self.logger.error("Failed to list files", error=str(e), path=path)
            return []
    
    def file_exists(self, path: str) -> bool:
        """Check if file exists."""
        try:
            file_path = self.base_path / path.lstrip("/")
            return file_path.exists()
        except Exception:
            return False


class S3FileStorage(FileStorageProvider):
    """S3-compatible storage provider."""
    
    def __init__(self, bucket: str, endpoint: Optional[str] = None, access_key: Optional[str] = None, secret_key: Optional[str] = None):
        try:
            import boto3
        except ImportError:
            raise ImportError("boto3 not installed. Install with: pip install boto3")
        
        self.bucket = bucket
        self.logger = get_logger()
        
        # Initialize S3 client
        s3_config = {}
        if endpoint:
            s3_config["endpoint_url"] = endpoint
        if access_key and secret_key:
            s3_config["aws_access_key_id"] = access_key
            s3_config["aws_secret_access_key"] = secret_key
        
        self.s3_client = boto3.client("s3", **s3_config)
        self.logger.info("S3 file storage initialized", bucket=bucket)
    
    def read_file(self, path: str) -> Optional[str]:
        """Read file from S3."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=path)
            return response["Body"].read().decode("utf-8")
        except Exception as e:
            self.logger.error("Failed to read file from S3", error=str(e), path=path)
            return None
    
    def list_files(self, path: str, pattern: str = "*.md") -> List[str]:
        """List files matching pattern in S3."""
        try:
            # S3 list_objects_v2
            response = self.s3_client.list_objects_v2(Bucket=self.bucket, Prefix=path)
            files = []
            
            if "Contents" in response:
                for obj in response["Contents"]:
                    key = obj["Key"]
                    if pattern == "*.md" and key.endswith(".md"):
                        files.append(key)
                    elif pattern == "*" or key.endswith(pattern.lstrip("*")):
                        files.append(key)
            
            return files
        except Exception as e:
            self.logger.error("Failed to list files from S3", error=str(e), path=path)
            return []
    
    def file_exists(self, path: str) -> bool:
        """Check if file exists in S3."""
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=path)
            return True
        except Exception:
            return False


def get_file_storage() -> FileStorageProvider:
    """Get or create file storage provider instance."""
    global _file_storage
    
    if _file_storage is not None:
        return _file_storage
    
    storage_type = os.getenv("FILE_STORAGE_TYPE", "local").lower()
    base_path = os.getenv("FILE_STORAGE_BASE_PATH", "/app/knowledge")
    
    if storage_type == "local":
        _file_storage = LocalFileStorage(base_path=base_path)
    elif storage_type == "s3":
        bucket = os.getenv("FILE_STORAGE_BUCKET", "")
        endpoint = os.getenv("FILE_STORAGE_ENDPOINT")
        access_key = os.getenv("FILE_STORAGE_ACCESS_KEY")
        secret_key = os.getenv("FILE_STORAGE_SECRET_KEY")
        _file_storage = S3FileStorage(bucket=bucket, endpoint=endpoint, access_key=access_key, secret_key=secret_key)
    else:
        # Try to load custom plugin
        plugin_path = os.getenv("FILE_STORAGE_PLUGIN_PATH", "/app/plugins")
        _file_storage = _load_custom_storage(storage_type, plugin_path, base_path)
    
    return _file_storage


def _load_custom_storage(provider_name: str, plugin_path: str, *args, **kwargs) -> FileStorageProvider:
    """Load custom file storage provider from plugin."""
    import importlib.util
    import sys
    
    plugin_file = f"{plugin_path}/file_storage_{provider_name}.py"
    
    if not os.path.exists(plugin_file):
        logger.warn("Custom file storage plugin not found, falling back to local", plugin=plugin_file)
        return LocalFileStorage()
    
    try:
        spec = importlib.util.spec_from_file_location(f"file_storage_{provider_name}", plugin_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"file_storage_{provider_name}"] = module
        spec.loader.exec_module(module)
        
        # Expect a class named {ProviderName}FileStorage
        storage_class = getattr(module, f"{provider_name.capitalize()}FileStorage")
        return storage_class(*args, **kwargs)
    except Exception as e:
        logger.error("Failed to load custom file storage provider", error=str(e), plugin=plugin_file)
        return LocalFileStorage()  # Fallback

