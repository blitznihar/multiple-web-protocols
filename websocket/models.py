from __future__ import annotations

from datetime import datetime
from typing import Any, Dict
from pydantic import BaseModel, Field


class PlayerEvent(BaseModel):
    event_id: str
    event_type: str
    occurred_at: datetime
    player_id: str
    data: Dict[str, Any] = Field(default_factory=dict)
    # Optional fields if you add them later:
    # trace_id: Optional[str] = None
