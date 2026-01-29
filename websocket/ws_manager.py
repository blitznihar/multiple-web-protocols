from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import DefaultDict, Set, Optional

from fastapi import WebSocket


class WebSocketManager:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._all_clients: Set[WebSocket] = set()
        self._by_player: DefaultDict[str, Set[WebSocket]] = defaultdict(set)

    async def connect(self, ws: WebSocket, player_id: Optional[str] = None) -> None:
        await ws.accept()
        async with self._lock:
            self._all_clients.add(ws)
            if player_id:
                self._by_player[player_id].add(ws)

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._all_clients.discard(ws)
            for _, group in list(self._by_player.items()):
                group.discard(ws)

    async def broadcast_all(self, message: dict) -> None:
        # Snapshot connections so we don't hold the lock while sending
        async with self._lock:
            clients = list(self._all_clients)
        await self._safe_send_many(clients, message)

    async def broadcast_player(self, player_id: str, message: dict) -> None:
        async with self._lock:
            clients = list(self._by_player.get(player_id, set()))
        await self._safe_send_many(clients, message)

    async def _safe_send_many(self, clients: list[WebSocket], message: dict) -> None:
        for ws in clients:
            try:
                await ws.send_json(message)
            except Exception:
                # client likely disconnected; ignore here
                pass
