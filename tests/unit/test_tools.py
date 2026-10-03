"""Unit tests for the agent's tools — no LLM calls."""

import re

from weather_time_agent.agent import get_current_time, get_weather


def test_get_weather_known_city() -> None:
    result = get_weather("Paris")
    assert result["status"] == "success"
    assert result["report"] == "The weather in Paris is partly cloudy, 19 °C (66 °F)."


def test_get_weather_is_case_and_space_insensitive() -> None:
    assert get_weather("  new YORK ")["status"] == "success"


def test_get_weather_unknown_city() -> None:
    result = get_weather("Atlantis")
    assert result["status"] == "error"
    assert "Atlantis" in result["error_message"]
    assert "Paris" in result["error_message"]


def test_get_current_time_known_city() -> None:
    result = get_current_time("Tokyo")
    assert result["status"] == "success"
    assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} JST", result["report"])


def test_get_current_time_unknown_city() -> None:
    result = get_current_time("Atlantis")
    assert result["status"] == "error"
    assert "timezone" in result["error_message"]
