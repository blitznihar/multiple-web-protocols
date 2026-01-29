from __future__ import annotations
from typing import Any, Dict, List

from .models import PlayerEvent

LEVEL_UP_SCORE = 1000
ANOMALY_DELTA_THRESHOLD = 500
ANOMALY_WINDOW_SECONDS = 10


def derive_webhook_events(base: PlayerEvent) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []

    if base.event_type != "player.score.updated":
        return out

    delta = int(base.data.get("delta", 0))
    before = int(base.data.get("score_before", 0))
    after = int(base.data.get("score_after", 0))

    if before < LEVEL_UP_SCORE <= after:
        out.append(
            {
                "event_id": base.event_id,
                "event_type": "player.level.up",
                "occurred_at": base.occurred_at.isoformat(),
                "player_id": base.player_id,
                "data": {
                    "old_level": base.data.get("level_before"),
                    "new_level": base.data.get("level_after"),
                    "score": after,
                },
            }
        )

    if after >= 5000 and before < 5000:
        out.append(
            {
                "event_id": base.event_id,
                "event_type": "player.achievement.unlocked",
                "occurred_at": base.occurred_at.isoformat(),
                "player_id": base.player_id,
                "data": {"achievement": "Silver", "score": after},
            }
        )

    if abs(delta) >= ANOMALY_DELTA_THRESHOLD:
        out.append(
            {
                "event_id": base.event_id,
                "event_type": "player.score.anomaly_detected",
                "occurred_at": base.occurred_at.isoformat(),
                "player_id": base.player_id,
                "data": {"delta": delta, "window_seconds": ANOMALY_WINDOW_SECONDS},
            }
        )

    return out
