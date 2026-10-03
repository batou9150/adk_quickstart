"""The classic ADK demo agent: weather and current time for a city."""

import datetime
import os
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

MODEL = os.environ.get("AGENT_MODEL", "gemini-3.8-flash")

# city -> (IANA timezone, canned weather)
CITIES: dict[str, tuple[str, str]] = {
    "new york": ("America/New_York", "sunny, 25 °C (77 °F)"),
    "london": ("Europe/London", "overcast with light rain, 14 °C (57 °F)"),
    "paris": ("Europe/Paris", "partly cloudy, 19 °C (66 °F)"),
    "berlin": ("Europe/Berlin", "clear, 17 °C (63 °F)"),
    "madrid": ("Europe/Madrid", "hot and dry, 31 °C (88 °F)"),
    "tokyo": ("Asia/Tokyo", "humid with scattered showers, 27 °C (81 °F)"),
}


def _unknown_city(city: str, what: str) -> dict:
    return {
        "status": "error",
        "error_message": (
            f"No {what} information available for '{city}'. "
            f"Known cities: {', '.join(c.title() for c in sorted(CITIES))}."
        ),
    }


def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city.

    Args:
        city: The name of the city, for example "Paris".

    Returns:
        A dict with status "success" and a "report", or status "error" and an
        "error_message".
    """
    entry = CITIES.get(city.strip().lower())
    if entry is None:
        return _unknown_city(city, "weather")
    return {
        "status": "success",
        "report": f"The weather in {city.strip().title()} is {entry[1]}.",
    }


def get_current_time(city: str) -> dict:
    """Returns the current local time in a specified city.

    Args:
        city: The name of the city, for example "Paris".

    Returns:
        A dict with status "success" and a "report", or status "error" and an
        "error_message".
    """
    entry = CITIES.get(city.strip().lower())
    if entry is None:
        return _unknown_city(city, "timezone")
    now = datetime.datetime.now(ZoneInfo(entry[0]))
    return {
        "status": "success",
        "report": f"The current time in {city.strip().title()} is {now.strftime('%Y-%m-%d %H:%M:%S %Z')}.",
    }


root_agent = Agent(
    # Keep in sync with root_agent_name in agents-cli-manifest.yaml.
    name="weather_time_agent",
    model=Gemini(model=MODEL, retry_options=types.HttpRetryOptions(attempts=3)),
    description="Answers questions about the weather and the current time in a city.",
    instruction=(
        "You are a concise assistant that reports the weather and the current time "
        "for a city. Use the get_weather and get_current_time tools; never guess. "
        "If a tool returns an error, relay its error_message verbatim. "
        "If the user names no city, ask which one."
    ),
    tools=[get_weather, get_current_time],
)

app = App(root_agent=root_agent, name="weather_time_agent")
