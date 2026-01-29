from __future__ import annotations

import asyncio
import json
from typing import Optional

from aiokafka import AIOKafkaConsumer
from pydantic import ValidationError
from motor.motor_asyncio import AsyncIOMotorDatabase

from .models import PlayerEvent
from .registry import SubscriptionRegistry
from .rules import derive_webhook_events
from .dispatcher import WebhookDispatcher


BASE_EVENTS_ALLOWED = {
    "player.score.updated",
    "player.level.up",
    "player.achievement.unlocked",
    "player.score.anomaly_detected",
}


class KafkaWebhookConsumer:
    def __init__(
        self, *, db: AsyncIOMotorDatabase, bootstrap: str, topic: str, group_id: str
    ) -> None:
        self.db = db
        self.bootstrap = bootstrap
        self.topic = topic
        self.group_id = group_id

        self.registry = SubscriptionRegistry(db)
        self.dispatcher = WebhookDispatcher(db)

        self._consumer: Optional[AIOKafkaConsumer] = None
        self._task: Optional[asyncio.Task] = None
        self._stopping = asyncio.Event()

    async def start(self) -> None:
        self._consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap,
            group_id=self.group_id,
            enable_auto_commit=True,
            auto_offset_reset="latest",
            value_deserializer=lambda v: v,
        )
        await self._consumer.start()
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._stopping.set()
        if self._task:
            self._task.cancel()
        if self._consumer:
            await self._consumer.stop()

    async def _run(self) -> None:
        assert self._consumer is not None
        async for msg in self._consumer:
            if self._stopping.is_set():
                break

            try:
                raw = json.loads(msg.value.decode("utf-8"))
                base = PlayerEvent.model_validate(raw)
            except (Exception, ValidationError):
                continue

            if base.event_type not in BASE_EVENTS_ALLOWED:
                continue

            derived = derive_webhook_events(base)
            if not derived:
                continue

            subs = await self.registry.list_active()
            for evt in derived:
                for sub in subs:
                    if evt["event_type"] not in sub.event_types:
                        continue
                    if sub.player_id and sub.player_id != evt["player_id"]:
                        continue
                    try:
                        await self.dispatcher.deliver(sub, evt)
                    except Exception:
                        # network retries happen in dispatcher; final failure lands here
                        pass
