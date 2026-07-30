from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class EscalationSummary(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    workflow_run_id: int
    category: str
    reason: str
    status: str
    created_at: datetime