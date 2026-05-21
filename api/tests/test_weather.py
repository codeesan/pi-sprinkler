import json
from unittest.mock import MagicMock, patch


_OPEN_METEO_RESPONSE = {
    "current": {
        "temperature_2m": 87.0,
        "weather_code": 0,
        "precipitation": 0.0,
    },
    "daily": {
        "precipitation_sum": [0.0],
        "precipitation_probability_max": [5],
    },
}


def _make_urlopen_mock(payload: dict):
    body = json.dumps(payload).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return MagicMock(return_value=mock_resp)


def test_weather_404_when_location_not_set(client):
    resp = client.get("/weather")
    assert resp.status_code == 404
    assert "Location not configured" in resp.json()["detail"]


def test_weather_returns_valid_data_when_location_set(client_with_location):
    with patch("urllib.request.urlopen", _make_urlopen_mock(_OPEN_METEO_RESPONSE)):
        resp = client_with_location.get("/weather")

    assert resp.status_code == 200
    data = resp.json()
    assert data["temperature"] == 87.0
    assert data["weather_code"] == 0
    assert data["condition"] == "Clear"
    assert data["icon"] == "mdi-weather-sunny"
    assert data["precipitation_today"] == 0.0
    assert data["precip_probability"] == 5
    assert data["rain_likely"] is False
    assert "fetched_at" in data


def test_weather_502_when_open_meteo_unreachable(client_with_location):
    with patch("urllib.request.urlopen", side_effect=OSError("Connection refused")):
        resp = client_with_location.get("/weather")

    assert resp.status_code == 502
    assert "Weather fetch failed" in resp.json()["detail"]
