# Coding Agent Guide

ADK quickstart: one agent (`weather_time_agent/agent.py`) with two tools,
`get_weather` and `get_current_time`, backed by the `CITIES` table.

## Workflow

1. Change the agent in `weather_time_agent/agent.py`; try it with `uv run adk web`.
2. Keep `tests/unit` in sync with the tools; run `uv run pytest tests/unit`.
3. Add eval cases to `tests/eval/datasets/basic-dataset.json` and run
   `agents-cli eval run`. Iterate until the scores hold.
4. `uv run pytest tests/integration` before calling a change done.

## Guidelines

- **Never change the model** unless explicitly asked (`AGENT_MODEL`, default `gemini-3.8-flash`).
- **Model 404 errors**: fix `GOOGLE_CLOUD_LOCATION` (e.g. `global`), not the model name.
- **Auth errors** (`RefreshError`): run `gcloud auth application-default login`.
- **Agent name**: `weather_time_agent` must match `root_agent_name` in `agents-cli-manifest.yaml`.
- **Run Python with uv**: `uv run ...`, after `uv sync --all-extras`.
- **No deployment here**: deploying requires `agents-cli scaffold enhance` and explicit user approval.
