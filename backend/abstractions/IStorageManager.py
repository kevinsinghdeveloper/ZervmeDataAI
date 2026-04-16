from abc import abstractmethod
from typing import Optional


class IStorageManager:
    @abstractmethod
    def upload_file(self, file_path: str, content: bytes, content_type: Optional[str] = None) -> str:
        pass

    @abstractmethod
    def download_file(self, file_path: str) -> bytes:
        pass

    @abstractmethod
    def delete_file(self, file_path: str) -> bool:
        pass

    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        pass
