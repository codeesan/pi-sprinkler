import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware

from database import (
    get_db, init_db,
    row_to_zone, row_to_schedule,
    get_zone, get_schedule,
    create_zone, update_zone, delete_zone,
    create_schedule, update_schedule, delete_schedule,
)
from models import Zone, ZoneCreate, ZoneUpdate, Schedule, ScheduleCreate, ScheduleUpdate

# ---------------------------------------------------------------------------
# Hardware — graceful fallback when smbus2 is unavailable (dev / Mac)
# ---------------------------------------------------------------------------
try:
    from sprinklerfunctions import (
        turn_on_valve,
        turn_off_valve,
        turn_off_all_valves,
        get_all_valve_status,
    )
    HW_AVAILABLE = True
except Exception:
    HW_AVAILABLE = False

    def turn_on_valve(v: int) -> None: pass
    def turn_off_valve(v: int) -> None: pass
    def turn_off_all_valves() -> bool: return True
    def get_all_valve_status() -> list[dict]: return [{"valve": i, "status": "OFF"} for i in range(16)]


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Sprinkler API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/healthz")
def health():
    return {"status": "ok", "hw_available": HW_AVAILABLE}


# ---------------------------------------------------------------------------
# Zones — CRUD
# ---------------------------------------------------------------------------
@app.get("/zones", response_model=list[Zone])
def list_zones():
    with get_db() as con:
        rows = con.execute("SELECT * FROM zones ORDER BY port").fetchall()
        return [row_to_zone(r) for r in rows]


@app.post("/zones", response_model=Zone, status_code=status.HTTP_201_CREATED)
def add_zone(body: ZoneCreate):
    with get_db() as con:
        if con.execute("SELECT id FROM zones WHERE port = ?", (body.port,)).fetchone():
            raise HTTPException(status_code=409, detail=f"Port {body.port} is already assigned to another zone")
        return create_zone(con, body.name, body.port, body.duration, body.icon, body.color)


@app.put("/zones/{zone_id}", response_model=Zone)
def replace_zone(zone_id: str, body: ZoneUpdate):
    with get_db() as con:
        if not get_zone(con, zone_id):
            raise HTTPException(status_code=404, detail="Zone not found")
        result = update_zone(con, zone_id, **body.model_dump(exclude_none=True))
        return result


@app.delete("/zones/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_zone(zone_id: str):
    with get_db() as con:
        if not delete_zone(con, zone_id):
            raise HTTPException(status_code=404, detail="Zone not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Zones — hardware control
# ---------------------------------------------------------------------------
@app.post("/zones/{zone_id}/run")
def run_zone(zone_id: str):
    with get_db() as con:
        zone = get_zone(con, zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    valve = zone["port"] - 1
    turn_on_valve(valve)
    return {"status": "running", "zone_id": zone_id, "valve": valve}


@app.post("/zones/{zone_id}/stop")
def stop_zone(zone_id: str):
    with get_db() as con:
        zone = get_zone(con, zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    valve = zone["port"] - 1
    turn_off_valve(valve)
    return {"status": "idle", "zone_id": zone_id, "valve": valve}


# ---------------------------------------------------------------------------
# Valves — global control
# ---------------------------------------------------------------------------
@app.post("/valves/stop-all")
def stop_all_valves():
    turn_off_all_valves()
    return {"status": "all_off"}


@app.get("/valves/status")
def valve_status():
    return get_all_valve_status()


# ---------------------------------------------------------------------------
# Schedules — CRUD
# ---------------------------------------------------------------------------
@app.get("/schedules", response_model=list[Schedule])
def list_schedules():
    with get_db() as con:
        rows = con.execute("SELECT * FROM schedules").fetchall()
        return [row_to_schedule(r) for r in rows]


@app.post("/schedules", response_model=Schedule, status_code=status.HTTP_201_CREATED)
def add_schedule(body: ScheduleCreate):
    with get_db() as con:
        return create_schedule(
            con,
            body.name,
            body.days,
            body.startTimes,
            body.zoneIds,
            body.enabled,
        )


@app.put("/schedules/{sched_id}", response_model=Schedule)
def replace_schedule(sched_id: str, body: ScheduleUpdate):
    with get_db() as con:
        if not get_schedule(con, sched_id):
            raise HTTPException(status_code=404, detail="Schedule not found")
        data = body.model_dump(exclude_none=True)
        # Map frontend camelCase keys to DB snake_case keys
        if "startTimes" in data:
            data["start_times"] = data.pop("startTimes")
        if "zoneIds" in data:
            data["zone_ids"] = data.pop("zoneIds")
        result = update_schedule(con, sched_id, **data)
        return result


@app.delete("/schedules/{sched_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_schedule(sched_id: str):
    with get_db() as con:
        if not delete_schedule(con, sched_id):
            raise HTTPException(status_code=404, detail="Schedule not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
