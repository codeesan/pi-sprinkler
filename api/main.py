import sys
import os
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, Response, status, Query
from fastapi.middleware.cors import CORSMiddleware

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database import (
    get_db, init_db,
    row_to_zone, row_to_schedule,
    get_zone, get_schedule,
    create_zone, update_zone, delete_zone,
    create_schedule, update_schedule, delete_schedule,
    get_active_run, start_run, end_run, clear_all_runs,
    get_active_schedule,
    get_settings, upsert_settings,
)
from models import (
    Zone, ZoneCreate, ZoneUpdate,
    Schedule, ScheduleCreate, ScheduleUpdate,
    SystemStatus, RunningZone, ActiveSchedule,
    HistoryEvent,
    AppSettings, AppSettingsUpdate,
    WeatherData,
)

# ---------------------------------------------------------------------------
# Event logging
# ---------------------------------------------------------------------------
from event_log import (
    event_cache,
    log_system_start,
    log_manual_zone_start,
    log_manual_zone_stop,
    log_stop_all,
    log_schedule_start,
    log_schedule_zone_start,
    log_schedule_complete,
    log_schedule_skipped_rain,
)

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
# Task registries (module-level, lives for the lifetime of the process)
# ---------------------------------------------------------------------------
_zone_tasks: dict[str, asyncio.Task] = {}      # zone_id -> running asyncio.Task
_schedule_tasks: dict[str, asyncio.Task] = {}  # schedule_id -> running asyncio.Task

# APScheduler instance (async mode so it runs inside uvicorn's event loop)
scheduler = AsyncIOScheduler()


# ---------------------------------------------------------------------------
# Zone auto-shutoff background task
# ---------------------------------------------------------------------------
async def _zone_shutoff_task(zone_id: str, valve: int, duration_sec: int) -> None:
    """Sleep for duration_sec, then turn off the valve and clear the DB record."""
    try:
        await asyncio.sleep(duration_sec)
    except asyncio.CancelledError:
        pass
    finally:
        turn_off_valve(valve)
        with get_db() as con:
            end_run(con, zone_id)
        _zone_tasks.pop(zone_id, None)


# ---------------------------------------------------------------------------
# Schedule execution
# ---------------------------------------------------------------------------
async def _run_schedule_sequence(zone_ids: list[str], run_one_fn) -> None:
    """Run each zone in the schedule sequentially."""
    for zone_id in zone_ids:
        try:
            await run_one_fn(zone_id)
        except asyncio.CancelledError:
            # Propagate cancellation — caller will clean up hardware
            turn_off_all_valves()
            raise


async def _execute_schedule(schedule_id: str) -> None:
    """APScheduler callback: runs all zones in a schedule sequentially."""
    with get_db() as con:
        schedule = get_schedule(con, schedule_id)
        s = get_settings(con)
    if not schedule:
        return

    # Rain delay check
    if s["rain_delay_enabled"] and _weather_cache is not None:
        prob = _weather_cache.precip_probability
        threshold = s["rain_delay_threshold"]
        if _weather_cache.rain_likely or prob >= threshold:
            log_schedule_skipped_rain(schedule["name"], prob)
            # TODO: prompt user about postponing watering once notifications have been added.
            # Send a notification asking whether to skip this run before silently returning.
            return

    log_schedule_start(schedule["name"], len(schedule["zoneIds"]))

    async def run_one(zone_id: str) -> None:
        with get_db() as con:
            zone = get_zone(con, zone_id)
        if not zone:
            return
        valve = zone["port"] - 1
        duration_sec = zone["duration"] * 60

        # Single-valve enforcement: wait up to 1 hour (720 × 5 s) for manual run to finish
        for _ in range(720):
            with get_db() as con:
                existing = get_active_run(con)
            if not existing:
                break
            await asyncio.sleep(5)

        # Clear whatever was left (timeout or stale record)
        turn_off_all_valves()
        with get_db() as con:
            clear_all_runs(con)

        # Delegate to relay controller hardware and log the zone start
        log_schedule_zone_start(schedule["name"], zone["name"], zone["duration"])
        turn_on_valve(valve)
        with get_db() as con:
            start_run(con, zone_id, zone["name"], duration_sec, schedule_id)
        try:
            await asyncio.sleep(duration_sec)
        except asyncio.CancelledError:
            return
        finally:
            turn_off_valve(valve)
            with get_db() as con:
                end_run(con, zone_id)

    task = asyncio.create_task(
        _run_schedule_sequence(schedule["zoneIds"], run_one)
    )
    _schedule_tasks[schedule_id] = task
    try:
        await task
        log_schedule_complete(schedule["name"])
    finally:
        _schedule_tasks.pop(schedule_id, None)


