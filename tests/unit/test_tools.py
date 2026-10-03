"""Unit tests for the agent's tools, with Open-Meteo stubbed out."""

import re

import httpx
import pytest

from weather_time_agent import agent
from weather_time_agent.agent import get_current_time, get_forecast, get_weather

PARIS = {
    "name": "Paris",
    "country": "France",
    "latitude": 48.85341,
    "longitude": 2.3488,
    "timezone": "Europe/Paris",
}
FORECAST = {
    "current": {
        "temperature_2m": 13.6,
        "apparent_temperature": 12.3,
        "relative_humidity_2m": 69,
        "weather_code": 2,
        "wind_speed_10m": 5.4,
    }
}
DAILY_FORECAST = {
    "daily": {
        "time": ["2026-10-03", "2026-10-04"],
        "weather_code": [3, 61],
        "temperature_2m_max": [22.3, 24.6],
        "temperature_2m_min": [11.6, 15.2],
        "precipitation_probability_max": [3, 80],
        "precipitation_sum": [0.0, 4.2],
    }
}


@pytest.fixture
def open_meteo(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, dict]]:
    """Answers geocoding with Paris (or nothing for "Atlantis") and records calls."""
    calls: list[tuple[str, dict]] = []

    async def fake_get_json(url: str, params: dict) -> dict:
        calls.append((url, params))
        if url == agent.GEOCODING_URL:
            return {} if params["name"] == "Atlantis" else {"results": [PARIS]}
        return DAILY_FORECAST if "daily" in params else FORECAST

    monkeypatch.setattr(agent, "_get_json", fake_get_json)
    return calls


async def test_get_weather(open_meteo: list[tuple[str, dict]]) -> None:
    result = await get_weather("  Paris ")
    assert result == {
        "status": "success",
        "report": (
            "The weather in Paris, France is partly cloudy, 13.6 °C (feels like "
            "12.3 °C), humidity 69%, wind 5.4 km/h."
        ),
    }
    assert open_meteo[0][1]["name"] == "Paris"
    assert open_meteo[1] == (
        agent.FORECAST_URL,
        {
            "latitude": 48.85341,
            "longitude": 2.3488,
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m",
            "timezone": "auto",
        },
    )


async def test_get_weather_unknown_city(open_meteo: list[tuple[str, dict]]) -> None:
    result = await get_weather("Atlantis")
    assert result == {
        "status": "error",
        "error_message": "No location found for 'Atlantis'.",
    }
    assert len(open_meteo) == 1, "No forecast call for an unknown city"


async def test_get_weather_service_down(monkeypatch: pytest.MonkeyPatch) -> None:
    async def failing_get_json(url: str, params: dict) -> dict:
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(agent, "_get_json", failing_get_json)
    result = await get_weather("Paris")
    assert result["status"] == "error"
    assert "unavailable" in result["error_message"]


async def test_get_forecast(open_meteo: list[tuple[str, dict]]) -> None:
    result = await get_forecast("Paris", 2)
    assert result == {
        "status": "success",
        "report": (
            "Forecast for Paris, France:\n"
            "- Saturday 2026-10-03: overcast, 11.6 to 22.3 °C, "
            "3% chance of precipitation (0.0 mm).\n"
            "- Sunday 2026-10-04: slight rain, 15.2 to 24.6 °C, "
            "80% chance of precipitation (4.2 mm)."
        ),
    }
    forecast_params = open_meteo[1][1]
    assert forecast_params["forecast_days"] == 2
    assert "current" not in forecast_params


@pytest.mark.parametrize("days", [0, 17])
async def test_get_forecast_rejects_out_of_range_days(
    open_meteo: list[tuple[str, dict]], days: int
) -> None:
    result = await get_forecast("Paris", days)
    assert result == {
        "status": "error",
        "error_message": f"Can only forecast between 1 and 16 days, not {days}.",
    }
    assert open_meteo == [], "No API call for an invalid range"


async def test_get_forecast_unknown_city(open_meteo: list[tuple[str, dict]]) -> None:
    result = await get_forecast("Atlantis", 3)
    assert result == {
        "status": "error",
        "error_message": "No location found for 'Atlantis'.",
    }


async def test_get_current_time(open_meteo: list[tuple[str, dict]]) -> None:
    result = await get_current_time("Paris")
    assert result["status"] == "success"
    assert re.fullmatch(
        r"The current time in Paris, France is \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} CES?T\.",
        result["report"],
    )
    assert len(open_meteo) == 1, "Time needs geocoding only"


async def test_get_current_time_unknown_city(
    open_meteo: list[tuple[str, dict]],
) -> None:
    result = await get_current_time("Atlantis")
    assert result == {
        "status": "error",
        "error_message": "No timezone information available for 'Atlantis'.",
    }
