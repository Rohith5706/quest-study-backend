import time
import uuid
from app.core.redis_client import redis_client

HEARTBEAT_TTL_SECONDS = 45    # session key dies if no ping arrives within this window
HEARTBEAT_INTERVAL_SECONDS = 30 # expected client ping cadence


async def start_session(user_id: int, skill_id: int) -> str:
    session_id = str(uuid.uuid4())
    key = f"session:{session_id}"
    now = time.time()

    await redis_client.hset(key, mapping={
        "user_id": user_id,
        "skill_id": skill_id,
        "start_ts": now,
        "last_ping": now,
        "ping_count": 1,
    })
    await redis_client.expire(key, HEARTBEAT_TTL_SECONDS)
    return session_id


async def record_heartbeat(session_id: str) -> bool:
    key = f"session:{session_id}"
    exists = await redis_client.exists(key)
    if not exists:
        # key already expired -- there's a real gap, can't be faked retroactively
        return False

    now = time.time()
    await redis_client.hset(key, mapping={"last_ping": now})
    await redis_client.hincrby(key, "ping_count", 1)
    await redis_client.expire(key, HEARTBEAT_TTL_SECONDS)
    return True


async def end_session(session_id: str, claimed_seconds: int) -> dict:
    key = f"session:{session_id}"
    data = await redis_client.hgetall(key)

    if not data:
        return {"verified_seconds": 0, "ping_count": 0, "status": "rejected"}

    start_ts = float(data["start_ts"])
    last_ping = float(data["last_ping"])
    ping_count = int(data["ping_count"])
    verified_seconds = int(last_ping - start_ts)

    expected_pings = max(1, verified_seconds // HEARTBEAT_INTERVAL_SECONDS)
    ping_ratio = ping_count / expected_pings if expected_pings else 0

    if ping_ratio < 0.5:
        status = "flagged"
    elif abs(claimed_seconds - verified_seconds) > 60:
        status = "flagged"
    else:
        status = "verified"

    await redis_client.delete(key)
    return {"verified_seconds": verified_seconds, "ping_count": ping_count, "status": status}