from enum import Enum


class JobStatusEnum(Enum):
    START = "start"
    STOP = "stop"
    STATUS = "status"
    COMPLETED = "completed"
    FAILED = "failed"
