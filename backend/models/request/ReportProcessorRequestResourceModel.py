from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ReportProcessorRequestResourceModel:
    task_type: str = ""
    report_name: str = ""
    task_params: dict = field(default_factory=dict)
    llm_config: dict = field(default_factory=dict)