# ---------------------------------------------------------------------------
# Scheduler management
# ---------------------------------------------------------------------------
def _reload_scheduler() -> None:
    """
    Remove all APScheduler jobs and re-add them from the DB.
    Called on startup and after every schedule CRUD operation.
    """
    scheduler.remove_all_jobs()
    with get_db() as con:
        rows = con.execute("SELECT * FROM schedules WHERE enabled = 1").fetchall()
        schedules = [row_to_schedule(r) for r in rows]

    for s in schedules:
        for time_str in s["startTimes"]:
            h, m = time_str.split(":")
            # Map app day abbreviations (Mon, Tue…) to APScheduler lowercase (mon, tue…)
            days = ",".join(d.lower() for d in s["days"])
            scheduler.add_job(
                _execute_schedule,
                CronTrigger(day_of_week=days, hour=int(h), minute=int(m)),
                id=f"{s['id']}_{time_str}",
                args=[s["id"]],
                replace_existing=True,
                misfire_grace_time=300,
            )


# ---------------------------------------------------------------------------
# App lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    # Startup safety: clear any stale run state left from a previous crash
    with get_db() as con:
        clear_all_runs(con)
    turn_off_all_valves()  # runs even when HW_AVAILABLE is False

    # Boot APScheduler with jobs loaded from DB
    _reload_scheduler()
    scheduler.start()

    log_system_start()

    yield

    scheduler.shutdown()


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
# Settings
# ---------------------------------------------------------------------------
@app.get("/settings", response_model=AppSettings)
def read_settings():
    with get_db() as con:
        data = get_settings(con)
    return AppSettings(
        name=data["name"],
        location=data["location"],
        rain_delay_enabled=data["rain_delay_enabled"],
        rain_delay_threshold=data["rain_delay_threshold"],
    )


@app.put("/settings", response_model=AppSettings)
def write_settings(body: AppSettingsUpdate):
    with get_db() as con:
        data = upsert_settings(
            con,
            name=body.name,
            location=body.location.model_dump() if body.location is not None else None,
            rain_delay_enabled=body.rain_delay_enabled,
            rain_delay_threshold=body.rain_delay_threshold,
        )
    return AppSettings(
        name=data["name"],
        location=data["location"],
        rain_delay_enabled=data["rain_delay_enabled"],
        rain_delay_threshold=data["rain_delay_threshold"],
    )


# ---------------------------------------------------------------------------
# Weather  (cached 30 min; fetched server-side so the Pi can act on rain data)
# ---------------------------------------------------------------------------
_WMO_MAP = [
    ([0],                   'mdi-weather-sunny',           'Clear'),
    ([1],                   'mdi-weather-sunny',           'Mostly Clear'),
    ([2],                   'mdi-weather-partly-cloudy',   'Partly Cloudy'),
    ([3],                   'mdi-weather-cloudy',          'Overcast'),
    ([45, 48],              'mdi-weather-fog',             'Foggy'),
    ([51,52,53,54,55],      'mdi-weather-rainy',           'Drizzle'),
    ([61,62,63,64,65],      'mdi-weather-rainy',           'Rain'),
    ([66, 67],              'mdi-weather-snowy-rainy',     'Freezing Rain'),
    ([71,72,73,74,75,77],   'mdi-weather-snowy',           'Snow'),
    ([80, 81, 82],          'mdi-weather-pouring',         'Rain Showers'),
    ([85, 86],              'mdi-weather-snowy',           'Snow Showers'),
    ([95],                  'mdi-weather-lightning-rainy', 'Thunderstorm'),
    ([96, 99],              'mdi-weather-lightning-rainy', 'Severe Thunderstorm'),
]

