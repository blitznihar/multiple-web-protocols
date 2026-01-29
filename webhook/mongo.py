from __future__ import annotations

import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


def get_mongo_client() -> AsyncIOMotorClient:
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    return AsyncIOMotorClient(uri)


def get_db(client: AsyncIOMotorClient) -> AsyncIOMotorDatabase:
    db_name = os.getenv("MONGO_DB_WEBHOOK", "webhookdb")
    return client[db_name]


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    # subscriptions
    await db.webhook_subscriptions.create_index("subscription_id", unique=True)
    await db.webhook_subscriptions.create_index("is_active")
    await db.webhook_subscriptions.create_index("player_id")
    await db.webhook_subscriptions.create_index("event_types")

    # delivery log (optional but useful)
    await db.webhook_deliveries.create_index("delivery_id", unique=True)
    await db.webhook_deliveries.create_index([("subscription_id", 1), ("event_id", 1)])
