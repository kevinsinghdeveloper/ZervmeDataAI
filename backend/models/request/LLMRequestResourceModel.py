from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class LLMRequestResourceModel:
    system_prompt: str = ""
    prompt: str = ""
    examples: Optional[str] = None
    response_type: Optional[str] = None
    history_messages: Optional[List[dict]] = None
