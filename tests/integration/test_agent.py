"""Runs the real agent against the model: needs credentials from .env."""

from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from google.genai import types

from weather_time_agent.agent import app

load_dotenv()


def test_agent_answers_with_tool() -> None:
    runner = InMemoryRunner(app=app)
    session = runner.session_service.create_session_sync(
        app_name=app.name, user_id="test_user"
    )
    message = types.Content(
        role="user", parts=[types.Part.from_text(text="What's the weather in Paris?")]
    )

    events = list(
        runner.run(user_id="test_user", session_id=session.id, new_message=message)
    )

    calls = [call.name for event in events for call in event.get_function_calls()]
    assert "get_weather" in calls, f"Expected a get_weather call, got {calls}"

    final_text = "".join(
        part.text or ""
        for event in events
        if event.is_final_response() and event.content
        for part in event.content.parts or []
    )
    assert "°C" in final_text, f"Expected a temperature, got {final_text!r}"
