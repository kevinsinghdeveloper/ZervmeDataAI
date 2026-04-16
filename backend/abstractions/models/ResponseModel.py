from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ResponseModel:
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    error: Optional[str] = None
    status_code: int = 200

    def to_dict(self):
        return {
            "success": self.success,
            "data": self.data,
            "message": self.message,
            "error": self.error
        }
