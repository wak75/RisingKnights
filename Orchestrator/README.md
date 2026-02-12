# Orchestrator Agent

A Google ADK-based orchestrator agent that coordinates multiple MCP (Model Context Protocol) servers to accomplish complex CI/CD and infrastructure tasks.

## Features

- 🤖 **Gemini 2.5 Flash** - Powered by Google's latest AI model
- 🔌 **MCP Integration** - Connects to multiple MCP servers (Jenkins, Kubernetes, etc.)
- 🖥️ **CLI Interface** - Interactive chat for local use
- 🌐 **Web API** - RESTful API for programmatic access
- 🔧 **Extensible** - Easy to add new MCP servers

## Quick Start

### 1. Install Dependencies

```bash
cd Orchestrator
pip install -e .
```

Or using uv:

```bash
cd Orchestrator
uv pip install -e .
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Google API key
# Get one at: https://aistudio.google.com/app/apikey
```

### 3. Start the Jenkins MCP Server

Make sure the Jenkins MCP server is running:

```bash
cd ../Jenkins_MCP
pip install -e .
jenkins-mcp-server
```

### 4. Run the Orchestrator

**CLI Mode (default):**
```bash
orchestrator
# or
orchestrator cli
```

**Web API Mode:**
```bash
orchestrator serve
```

## Usage

### CLI Interface

```
┌─────────────────────────────────────────────────┐
│ Orchestrator Agent CLI                          │
│ An intelligent agent for orchestrating MCP      │
│ Type 'quit' or 'exit' to stop, 'help' for cmds  │
└─────────────────────────────────────────────────┘

You: List all Jenkins jobs

Agent: I'll retrieve the list of Jenkins jobs for you...
```

**CLI Commands:**
- `quit` / `exit` / `q` - Exit the CLI
- `help` - Show available commands
- `servers` - List connected MCP servers
- `new` - Start a new conversation session

### Web API

The web API runs on `http://localhost:8080` by default.

**Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/chat` | Send a message to the agent |
| GET | `/servers` | List configured MCP servers |

**Example API Call:**

```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "List all Jenkins jobs"}'
```

**Response:**
```json
{
  "response": "Here are the Jenkins jobs...",
  "user_id": "user_abc123",
  "session_id": "session_def456"
}
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | - | Your Google AI API key (required) |
| `GOOGLE_GENAI_USE_VERTEXAI` | `False` | Use Vertex AI instead of public API |
| `ORCHESTRATOR_MODEL` | `gemini-2.5-flash` | Gemini model to use |
| `ORCHESTRATOR_HOST` | `0.0.0.0` | Web API host |
| `ORCHESTRATOR_PORT` | `8080` | Web API port |
| `JENKINS_MCP_URL` | `http://localhost:8000/sse` | Jenkins MCP server URL |
| `JENKINS_MCP_ENABLED` | `true` | Enable Jenkins MCP |
| `KUBERNETES_MCP_URL` | - | Kubernetes MCP server URL |
| `KUBERNETES_MCP_ENABLED` | `false` | Enable Kubernetes MCP |

## Adding New MCP Servers

The orchestrator is designed to be easily extensible. To add a new MCP server:

### 1. Add Environment Variables

In your `.env` file:
```bash
NEWSERVER_MCP_URL=http://localhost:8002/sse
NEWSERVER_MCP_ENABLED=true
```

### 2. Update Configuration

In `src/orchestrator/config.py`, add to the `_load_mcp_servers` method:

```python
# New Server MCP
newserver_url = os.getenv("NEWSERVER_MCP_URL", "")
newserver_enabled = os.getenv("NEWSERVER_MCP_ENABLED", "false").lower() == "true"

if newserver_enabled and newserver_url:
    servers.append(MCPServerConfig(
        name="newserver",
        url=newserver_url,
        transport="sse",
        enabled=True,
        description="Description of what this MCP server provides"
    ))
```

### 3. Restart the Orchestrator

The agent will automatically connect to the new MCP server and make its tools available.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator Agent                        │
│                   (Google ADK + Gemini)                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Jenkins   │  │ Kubernetes  │  │   GitHub    │   ...    │
│  │     MCP     │  │     MCP     │  │     MCP     │          │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │
│         │                │                │                  │
│         └────────────────┼────────────────┘                  │
│                          │                                   │
│                    ┌─────┴─────┐                             │
│                    │    SSE    │                             │
│                    │ Transport │                             │
│                    └───────────┘                             │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  CLI Interface          │           Web API (FastAPI)        │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
Orchestrator/
├── pyproject.toml           # Project dependencies
├── .env.example             # Environment template
├── README.md                # This file
└── src/
    └── orchestrator/
        ├── __init__.py      # Package init
        ├── config.py        # Configuration management
        ├── agent.py         # Orchestrator agent definition
        └── main.py          # CLI and Web API entry point
```

## Development

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Format Code

```bash
black src/
ruff check src/ --fix
```

## Troubleshooting

### Agent fails to connect to MCP server

1. Ensure the MCP server is running
2. Check the MCP server URL in your `.env` file
3. Verify the MCP server is using SSE transport

### "No response from agent"

1. Check your `GOOGLE_API_KEY` is valid
2. Ensure you have API quota available
3. Check the model name is correct

### Connection timeout

1. Increase timeout in MCP server configuration
2. Check network connectivity between orchestrator and MCP servers

## License

MIT