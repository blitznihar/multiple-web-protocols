from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorDatabase

from .models import WebhookSubscription


class SubscriptionRegistry:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db

    async def list(self) -> List[WebhookSubscription]:
        cursor = self.db.webhook_subscriptions.find({})
        docs = await cursor.to_list(length=10_000)
        return [WebhookSubscription.model_validate(d) for d in docs]

    async def list_active(self) -> List[WebhookSubscription]:
        cursor = self.db.webhook_subscriptions.find({"is_active": True})
        docs = await cursor.to_list(length=10_000)
        return [WebhookSubscription.model_validate(d) for d in docs]

    async def add(
        self,
        *,
        url: str,
        event_types: List[str],
        secret: str,
        player_id: Optional[str] = None,
    ) -> WebhookSubscription:
        sub = WebhookSubscription(
            subscription_id=str(uuid4()),
            url=url,
            event_types=event_types,
            player_id=player_id,
            secret=secret,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        await self.db.webhook_subscriptions.insert_one(sub.model_dump(mode="json"))
        return sub

    async def disable(self, subscription_id: str) -> bool:
        res = await self.db.webhook_subscriptions.update_one(
            {"subscription_id": subscription_id},
            {"$set": {"is_active": False}},
        )
        return res.modified_count == 1
