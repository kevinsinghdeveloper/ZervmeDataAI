import os
import shutil
from typing import Optional
from abstractions.IStorageManager import IStorageManager

STORAGE_BASE_DIR = os.getenv("STORAGE_BASE_DIR", "uploads")


class LocalStorageService(IStorageManager):
    """Local filesystem storage implementation."""

    def __init__(self, base_dir: Optional[str] = None):
        self._base_dir = base_dir or STORAGE_BASE_DIR
        os.makedirs(self._base_dir, exist_ok=True)

    def _resolve_path(self, file_path: str) -> str:
        """Resolve relative path to absolute path within the storage directory."""
        resolved = os.path.join(self._base_dir, file_path)
        # Prevent directory traversal
        abs_base = os.path.abspath(self._base_dir)
        abs_resolved = os.path.abspath(resolved)
        if not abs_resolved.startswith(abs_base):
            raise ValueError("Invalid file path: directory traversal detected")
        return abs_resolved

    def upload_file(self, file_path: str, content: bytes, content_type: Optional[str] = None) -> str:
        """Save content to a file on the local filesystem.

        Args:
            file_path: Relative path within the storage directory.
            content: File content as bytes.
            content_type: MIME type (ignored for local storage).

        Returns:
            The resolved absolute path of the saved file.
        """
        resolved = self._resolve_path(file_path)
        os.makedirs(os.path.dirname(resolved), exist_ok=True)

        with open(resolved, "wb") as f:
            f.write(content)

        return resolved

    def download_file(self, file_path: str) -> bytes:
        """Read and return the content of a file.

        Args:
            file_path: Relative path within the storage directory.

        Returns:
            File content as bytes.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        resolved = self._resolve_path(file_path)
        if not os.path.exists(resolved):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(resolved, "rb") as f:
            return f.read()

    def delete_file(self, file_path: str) -> bool:
        """Delete a file from local storage.

        Args:
            file_path: Relative path within the storage directory.

        Returns:
            True if the file was deleted, False if it did not exist.
        """
        resolved = self._resolve_path(file_path)
        if os.path.exists(resolved):
            os.remove(resolved)
            return True
        return False

    def file_exists(self, file_path: str) -> bool:
        """Check whether a file exists in local storage.

        Args:
            file_path: Relative path within the storage directory.

        Returns:
            True if the file exists, False otherwise.
        """
        resolved = self._resolve_path(file_path)
        return os.path.exists(resolved)

    def list_files(self, directory: str = "") -> list:
        """List all files within a directory in local storage.

        Args:
            directory: Relative directory path within the storage directory.

        Returns:
            List of relative file paths.
        """
        resolved = self._resolve_path(directory)
        if not os.path.isdir(resolved):
            return []

        files = []
        for root, dirs, filenames in os.walk(resolved):
            for filename in filenames:
                full_path = os.path.join(root, filename)
                relative = os.path.relpath(full_path, self._base_dir)
                files.append(relative)
        return files

    def get_file_size(self, file_path: str) -> int:
        """Get the size of a file in bytes.

        Args:
            file_path: Relative path within the storage directory.

        Returns:
            File size in bytes.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        resolved = self._resolve_path(file_path)
        if not os.path.exists(resolved):
            raise FileNotFoundError(f"File not found: {file_path}")
        return os.path.getsize(resolved)
