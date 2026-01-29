import asyncio
import json
from datetime import datetime, timezone
from uuid import uuid4

from aiokafka import AIOKafkaProducer


async def main():
    producer = AIOKafkaProducer(bootstrap_servers="localhost:9092")
    await producer.start()
    try:
        score_before = 990

        for _ in range(20):
            evt = {
                "event_id": str(uuid4()),
                "event_type": "player.score.updated",
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "player_id": "12345",
                "data": {
                    "delta": 10,
                    "score_before": score_before,
                    "score_after": score_before + 10,
                    "reason": "match_win",
                    "match_id": "m-7781",
                },
            }

            await producer.send_and_wait(
                "player-events",
                json.dumps(evt).encode("utf-8"),
                key=b"12345",
            )

            score_before += 10
            print("sent:", evt)

    finally:
        await producer.stop()


asyncio.run(main())
