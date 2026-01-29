from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from uuid import uuid4

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from motor.motor_asyncio import AsyncIOMotorDatabase

from .models import WebhookSubscription, WebhookDeliveryLog


def sign(secret: str, payload: dict) -> str:
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


class WebhookDispatcher:
    def __init__(self, db: AsyncIOMotorDatabase, timeout_seconds: float = 5.0) -> None:
        self.db = db
        self.timeout = timeout_seconds

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
        reraise=True,
    )
    async def _post(self, url: str, headers: dict, payload: dict) -> httpx.Response:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.post(url, json=payload, headers=headers)

    async def deliver(self, sub: WebhookSubscription, payload: dict) -> None:
        delivery_id = str(uuid4())
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "multiple-web-protocols/webhook",
            "X-Webhook-Id": sub.subscription_id,
            "X-Delivery-Id": delivery_id,
            "X-Event-Id": str(payload.get("event_id", "")),
            "X-Event-Type": str(payload.get("event_type", "")),
            "X-Signature": sign(sub.secret, payload),
        }

        log = WebhookDeliveryLog(
            delivery_id=delivery_id,
            subscription_id=sub.subscription_id,
            url=sub.url,
            event_id=str(payload.get("event_id", "")),
            event_type=str(payload.get("event_type", "")),
            player_id=str(payload.get("player_id", "")),
            attempted_at=datetime.now(timezone.utc),
        )

        try:
            resp = await self._post(str(sub.url), headers, payload)
            log.status_code = resp.status_code
            # Optional: treat 429/5xx as “error” and trigger manual retry logic later
        except Exception as e:
            log.error = repr(e)
            raise
        finally:
            await self.db.webhook_deliveries.insert_one(log.model_dump(mode="json"))
