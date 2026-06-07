from typing import List, Literal

from pydantic import BaseModel, Field, field_validator


Category = Literal[
    "network_issue",
    "performance_issue",
    "hardware_issue",
    "software_issue",
    "os_error",
    "storage_issue",
    "driver_issue",
    "security_issue",
    "peripheral_issue",
    "unknown_issue",
]

Priority = Literal["low", "medium", "high", "critical"]
RiskLevel = Literal["safe", "warning", "dangerous"]
OperatingSystem = Literal["Windows", "macOS", "Linux", "Unknown"]


class AnalyzeRequest(BaseModel):
    message: str = Field(..., min_length=1)
    os: OperatingSystem
    session_id: str | None = None

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message alanı boş olamaz.")
        return value.strip()


class ITSupportResponse(BaseModel):
    assistant_message: str | None = None
    category: Category
    priority: Priority
    summary: str
    possible_causes: List[str]
    questions: List[str]
    solution_steps: List[str]
    risk_level: RiskLevel
    session_id: str | None = None
    mode: str | None = None
    latency_ms: int | None = None
    model_used: bool | None = None
    repair_used: bool | None = None
    retry_used: bool | None = None
    model_call_count: int | None = None
    model_inference_ms: int | None = None
    advisory_warnings: List[str] | None = None


class ErrorResponse(BaseModel):
    detail: str


class InvalidModelOutputResponse(BaseModel):
    detail: str
    error_type: Literal["invalid_model_json", "invalid_model_semantics"]
    raw_preview: str
    reasons: List[str] = Field(default_factory=list)
