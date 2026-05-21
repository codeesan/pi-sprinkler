import os
import sys
import tempfile
import pytest
from unittest.mock import patch

# Point the database module at a fresh temp file before main.py is imported.
_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp_db.close()

API_DIR = os.path.dirname(os.path.dirname(__file__))
if API_DIR not in sys.path:
    sys.path.insert(0, API_DIR)

import database
database.DB_PATH = _tmp_db.name

from fastapi.testclient import TestClient
import main  # noqa: E402


@pytest.fixture()
def client():
    main._weather_cache = None
    main._weather_cached_at = None
    # Prevent APScheduler from binding to the event loop during lifespan startup.
    # Each TestClient creates a new loop; the scheduler's stored loop goes stale
    # after the first client closes, causing RuntimeError on subsequent tests.
    with patch.object(main, '_reload_scheduler', lambda: None), \
         patch.object(main.scheduler, 'start'), \
         patch.object(main.scheduler, 'shutdown'):
        with TestClient(main.app) as c:
            yield c
    main._weather_cache = None
    main._weather_cached_at = None


@pytest.fixture()
def client_with_location(client):
    resp = client.put("/settings", json={
        "location": {"city": "Canyon Country", "lat": 34.4233, "lon": -118.4720}
    })
    assert resp.status_code == 200
    return client
