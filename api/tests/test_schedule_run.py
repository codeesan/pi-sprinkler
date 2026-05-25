"""Tests for the manual schedule run endpoint and sequential zone execution."""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import database
import main


# ---------------------------------------------------------------------------
# Per-test DB cleanup so zone/schedule rows don't collide between tests
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_db(client):
    # client fixture triggers lifespan → init_db(); clean after it runs
    with database.get_db() as con:
        con.execute("DELETE FROM active_runs")
        con.execute("DELETE FROM schedules")
        con.execute("DELETE FROM zones")
        con.execute("DELETE FROM counters")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Endpoint contract tests
# ---------------------------------------------------------------------------

def test_run_schedule_404_for_missing_schedule(client):
    r = client.post("/schedules/nonexistent/run")
    assert r.status_code == 404


def test_run_schedule_409_when_already_running(client):
    z1 = _create_zone(client, "Zone A", 1)
    sched_id = _create_schedule(client, [z1])

    fake_task = MagicMock(spec=asyncio.Task)
    main._schedule_tasks[sched_id] = fake_task
    try:
        r = client.post(f"/schedules/{sched_id}/run")
        assert r.status_code == 409
    finally:
        main._schedule_tasks.pop(sched_id, None)


def test_run_schedule_202_accepted(client):
    z1 = _create_zone(client, "Zone B", 2)
    sched_id = _create_schedule(client, [z1])

    with patch.object(main, "_execute_schedule", new=AsyncMock()):
        r = client.post(f"/schedules/{sched_id}/run")

    assert r.status_code == 202
    data = r.json()
    assert data["status"] == "started"
    assert data["schedule_id"] == sched_id


# ---------------------------------------------------------------------------
# Sequential execution tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_all_zones_run_in_order(client):
    """All zones in a schedule run sequentially — not just the first.

    This is the regression test for the bug where runSchedule() only started
    the first zone because the frontend manually called runZone(firstZoneId)
    instead of delegating to the backend's _execute_schedule sequence.
    """
    z1 = _create_zone(client, "Front Lawn", 3, duration=1)
    z2 = _create_zone(client, "Back Garden", 4, duration=1)
    z3 = _create_zone(client, "Side Yard", 5, duration=1)
    sched_id = _create_schedule(client, [z1, z2, z3])

    valve_on_calls = []
    valve_off_calls = []

    with patch.object(main, "turn_on_valve", side_effect=lambda v: valve_on_calls.append(v)), \
         patch.object(main, "turn_off_valve", side_effect=lambda v: valve_off_calls.append(v)), \
         patch.object(main, "turn_off_all_valves"), \
         patch("asyncio.sleep", new=AsyncMock()):
        await main._execute_schedule(sched_id)

    # All three zones must have fired their valves — not just the first
    assert len(valve_on_calls) == 3, f"Expected 3 valve-on calls, got {valve_on_calls}"
    assert len(valve_off_calls) == 3, f"Expected 3 valve-off calls, got {valve_off_calls}"

    with database.get_db() as con:
        expected_valves = [
            database.get_zone(con, z1)["port"] - 1,
            database.get_zone(con, z2)["port"] - 1,
            database.get_zone(con, z3)["port"] - 1,
        ]
    assert valve_on_calls == expected_valves, "Zones did not run in schedule order"


@pytest.mark.asyncio
async def test_single_zone_schedule_completes(client):
    """A one-zone schedule still works end-to-end."""
    z1 = _create_zone(client, "Patio", 6, duration=1)
    sched_id = _create_schedule(client, [z1])

    valve_on_calls = []

    with patch.object(main, "turn_on_valve", side_effect=lambda v: valve_on_calls.append(v)), \
         patch.object(main, "turn_off_valve"), \
         patch.object(main, "turn_off_all_valves"), \
         patch("asyncio.sleep", new=AsyncMock()):
        await main._execute_schedule(sched_id)

    assert len(valve_on_calls) == 1


@pytest.mark.asyncio
async def test_cancellation_stops_sequence_at_outer_level():
    """_run_schedule_sequence turns off all valves when CancelledError propagates."""
    run_calls = []

    async def run_one(zone_id: str):
        run_calls.append(zone_id)
        raise asyncio.CancelledError

    all_off_calls = []
    with patch.object(main, "turn_off_all_valves", side_effect=lambda: all_off_calls.append(1)):
        with pytest.raises(asyncio.CancelledError):
            await main._run_schedule_sequence(["z1", "z2", "z3"], run_one)

    # Sequence stops after first zone raises CancelledError
    assert run_calls == ["z1"]
    # Hardware is shut down safely
    assert len(all_off_calls) >= 1
