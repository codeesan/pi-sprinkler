import json
import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "sprinklers.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS zones (
    id      TEXT PRIMARY KEY,
    name    TEXT NOT NULL,
    port    INTEGER NOT NULL,
    duration INTEGER NOT NULL DEFAULT 15,
    icon    TEXT NOT NULL DEFAULT 'mdi-water',
    color   TEXT NOT NULL DEFAULT 'primary'
);

CREATE TABLE IF NOT EXISTS schedules (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    days        TEXT NOT NULL DEFAULT '[]',
    start_times TEXT NOT NULL DEFAULT '[]',
    zone_ids    TEXT NOT NULL DEFAULT '[]',
    enabled     INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS counters (
    key   TEXT PRIMARY KEY,
    value INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS active_runs (
    zone_id      TEXT PRIMARY KEY,
    zone_name    TEXT NOT NULL,
    started_at   TEXT NOT NULL,
    duration_sec INTEGER NOT NULL,
    schedule_id  TEXT
);

CREATE TABLE IF NOT EXISTS app_settings (
    id                   INTEGER PRIMARY KEY CHECK (id = 1),
    name                 TEXT NOT NULL DEFAULT '',
    loc_city             TEXT NOT NULL DEFAULT '',
    loc_lat              REAL,
    loc_lon              REAL,
    rain_delay_enabled   INTEGER NOT NULL DEFAULT 0,
    rain_delay_threshold INTEGER NOT NULL DEFAULT 50
);
"""

_SEED_ZONES = [
    ("zone-1", "Front Lawn Left",  1, 15, "mdi-grass",  "secondary"),
    ("zone-2", "Front Lawn Right", 2, 15, "mdi-grass",  "secondary"),
    ("zone-3", "Front Lawn Drip",  3, 20, "mdi-water",  "accent"),
    ("zone-4", "Back Yard",        4, 20, "mdi-leaf",   "primary"),
    ("zone-5", "Rose Garden",      5, 10, "mdi-flower", "error"),
]

_SEED_SCHEDULES = [
    ("sched-1", "Front Yard", '["Mon","Wed","Fri"]', '["06:00"]', '["zone-1","zone-2","zone-3"]', 1),
    ("sched-2", "Back Yard",  '["Tue","Thu","Sat"]', '["07:00"]', '["zone-4","zone-5"]',           1),
]


@contextmanager
def get_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    try:
        yield con
        con.commit()
    finally:
        con.close()


def _migrate_app_settings(con) -> None:
    # Add columns that exist in the schema but are absent from the live table.
    # Needed when deploying to a Pi whose DB was initialised before a schema change.
    existing = {row[1] for row in con.execute("PRAGMA table_info(app_settings)").fetchall()}
    pending = [
        ("rain_delay_enabled",   "INTEGER NOT NULL DEFAULT 0"),
        ("rain_delay_threshold", "INTEGER NOT NULL DEFAULT 50"),
    ]
    for col, definition in pending:
        if col not in existing:
            con.execute(f"ALTER TABLE app_settings ADD COLUMN {col} {definition}")


def init_db():
    with get_db() as con:
        con.executescript(_SCHEMA)
        _migrate_app_settings(con)
        if not con.execute("SELECT 1 FROM zones LIMIT 1").fetchone():
            con.executemany(
                "INSERT INTO zones (id, name, port, duration, icon, color) VALUES (?,?,?,?,?,?)",
                _SEED_ZONES,
            )
            con.execute("INSERT OR IGNORE INTO counters (key, value) VALUES ('zone_counter', 5)")
        if not con.execute("SELECT 1 FROM schedules LIMIT 1").fetchone():
            con.executemany(
                "INSERT INTO schedules (id, name, days, start_times, zone_ids, enabled) VALUES (?,?,?,?,?,?)",
                _SEED_SCHEDULES,
            )
            con.execute("INSERT OR IGNORE INTO counters (key, value) VALUES ('sched_counter', 2)")


def _next_id(con, key: str, prefix: str) -> str:
    con.execute("INSERT OR IGNORE INTO counters (key, value) VALUES (?, 0)", (key,))
    con.execute("UPDATE counters SET value = value + 1 WHERE key = ?", (key,))
    n = con.execute("SELECT value FROM counters WHERE key = ?", (key,)).fetchone()[0]
    return f"{prefix}-{n}"


def row_to_zone(row) -> dict:
    return {
        "id":       row["id"],
        "name":     row["name"],
        "port":     row["port"],
        "duration": row["duration"],
        "icon":     row["icon"],
        "color":    row["color"],
    }


def row_to_schedule(row) -> dict:
    return {
        "id":         row["id"],
        "name":       row["name"],
        "days":       json.loads(row["days"]),
        "startTimes": json.loads(row["start_times"]),
        "zoneIds":    json.loads(row["zone_ids"]),
        "enabled":    bool(row["enabled"]),
    }


def get_zone(con, zone_id: str) -> dict | None:
    row = con.execute("SELECT * FROM zones WHERE id = ?", (zone_id,)).fetchone()
    return row_to_zone(row) if row else None


def get_schedule(con, sched_id: str) -> dict | None:
    row = con.execute("SELECT * FROM schedules WHERE id = ?", (sched_id,)).fetchone()
    return row_to_schedule(row) if row else None


def create_zone(con, name: str, port: int, duration: int, icon: str, color: str) -> dict:
    zone_id = _next_id(con, "zone_counter", "zone")
    con.execute(
        "INSERT INTO zones (id, name, port, duration, icon, color) VALUES (?,?,?,?,?,?)",
        (zone_id, name, port, duration, icon, color),
    )
    return get_zone(con, zone_id)


def update_zone(con, zone_id: str, **fields) -> dict | None:
    allowed = {"name", "port", "duration", "icon", "color"}
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not updates:
        return get_zone(con, zone_id)
    cols = ", ".join(f"{k} = ?" for k in updates)
    con.execute(f"UPDATE zones SET {cols} WHERE id = ?", (*updates.values(), zone_id))
    return get_zone(con, zone_id)


def delete_zone(con, zone_id: str) -> bool:
    cur = con.execute("DELETE FROM zones WHERE id = ?", (zone_id,))
    return cur.rowcount > 0


def create_schedule(con, name: str, days: list, start_times: list, zone_ids: list, enabled: bool) -> dict:
    sched_id = _next_id(con, "sched_counter", "sched")
    con.execute(
        "INSERT INTO schedules (id, name, days, start_times, zone_ids, enabled) VALUES (?,?,?,?,?,?)",
        (sched_id, name, json.dumps(days), json.dumps(start_times), json.dumps(zone_ids), int(enabled)),
    )
    return get_schedule(con, sched_id)


def update_schedule(con, sched_id: str, **fields) -> dict | None:
    row = con.execute("SELECT * FROM schedules WHERE id = ?", (sched_id,)).fetchone()
    if not row:
        return None
    name        = fields.get("name",        row["name"])
    days        = json.dumps(fields.get("days",        json.loads(row["days"])))
    start_times = json.dumps(fields.get("start_times", json.loads(row["start_times"])))
    zone_ids    = json.dumps(fields.get("zone_ids",    json.loads(row["zone_ids"])))
    enabled     = int(fields.get("enabled", bool(row["enabled"])))
    con.execute(
        "UPDATE schedules SET name=?, days=?, start_times=?, zone_ids=?, enabled=? WHERE id=?",
        (name, days, start_times, zone_ids, enabled, sched_id),
    )
    return get_schedule(con, sched_id)


def delete_schedule(con, sched_id: str) -> bool:
    cur = con.execute("DELETE FROM schedules WHERE id = ?", (sched_id,))
    return cur.rowcount > 0


# ---------------------------------------------------------------------------
# Active-run helpers
# ---------------------------------------------------------------------------

def get_active_run(con) -> dict | None:
    """Return the single running zone record as a dict, or None."""
    row = con.execute("SELECT * FROM active_runs LIMIT 1").fetchone()
    if not row:
        return None
    return {
        "zone_id":      row["zone_id"],
        "zone_name":    row["zone_name"],
        "started_at":   row["started_at"],
        "duration_sec": row["duration_sec"],
        "schedule_id":  row["schedule_id"],
    }


def start_run(
    con,
    zone_id: str,
    zone_name: str,
    duration_sec: int,
    schedule_id: str | None = None,
) -> None:
    """INSERT OR REPLACE into active_runs."""
    from datetime import datetime, timezone
    started_at = datetime.now(timezone.utc).isoformat()
    con.execute(
        """
        INSERT OR REPLACE INTO active_runs
            (zone_id, zone_name, started_at, duration_sec, schedule_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        (zone_id, zone_name, started_at, duration_sec, schedule_id),
    )


def end_run(con, zone_id: str) -> None:
    """DELETE the active_runs row for zone_id."""
    con.execute("DELETE FROM active_runs WHERE zone_id = ?", (zone_id,))


def clear_all_runs(con) -> None:
    """DELETE all rows from active_runs."""
    con.execute("DELETE FROM active_runs")


def get_settings(con) -> dict:
    row = con.execute("SELECT * FROM app_settings WHERE id = 1").fetchone()
    if not row:
        return {
            "name": "",
            "location": {"city": "", "lat": None, "lon": None},
            "rain_delay_enabled": False,
            "rain_delay_threshold": 50,
        }
    return {
        "name": row["name"],
        "location": {"city": row["loc_city"], "lat": row["loc_lat"], "lon": row["loc_lon"]},
        "rain_delay_enabled": bool(row["rain_delay_enabled"]),
        "rain_delay_threshold": row["rain_delay_threshold"],
    }


def upsert_settings(
    con,
    name: str | None = None,
    location: dict | None = None,
    rain_delay_enabled: bool | None = None,
    rain_delay_threshold: int | None = None,
) -> dict:
    current = get_settings(con)
    new_name = name if name is not None else current["name"]
    new_loc = {**current["location"], **(location or {})}
    new_rde = rain_delay_enabled if rain_delay_enabled is not None else current["rain_delay_enabled"]
    new_rdt = rain_delay_threshold if rain_delay_threshold is not None else current["rain_delay_threshold"]
    con.execute(
        """
        INSERT INTO app_settings (id, name, loc_city, loc_lat, loc_lon, rain_delay_enabled, rain_delay_threshold)
        VALUES (1, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name                 = excluded.name,
            loc_city             = excluded.loc_city,
            loc_lat              = excluded.loc_lat,
            loc_lon              = excluded.loc_lon,
            rain_delay_enabled   = excluded.rain_delay_enabled,
            rain_delay_threshold = excluded.rain_delay_threshold
        """,
        (new_name, new_loc.get("city", ""), new_loc.get("lat"), new_loc.get("lon"), int(new_rde), new_rdt),
    )
    return get_settings(con)


def get_active_schedule(con) -> dict | None:
    """
    Return schedule info for the currently running zone's schedule, or None.

    Joins active_runs → schedules.  Returns a dict with keys:
        schedule_id, schedule_name, zone_index, total_zones
    """
    row = con.execute("SELECT * FROM active_runs LIMIT 1").fetchone()
    if not row or not row["schedule_id"]:
        return None
    sched_row = con.execute(
        "SELECT * FROM schedules WHERE id = ?", (row["schedule_id"],)
    ).fetchone()
    if not sched_row:
        return None
    import json
    zone_ids = json.loads(sched_row["zone_ids"])
    try:
        zone_index = zone_ids.index(row["zone_id"])
    except ValueError:
        zone_index = 0
    return {
        "schedule_id":   sched_row["id"],
        "schedule_name": sched_row["name"],
        "zone_index":    zone_index,
        "total_zones":   len(zone_ids),
    }
