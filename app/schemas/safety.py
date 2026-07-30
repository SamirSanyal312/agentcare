from typing import Literal

from pydantic import BaseModel
from pydantic import Field

from app.schemas.workflow import WorkflowRunResponse


SafetyClassification = Literal[
    "administrative_allowed",
    "medical_advice",
    "emergency",
    "sensitive",
    "uncertain",
]


class SafetyDecision(BaseModel):
    classification: SafetyClassification

    allow_automation: bool

    requires_human_review: bool

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    reason: str = Field(
        min_length=1,
        max_length=500,
    )

    flags: list[str] = Field(
        default_factory=list,
    )

    source: Literal[
        "deterministic",
        "llm",
    ]


class SafetyExecutionResponse(BaseModel):
    decision: SafetyDecision
    workflow: WorkflowRunResponse
    escalation_id: int | None = None