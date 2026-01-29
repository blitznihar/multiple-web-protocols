from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, AnyHttpUrl


class PlayerEvent(BaseModel):
    event_id: str
    event_type: str
    occurred_at: datetime
    player_id: str
    data: Dict[str, Any] = Field(default_factory=dict)


class WebhookSubscription(BaseModel):
    subscription_id: str
    url: AnyHttpUrl
    event_types: List[str]
    player_id: Optional[str] = None
    secret: str
    is_active: bool = True
    created_at: datetime


class WebhookDeliveryLog(BaseModel):
    delivery_id: str
    subscription_id: str
    url: AnyHttpUrl
    event_id: str
    event_type: str
    player_id: str
    status_code: Optional[int] = None
    error: Optional[str] = None
    attempted_at: datetime
