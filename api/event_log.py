"""
event_log.py — Structured event logging for the sprinkler controller.

Writes human-readable lines to a rotating file at api/logs/sprinkler.log
and simultaneously maintains an in-memory deque of structured event dicts
for fast, no-I/O reads via the GET /history endpoint.
"""

import logging
import uuid
from collections import deque
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

# ---------------------------------------------------------------------------
# Log directory / file setup
# ---------------------------------------------------------------------------
_logs_dir = Path(__file__).parent / "logs"
_logs_dir.mkdir(exist_ok=True)  # Create at runtime; not committed to git

_LOG_FILE = _logs_dir / "sprinkler.log"
_MAX_BYTES = 1 * 1024 * 1024  # 1 MB per file
_BACKUP_COUNT = 5

# ---------------------------------------------------------------------------
# In-memory event deque (fast reads, survives for the process lifetime)
# ---------------------------------------------------------------------------
event_cache: deque[dict] = deque(maxlen=500)


# ---------------------------------------------------------------------------
# Custom handler: mirrors every log record into the structured deque
# ---------------------------------------------------------------------------
class _DequeHandler(logging.Handler):
    """Appends a pre-built event dict (stored in LogRecord.__dict__) to the deque."""

    def emit(self, record: logging.LogRecord) -> None:
        event = getattr(record, "_event_dict", None)
        if event is not None:
            event_cache.appendleft(event)  # most-recent first


# ---------------------------------------------------------------------------
# Logger wiring
# ---------------------------------------------------------------------------
_logger = logging.getLogger("sprinkler.events")
_logger.setLevel(logging.DEBUG)
_logger.propagate = False  # Don't bubble up to the root logger

# Rotating file handler — human-readable lines
_file_handler = RotatingFileHandler(
    _LOG_FILE,
    maxBytes=_MAX_BYTES,
    backupCount=_BACKUP_COUNT,
    encoding="utf-8",
)
_file_handler.setFormatter(
    logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s", datefmt="%Y-%m-%dT%H:%M:%SZ")
)
_logger.addHandler(_file_handler)

# Deque handler — structured dicts
_logger.addHandler(_DequeHandler())


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------
def _emit(event_type: str, message: str, details: dict) -> None:
    """Build a structured event dict, attach it to a LogRecord, and emit."""
    event = {
        "id": uuid.uuid4().hex[:12],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": event_type,
        "message": message,
        "details": details,
    }
    record = _logger.makeRecord(
        name=_logger.name,
        level=logging.INFO,
        fn="",
        lno=0,
        msg=message,
        args=(),
        exc_info=None,
    )
    record._event_dict = event  # type: ignore[attr-defined]
    _logger.handle(record)


# ---------------------------------------------------------------------------
# Public helper functions
# ---------------------------------------------------------------------------

def log_system_start() -> None:
    _emit(
        event_type="system_start",
        message="Sprinkler system started",
        details={},
    )


def log_manual_zone_start(zone_name: str, duration_min: int) -> None:
    _emit(
        event_type="zone_start",
        message=f"{zone_name} started manually ({duration_min} min)",
        details={"zone_name": zone_name, "duration_min": duration_min, "trigger": "manual"},
    )


def log_manual_zone_stop(zone_name: str) -> None:
    _emit(
        event_type="zone_stop",
        message=f"{zone_name} stopped manually",
        details={"zone_name": zone_name, "trigger": "manual"},
    )


def log_stop_all() -> None:
    _emit(
        event_type="stop_all",
        message="All zones stopped",
        details={},
    )


def log_schedule_start(schedule_name: str, zone_count: int) -> None:
    _emit(
        event_type="schedule_start",
        message=f"Schedule '{schedule_name}' started ({zone_count} zones)",
        details={"schedule_name": schedule_name, "zone_count": zone_count},
    )


def log_schedule_zone_start(schedule_name: str, zone_name: str, duration_min: int) -> None:
    _emit(
        event_type="schedule_zone_start",
        message=f"Schedule '{schedule_name}': {zone_name} started ({duration_min} min)",
        details={
            "schedule_name": schedule_name,
            "zone_name": zone_name,
            "duration_min": duration_min,
        },
    )


def log_schedule_complete(schedule_name: str) -> None:
    _emit(
        event_type="schedule_complete",
        message=f"Schedule '{schedule_name}' completed",
        details={"schedule_name": schedule_name},
    )


def log_schedule_skipped_rain(schedule_name: str, precip_probability: int) -> None:
    _emit(
        event_type="schedule_skipped_rain",
        message=f"Schedule '{schedule_name}' skipped — {precip_probability}% chance of rain",
        details={"schedule_name": schedule_name, "precip_probability": precip_probability},
    )