def _resolve_wmo(code: int) -> tuple[str, str]:
    for codes, icon, label in _WMO_MAP:
        if code in codes:
            return icon, label
    return 'mdi-weather-cloudy', 'Unknown'

_weather_cache: WeatherData | None = None
_weather_cached_at: datetime | None = None
_WEATHER_TTL = timedelta(minutes=30)


@app.get("/weather", response_model=WeatherData)
async def get_weather():
    global _weather_cache, _weather_cached_at

    # Serve from cache if still fresh
    now = datetime.now(timezone.utc)
    if _weather_cache and _weather_cached_at and (now - _weather_cached_at) < _WEATHER_TTL:
        return _weather_cache

    # Load coordinates from settings
    with get_db() as con:
        s = get_settings(con)
    lat = s["location"].get("lat")
    lon = s["location"].get("lon")
    if lat is None or lon is None:
        raise HTTPException(status_code=404, detail="Location not configured in settings")

    # Fetch from Open-Meteo (free, no API key required)
    import urllib.request, json as _json
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,weather_code,precipitation"
        f"&daily=precipitation_sum,precipitation_probability_max"
        f"&temperature_unit=fahrenheit&precipitation_unit=inch"
        f"&timezone=auto&forecast_days=1"
    )
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = _json.loads(resp.read())
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Weather fetch failed: {exc}")

    current        = data["current"]
    daily          = data["daily"]
    temp           = round(current["temperature_2m"], 1)
    code           = int(current["weather_code"])
    precip_now     = float(current.get("precipitation") or 0)
    precip_today   = float((daily.get("precipitation_sum") or [0])[0] or 0)
    precip_prob    = int((daily.get("precipitation_probability_max") or [0])[0] or 0)
    icon, label    = _resolve_wmo(code)
    rain_likely    = precip_prob >= 50 or precip_today > 0.1

    _weather_cache = WeatherData(
        temperature=temp,
        weather_code=code,
        condition=label,
        icon=icon,
        precipitation_today=round(precip_today, 2),
        precip_probability=precip_prob,
        rain_likely=rain_likely,
        fetched_at=now.isoformat(),
    )
    _weather_cached_at = now
    return _weather_cache


# ---------------------------------------------------------------------------
# Event history
# ---------------------------------------------------------------------------
@app.get("/history", response_model=list[HistoryEvent])
def get_history(limit: int = Query(default=100, ge=1, le=500)):
    """Return the most-recent `limit` events from the in-memory event cache."""
    events = list(event_cache)  # deque is already ordered most-recent first
    return events[:limit]


