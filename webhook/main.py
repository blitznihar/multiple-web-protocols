from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, AnyHttpUrl

from .mongo import get_mongo_client, get_db, ensure_indexes
from .registry import SubscriptionRegistry
from .kafka_consumer import KafkaWebhookConsumer

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "player-events")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "webhook-dispatcher-group")

mongo_client = get_mongo_client()
db = get_db(mongo_client)

registry = SubscriptionRegistry(db)
consumer = KafkaWebhookConsumer(
    db=db, bootstrap=KAFKA_BOOTSTRAP, topic=KAFKA_TOPIC, group_id=KAFKA_GROUP_ID
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_indexes(db)
    await consumer.start()
    try:
        yield
    finally:
        await consumer.stop()
        mongo_client.close()


app = FastAPI(title="Webhook Service", lifespan=lifespan)


class CreateWebhookRequest(BaseModel):
    url: AnyHttpUrl
    event_types: List[str]
    secret: str
    player_id: Optional[str] = None


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})


@app.get("/webhooks")
async def list_webhooks():
    subs = await registry.list()
    return [s.model_dump(mode="json") for s in subs]


@app.post("/webhooks")
async def create_webhook(req: CreateWebhookRequest):
    sub = await registry.add(
        url=str(req.url),
        event_types=req.event_types,
        secret=req.secret,
        player_id=req.player_id,
    )
    return sub.model_dump(mode="json")


@app.delete("/webhooks/{subscription_id}")
async def disable_webhook(subscription_id: str):
    ok = await registry.disable(subscription_id)
    if not ok:
        raise HTTPException(status_code=404, detail="subscription not found")
    return {"disabled": True, "subscription_id": subscription_id}
