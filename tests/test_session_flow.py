import asyncio
import pytest


async def test_honest_session_awards_xp(client, auth_headers):
    start = await client.post("/session/start", json={"skill_id": 1}, headers=auth_headers)
    session_id = start.json()["session_id"]

    await asyncio.sleep(3)

    hb = await client.post(f"/session/heartbeat/{session_id}", headers=auth_headers)
    assert hb.json()["accepted"] is True

    end = await client.post(
        "/session/end",
        json={"session_id": session_id, "skill_id": 1, "claimed_seconds": 3},
        headers=auth_headers,
    )
    body = end.json()
    assert body["verification_status"] == "verified"
    assert body["xp_gained"] > 0


async def test_farming_attempt_gets_zero_xp(client, auth_headers):
    start = await client.post("/session/start", json={"skill_id": 1}, headers=auth_headers)
    session_id = start.json()["session_id"]

    # wait past the 45s heartbeat TTL with no heartbeat sent -- key expires in Redis
    await asyncio.sleep(46)

    end = await client.post(
        "/session/end",
        json={"session_id": session_id, "skill_id": 1, "claimed_seconds": 600},
        headers=auth_headers,
    )
    body = end.json()
    assert body["xp_awarded"] == 0


async def test_unauthenticated_request_rejected(client):
    resp = await client.post("/session/start", json={"skill_id": 1})
    assert resp.status_code == 401


async def test_wrong_password_rejected(client):
    resp = await client.post("/auth/login", data={"username": "nonexistent_user", "password": "wrong"})
    assert resp.status_code == 401
