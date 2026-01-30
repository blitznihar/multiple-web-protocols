from __future__ import annotations

import json
from uuid import uuid4
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List

from fastmcp import FastMCP
from motor.motor_asyncio import AsyncIOMotorClient
from aiokafka import AIOKafkaProducer

from .models import Customer, Address
from config.envconfig import EnvConfig
from db.customer_db import CustomerDB

config = EnvConfig()
mongouri = config.database_url
mongodb_name = config.db_name
collection_name = config.collection_name
kafka_bootstrap = config.kafka_bootstrap
kafka_topic = config.kafka_topic

customerdb = CustomerDB(
    uri=mongouri,
    db_name=mongodb_name,
    collection_name=collection_name,
)
mcp = FastMCP(name="multiple-web-protocols MCP")

_mongo_client: Optional[AsyncIOMotorClient] = None
_kafka_producer: Optional[AIOKafkaProducer] = None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _mongo() -> AsyncIOMotorClient:
    global _mongo_client
    if _mongo_client is None:
        uri = mongouri
        _mongo_client = AsyncIOMotorClient(uri)
    return _mongo_client


def _db():
    db_name = mongodb_name
    return _mongo()[db_name]


async def _producer() -> AIOKafkaProducer:
    global _kafka_producer
    if _kafka_producer is None:
        bootstrap = kafka_bootstrap
        _kafka_producer = AIOKafkaProducer(bootstrap_servers=bootstrap)
        await _kafka_producer.start()
    return _kafka_producer


# -------------------------
# Mongo indexes (optional)
# -------------------------
@mcp.tool
async def customer_init_indexes() -> Dict[str, Any]:
    """
    Create Mongo indexes for customers collection.
    """
    await _db().customers.create_index("customerid", unique=True)
    await _db().customers.create_index("email")
    return {"ok": True}


# =========================
# Customer CRUD (Mongo)
# =========================


@mcp.tool
async def customer_create(
    customerid: str,
    firstname: str,
    lastname: str,
    email: str,
    phone: Optional[str] = None,
    street: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    zip: Optional[str] = None,
    country: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a customer with your schema (customerid + nested address).
    """
    address = None
    if any([street, city, state, zip, country]):
        # require all if any is provided
        if not all([street, city, state, zip, country]):
            return {
                "error": "address_incomplete",
                "message": "Provide street, city, state, zip, country",
            }
        address = Address(
            street=street, city=city, state=state, zip=zip, country=country
        )

    customer = Customer(
        customerid=customerid,
        firstname=firstname,
        lastname=lastname,
        email=email,
        phone=phone,
        address=address,
    )

    doc = customer.model_dump(mode="json")
    doc["created_at"] = _utc_now()
    doc["updated_at"] = _utc_now()

    await _db().customers.insert_one(doc)
    doc.pop("_id", None)
    return doc


@mcp.tool
async def customer_get(customer_id: str, customerid: str):
    """
    Get customer by customerid.
    """

    doc = await _db().customers.find_one({"customerid": customer_id}, {"_id": 0})
    if not doc:
        return {"error": "not_found", "customerid": customer_id}
    return doc


@mcp.tool
async def customer_update(
    customerid: str,
    firstname: Optional[str] = None,
    lastname: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    # address fields (optional patch)
    street: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    zip: Optional[str] = None,
    country: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Patch-update fields. Address can be updated partially.
    """
    update: Dict[str, Any] = {}
    if firstname is not None:
        update["firstname"] = firstname
    if lastname is not None:
        update["lastname"] = lastname
    if email is not None:
        update["email"] = email
    if phone is not None:
        update["phone"] = phone

    # Address patch: update nested keys if provided
    address_updates: Dict[str, Any] = {}
    if street is not None:
        address_updates["address.street"] = street
    if city is not None:
        address_updates["address.city"] = city
    if state is not None:
        address_updates["address.state"] = state
    if zip is not None:
        address_updates["address.zip"] = zip
    if country is not None:
        address_updates["address.country"] = country

    update.update(address_updates)
    update["updated_at"] = _utc_now()

    res = await _db().customers.update_one({"customerid": customerid}, {"$set": update})
    if res.matched_count == 0:
        return {"error": "not_found", "customerid": customerid}
    return await customer_get(customerid)


@mcp.tool
async def customer_delete(customerid: str) -> Dict[str, Any]:
    """
    Delete customer by customerid.
    """
    res = await _db().customers.delete_one({"customerid": customerid})
    return {"deleted": res.deleted_count == 1, "customerid": customerid}


@mcp.tool
async def customer_list(limit: int = 50) -> List[Dict[str, Any]]:
    """
    List customers.
    """
    cursor = _db().customers.find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
    return await cursor.to_list(length=limit)


# =========================
# Player events (Kafka)
# =========================


@mcp.tool
async def player_publish_score_updated(
    player_id: str,
    delta: int,
    score_before: int,
    reason: str = "match_win",
    match_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Publish base event player.score.updated to Kafka (topic player-events).
    """
    evt = {
        "event_id": str(uuid4()),
        "event_type": "player.score.updated",
        "occurred_at": _utc_now(),
        "player_id": player_id,
        "data": {
            "delta": delta,
            "score_before": score_before,
            "score_after": score_before + delta,
            "reason": reason,
            "match_id": match_id,
        },
    }

    topic = kafka_topic
    producer = await _producer()
    await producer.send_and_wait(
        topic,
        json.dumps(evt).encode("utf-8"),
        key=player_id.encode("utf-8"),
    )
    return {"published": True, "topic": topic, "event": evt}


@mcp.tool
async def player_publish_event(
    event_type: str,
    player_id: str,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Publish any player.* event to Kafka.
    """
    evt = {
        "event_id": str(uuid4()),
        "event_type": event_type,
        "occurred_at": _utc_now(),
        "player_id": player_id,
        "data": data,
    }

    topic = kafka_topic
    producer = await _producer()
    await producer.send_and_wait(
        topic,
        json.dumps(evt).encode("utf-8"),
        key=player_id.encode("utf-8"),
    )
    return {"published": True, "topic": topic, "event": evt}
