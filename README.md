# ADK Quickstart 🚀

Welcome to ADK Quickstart ! This project provides a basic template and example to help you get started with building and deploying your own AI agents using Agent Development Kit (ADK).

ADK is a **flexible and modular framework** designed to simplify the development and deployment of AI agents. While optimized for Gemini and the Google ecosystem, ADK is **model-agnostic**, **deployment-agnostic**, and built for **compatibility with other frameworks**. It aims to make agent development feel more like traditional software development, enabling you to create, deploy, and orchestrate everything from simple agentic tasks to complex workflows.

-----

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

  * Python (version 3.9+)
  * Access to a Google Cloud project with Vertex AI APIs enabled.


### Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/batou9150/adk_quickstart.git
    cd adk_quickstart
    ```

2.  **Install dependencies using Poetry:**

    ```bash
    poetry install
    ```

3.  **Set up Google Cloud credentials:**

    * At the top directory `multi_tool_agent/`, make a .env by copying .env.example
    ```bash
    cp .env.example .env
    # Open .env and add your configurations
    ```

    * Set the following environment variables.
    ```
    # Choose Model Backend: FALSE -> AI Studio, TRUE -> Vertex AI
    GOOGLE_GENAI_USE_VERTEXAI=TRUE

    # Vertex backend config
    GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
    GOOGLE_CLOUD_LOCATION=LOCATION
    ```

4.  **Activate the virtual environment set up by Poetry, run:**

    ```bash
    eval $(poetry env activate)
    ```

### Running the Example Agent

To run the example agent, execute the main script:

```bash
adk web
```

Try the following inputs : 
* `What time is it in New York?`
* `Is it raining in New York?`


## Deploy to Agent Engine

```python
from multi_tool_agent.agent import root_agent
import vertexai
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import AdkApp

vertexai.init(
    project="YOUR_PROJECT_ID",
    location="LOCATION",
    staging_bucket=f"gs://BUCKET_NAME",
)

app = AdkApp(
    agent=root_agent,
    enable_tracing=True,
)

remote_app = agent_engines.create(
    app,
    display_name="Weather & Time Agent",
    description="A basic multi-tool agent",
    requirements=[
        "google-adk (>=1.2.0,<2.0.0)",
        "google-cloud-aiplatform[adk,agent_engines] (>=1.96.0,<2.0.0)",
        "google-genai (>=1.5.0,<2.0.0)",
        "pydantic (>=2.10.6,<3.0.0)",
        "cloudpickle (>=3.1.1)",
    ],
    extra_packages=[
        "./multi_tool_agent",  # The main package
    ],
)
```

Test the remote agent :
```python
# remote_app = agent_engines.get('RESSOURCE_ID')
remote_session = remote_app.create_session(user_id='u_123')
remote_session

for event in remote_app.stream_query(
    user_id="u_123",
    session_id=remote_session["id"],
    message="whats the weather in new york",
):
    print(event)
```