# ---------------------------------------------------------------------------
# System status (frontend polling)
# ---------------------------------------------------------------------------
@app.get("/system/status", response_model=SystemStatus)
def system_status():
    with get_db() as con:
        run = get_active_run(con)
        sched_info = get_active_schedule(con) if run else None

    if not run:
        return SystemStatus(any_running=False, running_zone=None, active_schedule=None)

    started = datetime.fromisoformat(run["started_at"])
    elapsed = int((datetime.now(timezone.utc) - started).total_seconds())
    remaining = max(0, run["duration_sec"] - elapsed)

    rz = RunningZone(
        zone_id=run["zone_id"],
        zone_name=run["zone_name"],
        duration_sec=run["duration_sec"],
        elapsed_sec=elapsed,
        time_remaining_sec=remaining,
        schedule_id=run["schedule_id"],
    )
    as_ = ActiveSchedule(**sched_info) if sched_info else None
    return SystemStatus(any_running=True, running_zone=rz, active_schedule=as_)


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
            raise HTTPException(
                status_code=409,
                detail=f"Port {body.port} is already assigned to another zone",
            )
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
async def run_zone(
    zone_id: str,
    duration_minutes: int | None = Query(default=None, ge=1),
):
    with get_db() as con:
        zone = get_zone(con, zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    valve = zone["port"] - 1
    duration_sec = (duration_minutes * 60) if duration_minutes else (zone["duration"] * 60)

    # Single-valve enforcement: only one zone may run at a time
    with get_db() as con:
        existing = get_active_run(con)
    if existing and existing["zone_id"] != zone_id:
        raise HTTPException(
            status_code=409,
            detail=f"Zone {existing['zone_name']} is already running",
        )

    # Cancel any lingering shutoff task for this zone (re-run case)
    if zone_id in _zone_tasks:
        _zone_tasks.pop(zone_id).cancel()

    turn_on_valve(valve)

    with get_db() as con:
        start_run(con, zone_id, zone["name"], duration_sec)

    duration_min = duration_sec // 60
    log_manual_zone_start(zone["name"], duration_min)

    # Schedule the auto-shutoff background task
    task = asyncio.create_task(_zone_shutoff_task(zone_id, valve, duration_sec))
    _zone_tasks[zone_id] = task

    return {"status": "running", "zone_id": zone_id, "duration_sec": duration_sec}


@app.post("/zones/{zone_id}/stop")
async def stop_zone(zone_id: str):
    with get_db() as con:
        zone = get_zone(con, zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    # Cancel the auto-shutoff task if it exists
    if zone_id in _zone_tasks:
        _zone_tasks.pop(zone_id).cancel()

    # Cancel any schedule task that was running this zone
    with get_db() as con:
        run = get_active_run(con)
    if run and run.get("schedule_id"):
        sched_id = run["schedule_id"]
        if sched_id in _schedule_tasks:
            _schedule_tasks.pop(sched_id).cancel()

    turn_off_valve(zone["port"] - 1)

    with get_db() as con:
        end_run(con, zone_id)

    log_manual_zone_stop(zone["name"])

    return {"status": "idle"}


# ---------------------------------------------------------------------------
# Valves — global control
# ---------------------------------------------------------------------------
@app.post("/valves/stop-all")
async def stop_all_valves():
    # Cancel all zone shutoff tasks
    for t in list(_zone_tasks.values()):
        t.cancel()
    _zone_tasks.clear()

    # Cancel all schedule tasks
    for t in list(_schedule_tasks.values()):
        t.cancel()
    _schedule_tasks.clear()

    turn_off_all_valves()

    with get_db() as con:
        clear_all_runs(con)

    log_stop_all()

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
        result = create_schedule(
            con,
            body.name,
            body.days,
            body.startTimes,
            body.zoneIds,
            body.enabled,
        )
    _reload_scheduler()
    return result


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
    _reload_scheduler()
    return result


@app.delete("/schedules/{sched_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_schedule(sched_id: str):
    with get_db() as con:
        if not delete_schedule(con, sched_id):
            raise HTTPException(status_code=404, detail="Schedule not found")
    _reload_scheduler()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/schedules/{sched_id}/run", status_code=status.HTTP_202_ACCEPTED)
async def run_schedule_now(sched_id: str):
    with get_db() as con:
        schedule = get_schedule(con, sched_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    if sched_id in _schedule_tasks:
        raise HTTPException(status_code=409, detail="Schedule already running")
    asyncio.create_task(_execute_schedule(sched_id))
    return {"status": "started", "schedule_id": sched_id}
