"""Configuration management for Orchestrator Agent."""

import os
import sys
from typing import Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def check_api_key():
    """Check if Google API key is configured and provide helpful instructions if not."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         🔑 GOOGLE API KEY REQUIRED                           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  To use the Orchestrator Agent, you need a FREE Google AI API key.           ║
║                                                                              ║
║  Get your API key in 30 seconds:                                             ║
║  1. Go to: https://aistudio.google.com/app/apikey                            ║
║  2. Click "Create API Key"                                                   ║
║  3. Copy the key                                                             ║
║                                                                              ║
║  Then set it using ONE of these methods:                                     ║
║                                                                              ║
║  Option 1 - Environment variable (temporary):                                ║
║    export GOOGLE_API_KEY="your-api-key-here"                                 ║
║                                                                              ║
║  Option 2 - .env file (recommended):                                         ║
║    1. Copy .env.example to .env                                              ║
║    2. Add your key: GOOGLE_API_KEY=your-api-key-here                         ║
║                                                                              ║
║  The API is FREE with generous limits (15 requests/minute for Gemini Flash)  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        sys.exit(1)
    return api_key


@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server."""
    
    name: str
    """Unique name identifier for the MCP server."""
    
    url: str
    """URL endpoint for the MCP server (e.g., http://localhost:8000/sse)."""
    
    transport: str = "sse"
    """Transport type: 'sse', 'stdio', 'streamable-http', or 'http'."""
    
    enabled: bool = True
    """Whether this MCP server is enabled."""
    
    description: str = ""
    """Description of what this MCP server provides."""
    
    headers: dict = field(default_factory=dict)
    """Optional HTTP headers for authentication (e.g., Authorization: Bearer token)."""


@dataclass
class OrchestratorConfig:
    """Main configuration for the Orchestrator Agent."""
    
    # Model configuration
    model_name: str = field(
        default_factory=lambda: os.getenv("ORCHESTRATOR_MODEL", "gemini-2.5-flash")
    )
    """The Gemini model to use for the orchestrator agent."""
    
    # Google AI configuration
    use_vertex_ai: bool = field(
        default_factory=lambda: os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "False").lower() == "true"
    )
    """Whether to use Vertex AI instead of public Gemini API."""
    
    # Server configuration
    host: str = field(
        default_factory=lambda: os.getenv("ORCHESTRATOR_HOST", "0.0.0.0")
    )
    """Host to bind the web API server."""
    
    port: int = field(
        default_factory=lambda: int(os.getenv("ORCHESTRATOR_PORT", "8080"))
    )
    """Port for the web API server."""
    
    # Agent configuration
    agent_name: str = "orchestrator_agent"
    """Name of the orchestrator agent."""
    
    agent_description: str = "An orchestrator agent that coordinates multiple MCP servers to accomplish complex tasks."
    """Description of the orchestrator agent."""
    
    # MCP Servers - extensible list
    mcp_servers: list[MCPServerConfig] = field(default_factory=list)
    """List of MCP servers to connect to."""
    
    def __post_init__(self):
        """Initialize MCP servers from environment or defaults."""
        if not self.mcp_servers:
            self.mcp_servers = self._load_mcp_servers()
        
        # Set environment variable for Vertex AI usage
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = str(self.use_vertex_ai)
    
    def _load_mcp_servers(self) -> list[MCPServerConfig]:
        """Load MCP server configurations."""
        servers = []
        
        # Jenkins MCP Server (default)
        jenkins_url = os.getenv("JENKINS_MCP_URL", "http://localhost:8000/sse")
        jenkins_enabled = os.getenv("JENKINS_MCP_ENABLED", "true").lower() == "true"
        
        if jenkins_enabled:
            servers.append(MCPServerConfig(
                name="jenkins",
                url=jenkins_url,
                transport="sse",
                enabled=True,
                description="Jenkins CI/CD server management - jobs, builds, nodes, plugins"
            ))
        
        # Kubernetes MCP Server
        k8s_url = os.getenv("KUBERNETES_MCP_URL", "")
        k8s_enabled = os.getenv("KUBERNETES_MCP_ENABLED", "false").lower() == "true"
        
        if k8s_enabled and k8s_url:
            servers.append(MCPServerConfig(
                name="kubernetes",
                url=k8s_url,
                transport="sse",
                enabled=True,
                description="Kubernetes cluster management - pods, deployments, services, configmaps, secrets, nodes, events, and more"
            ))
        
        # GitHub MCP Server (Remote HTTP)
        github_url = os.getenv("GITHUB_MCP_URL", "https://api.githubcopilot.com/mcp/")
        github_enabled = os.getenv("GITHUB_MCP_ENABLED", "false").lower() == "true"
        github_token = os.getenv("GITHUB_TOKEN", "")
        
        if github_enabled and github_token:
            servers.append(MCPServerConfig(
                name="github",
                url=github_url,
                transport="http",
                enabled=True,
                description="GitHub operations - repositories, issues, pull requests, commits, branches, releases",
                headers={"Authorization": f"Bearer {github_token}"}
            ))
        
        # Add more MCP servers here as needed...
        
        return servers
    
    def add_mcp_server(self, config: MCPServerConfig) -> None:
        """Add a new MCP server configuration."""
        # Check if server with same name already exists
        existing = next((s for s in self.mcp_servers if s.name == config.name), None)
        if existing:
            # Update existing configuration
            self.mcp_servers.remove(existing)
        self.mcp_servers.append(config)
    
    def remove_mcp_server(self, name: str) -> bool:
        """Remove an MCP server by name."""
        server = next((s for s in self.mcp_servers if s.name == name), None)
        if server:
            self.mcp_servers.remove(server)
            return True
        return False
    
    def get_enabled_servers(self) -> list[MCPServerConfig]:
        """Get list of enabled MCP servers."""
        return [s for s in self.mcp_servers if s.enabled]


# Global configuration instance
config = OrchestratorConfig()