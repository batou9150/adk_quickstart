"""The classic ADK demo agent: weather and current time for a city.

Both tools resolve the city with Open-Meteo's geocoding API, and the weather
comes from its forecast API. Open-Meteo is free for non-commercial use and
needs no API key: https://open-meteo.com/
"""

import datetime
import os
from zoneinfo import ZoneInfo

import httpx
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

MODEL = os.environ.get("AGENT_MODEL", "gemini-3.8-flash")

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT = httpx.Timeout(10.0)
MAX_FORECAST_DAYS = 16  # Open-Meteo rejects anything longer

# WMO weather interpretation codes, as returned in `weather_code`.
WMO_CODES: dict[int, str] = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    56: "light freezing drizzle",
    57: "dense freezing drizzle",
    61: "slight rain",
    63: "moderate rain",
    65: "heavy rain",
    66: "light freezing rain",
    67: "heavy freezing rain",
    71: "slight snowfall",
    73: "moderate snowfall",
    75: "heavy snowfall",
    77: "snow grains",
    80: "slight rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    85: "slight snow showers",
    86: "heavy snow showers",
    95: "thunderstorm",
    96: "thunderstorm with slight hail",
    99: "thunderstorm with heavy hail",
}


async def _get_json(url: str, params: dict) -> dict:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


async def _geocode(city: str) -> dict | None:
    """The best Open-Meteo match for `city`, or None when there is none."""
    data = await _get_json(
        GEOCODING_URL, {"name": city.strip(), "count": 1, "language": "en"}
    )
    results = data.get("results") or []
    return results[0] if results else None


def _place_name(place: dict) -> str:
    return ", ".join(p for p in (place.get("name"), place.get("country")) if p)


def _error(message: str) -> dict:
    return {"status": "error", "error_message": message}


async def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city.

    Args:
        city: The name of the city, for example "Paris".

    Returns:
        A dict with status "success" and a "report", or status "error" and an
        "error_message".
    """
    try:
        place = await _geocode(city)
        if place is None:
            return _error(f"No location found for '{city}'.")
        data = await _get_json(
            FORECAST_URL,
            {
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m",
                "timezone": "auto",
            },
        )
    except httpx.HTTPError as exc:
        return _error(f"The weather service is unavailable: {exc}")

    current = data["current"]
    conditions = WMO_CODES.get(current["weather_code"], "unknown conditions")
    return {
        "status": "success",
        "report": (
            f"The weather in {_place_name(place)} is {conditions}, "
            f"{current['temperature_2m']} °C (feels like {current['apparent_temperature']} °C), "
            f"humidity {current['relative_humidity_2m']}%, "
            f"wind {current['wind_speed_10m']} km/h."
        ),
    }


async def get_forecast(city: str, days: int) -> dict:
    """Retrieves the daily weather forecast for a specified city.

    Args:
        city: The name of the city, for example "Paris".
        days: How many days to forecast, starting today: 1 for today only, 2 to
            include tomorrow, up to 16.

    Returns:
        A dict with status "success" and a "report" with one line per day, or
        status "error" and an "error_message".
    """
    if not 1 <= days <= MAX_FORECAST_DAYS:
        return _error(
            f"Can only forecast between 1 and {MAX_FORECAST_DAYS} days, not {days}."
        )
    try:
        place = await _geocode(city)
        if place is None:
            return _error(f"No location found for '{city}'.")
        data = await _get_json(
            FORECAST_URL,
            {
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum",
                "forecast_days": days,
                "timezone": "auto",
            },
        )
    except httpx.HTTPError as exc:
        return _error(f"The weather service is unavailable: {exc}")

    daily = data["daily"]
    lines = [f"Forecast for {_place_name(place)}:"]
    for i, day in enumerate(daily["time"]):
        date = datetime.date.fromisoformat(day)
        conditions = WMO_CODES.get(daily["weather_code"][i], "unknown conditions")
        lines.append(
            f"- {date:%A %Y-%m-%d}: {conditions}, "
            f"{daily['temperature_2m_min'][i]} to {daily['temperature_2m_max'][i]} °C, "
            f"{daily['precipitation_probability_max'][i]}% chance of precipitation "
            f"({daily['precipitation_sum'][i]} mm)."
        )
    return {"status": "success", "report": "\n".join(lines)}


async def get_current_time(city: str) -> dict:
    """Returns the current local time in a specified city.

    Args:
        city: The name of the city, for example "Paris".

    Returns:
        A dict with status "success" and a "report", or status "error" and an
        "error_message".
    """
    try:
        place = await _geocode(city)
    except httpx.HTTPError as exc:
        return _error(f"The geocoding service is unavailable: {exc}")
    if place is None or not place.get("timezone"):
        return _error(f"No timezone information available for '{city}'.")

    now = datetime.datetime.now(ZoneInfo(place["timezone"]))
    return {
        "status": "success",
        "report": f"The current time in {_place_name(place)} is {now.strftime('%Y-%m-%d %H:%M:%S %Z')}.",
    }


root_agent = Agent(
    # Keep in sync with root_agent_name in agents-cli-manifest.yaml.
    name="weather_time_agent",
    model=Gemini(model=MODEL, retry_options=types.HttpRetryOptions(attempts=3)),
    description="Answers questions about the weather, the forecast and the current time in a city.",
    instruction=(
        "You are a concise assistant that reports the weather, the forecast and the "
        "current time for a city. Use get_weather for current conditions, "
        "get_forecast for upcoming days and get_current_time for the local time; "
        "never guess. To know which days to request, remember that get_forecast "
        "starts today: tomorrow needs days=2, and when the user gives no range "
        "use 3. "
        "Each tool reports the place it resolved the city to; mention it so the "
        "user can spot a wrong match. "
        "If a tool returns an error, relay its error_message verbatim. "
        "If the user names no city, ask which one."
    ),
    tools=[get_weather, get_forecast, get_current_time],
)

app = App(root_agent=root_agent, name="weather_time_agent")
