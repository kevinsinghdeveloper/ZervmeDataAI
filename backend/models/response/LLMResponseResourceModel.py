from dataclasses import dataclass
from typing import Optional, Union


@dataclass
class LLMResponseResourceModel:
    response_content: Optional[Union[str, dict]] = None
    history_messages: Optional[list] = None
    usage_data: Optional[dict] = None
