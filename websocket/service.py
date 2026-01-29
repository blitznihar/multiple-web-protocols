from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from .kafka_consumer import KafkaEventConsumer
from .ws_manager import WebSocketManager

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "player-events")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "ws-gateway-group")


manager = WebSocketManager()
consumer = KafkaEventConsumer(
    manager=manager,
    bootstrap_servers=KAFKA_BOOTSTRAP,
    topic=KAFKA_TOPIC,
    group_id=KAFKA_GROUP_ID,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await consumer.start()
    try:
        yield
    finally:
        await consumer.stop()


app = FastAPI(title="WS Gateway", lifespan=lifespan)


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})


@app.websocket("/ws")
async def ws_all_events(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            # keep connection alive; optionally handle client messages
            await ws.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(ws)


@app.websocket("/ws/player/{player_id}")
async def ws_player(ws: WebSocket, player_id: str):
    await manager.connect(ws, player_id=player_id)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(ws)
