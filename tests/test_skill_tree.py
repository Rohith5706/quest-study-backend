import pytest



async def test_subtree_root_returns_all_descendants(client, auth_headers):
    resp = await client.get("/skills/tree/1", headers=auth_headers)
    body = resp.json()
    assert body["root_id"] == 1
    assert len(body["nodes"]) >= 1


async def test_subtree_leaf_scopes_correctly(client, auth_headers):
    resp = await client.get("/skills/tree/2", headers=auth_headers)
    body = resp.json()
    # Algebra's subtree should not include Geometry (skill_id 3)
    returned_ids = {n["skill_id"] for n in body["nodes"]}
    assert 3 not in returned_ids
