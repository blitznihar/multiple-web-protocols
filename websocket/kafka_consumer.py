from __future__ import annotations

import asyncio
import json
from typing import Optional

from aiokafka import AIOKafkaConsumer
from pydantic import ValidationError

from .models import PlayerEvent
from .ws_manager import WebSocketManager


REALTIME_EVENT_TYPES = {
    "player.score.updated",
    # optionally:
    "player.rank.changed",
    "player.level.up",
}


class KafkaEventConsumer:
    def __init__(
        self,
        *,
        manager: WebSocketManager,
        bootstrap_servers: str,
        topic: str,
        group_id: str,
    ) -> None:
        self.manager = manager
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._task: Optional[asyncio.Task] = None
        self._stopping = asyncio.Event()

    async def start(self) -> None:
        self._consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            enable_auto_commit=True,
            auto_offset_reset="latest",
            value_deserializer=lambda v: v,  # we’ll decode ourselves
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
                payload = json.loads(msg.value.decode("utf-8"))
            except Exception:
                continue

            try:
                evt = PlayerEvent.model_validate(payload)
            except ValidationError:
                continue

            if evt.event_type not in REALTIME_EVENT_TYPES:
                # Webhook dispatcher will handle “derived events” later
                continue

            out = evt.model_dump(mode="json")

            # If you want per-player channeling, do this:
            await self.manager.broadcast_player(evt.player_id, out)

            # If you also want “global feed” clients:
            await self.manager.broadcast_all(out)
