"""Tests for the manual rain delay override (POST/GET/DELETE /system/rain-delay)."""
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

import database
import main


# ---------------------------------------------------------------------------
# Per-test DB cleanup so zone/schedule/settings rows don't collide between
# tests (all test modules share one on-disk DB for the session — see conftest).
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_db(client):
    with database.get_db() as con:
        con.execute("DELETE FROM active_runs")
        con.execute("DELETE FROM schedules")
        con.execute("DELETE FROM zones")
        con.execute("DELETE FROM counters")
        con.execute("DELETE FROM app_settings")


def _create_zone(client, name, port, duration=1):
    r = client.post("/zones", json={
        "name": name, "port": port, "duration": duration,
        "icon": "mdi-sprinkler", "color": "#4CAF50",
    })
    assert r.status_code == 201, r.json()
    return r.json()["id"]


def _create_schedule(client, zone_ids):
    r = client.post("/schedules", json={
        "name": "Test Schedule",
        "days": ["Monday"],
        "startTimes": ["07:00"],
        "zoneIds": zone_ids,
        "enabled": True,
    })
    assert r.status_code == 201, r.json()
    return r.json()["id"]


def test_rain_delay_unset_by_default(client):
    r = client.get("/system/rain-delay")
    assert r.status_code == 200
    assert r.json() == {"rain_delay_until": None}


def test_system_status_includes_rain_delay_field(client):
    r = client.get("/system/status")
    assert r.status_code == 200
    assert "rain_delay_until" in r.json()
    assert r.json()["rain_delay_until"] is None


def test_set_rain_delay_returns_future_timestamp(client):
    before = datetime.now(timezone.utc)
    r = client.post("/system/rain-delay", json={"hours": 24})
    assert r.status_code == 200

    until = datetime.fromisoformat(r.json()["rain_delay_until"])
    assert until > before + timedelta(hours=23)
    assert until < before + timedelta(hours=25)

    status_resp = client.get("/system/status")
    assert status_resp.json()["rain_delay_until"] == r.json()["rain_delay_until"]


def test_set_rain_delay_rejects_out_of_range_hours(client):
    assert client.post("/system/rain-delay", json={"hours": 0}).status_code == 422
    assert client.post("/system/rain-delay", json={"hours": 169}).status_code == 422


def test_clear_rain_delay(client):
    client.post("/system/rain-delay", json={"hours": 5})
    r = client.delete("/system/rain-delay")
    assert r.status_code == 200
    assert r.json() == {"rain_delay_until": None}
    assert client.get("/system/rain-delay").json() == {"rain_delay_until": None}


def test_expired_rain_delay_reads_back_as_unset(client):
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    with database.get_db() as con:
        database.set_rain_delay_until(con, past)

    assert client.get("/system/rain-delay").json() == {"rain_delay_until": None}
    assert client.get("/system/status").json()["rain_delay_until"] is None


@pytest.mark.asyncio
async def test_scheduled_run_skipped_while_rain_delay_active(client):
    z1 = _create_zone(client, "Front Lawn", 3, duration=1)
    sched_id = _create_schedule(client, [z1])
    client.post("/system/rain-delay", json={"hours": 2})

    with patch.object(main, "turn_on_valve") as turn_on, \
         patch.object(main, "turn_off_valve"), \
         patch.object(main, "turn_off_all_valves"), \
         patch("asyncio.sleep", new=AsyncMock()):
        await main._execute_schedule(sched_id)

    turn_on.assert_not_called()


@pytest.mark.asyncio
async def test_scheduled_run_proceeds_after_rain_delay_cleared(client):
    z1 = _create_zone(client, "Back Garden", 4, duration=1)
    sched_id = _create_schedule(client, [z1])
    client.post("/system/rain-delay", json={"hours": 2})
    client.delete("/system/rain-delay")

    with patch.object(main, "turn_on_valve") as turn_on, \
         patch.object(main, "turn_off_valve"), \
         patch.object(main, "turn_off_all_valves"), \
         patch("asyncio.sleep", new=AsyncMock()):
        await main._execute_schedule(sched_id)

    turn_on.assert_called_once()
