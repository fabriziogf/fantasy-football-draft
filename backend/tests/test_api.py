"""API flow tests via FastAPI TestClient. Uses the real board (built/cached)."""
import pytest
from fastapi.testclient import TestClient

from backend.api import app as app_module
from backend.api.draft_state import DraftState


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Isolate persisted state to a temp file per test.
    import backend.api.draft_state as ds

    monkeypatch.setattr(ds, "_STATE_PATH", tmp_path / "state.json")
    app_module._state = None
    with TestClient(app_module.app) as c:
        yield c


def test_health_and_board(client):
    assert client.get("/health").json()["board_players"] > 100
    board = client.get("/board", params={"limit": 5}).json()
    assert len(board) == 5 and "key" in board[0]


def test_recommend_requires_setup(client):
    assert client.get("/recommend").status_code == 409


def test_full_draft_flow(client):
    top = client.get("/board", params={"limit": 3}).json()
    keys = [p["key"] for p in top]

    r = client.post("/setup", json={"my_slot": 1, "num_teams": 12}).json()
    assert r["my_slot"] == 1 and r["is_my_pick"] is True  # slot 1 on the clock

    # Draft my pick #1.
    r = client.post("/pick", json={"key": keys[0]}).json()
    assert r["picks_made"] == 1
    assert r["my_roster"][0]["key"] == keys[0]

    # Unknown key -> 404; duplicate -> 409.
    assert client.post("/pick", json={"key": "nobody|WR"}).status_code == 404
    assert client.post("/pick", json={"key": keys[0]}).status_code == 409

    # Recommendations available and ranked.
    rec = client.get("/recommend", params={"limit": 5}).json()
    assert len(rec["recommendations"]) == 5
    scores = [x["score"] for x in rec["recommendations"]]
    assert scores == sorted(scores, reverse=True)

    # Undo returns to empty roster.
    r = client.post("/undo").json()
    assert r["picks_made"] == 0


def test_state_persists_across_restart(client, tmp_path):
    client.post("/setup", json={"my_slot": 4})
    top_key = client.get("/board", params={"limit": 1}).json()[0]["key"]
    client.post("/pick", json={"key": top_key})

    # Simulate a restart: drop in-memory state, reload from disk.
    app_module._state = None
    reloaded = DraftState.load()
    assert reloaded is not None and reloaded.my_slot == 4
    assert reloaded.picked == [top_key]
