"""Jenkins MCP Server Resources."""

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from fastmcp import FastMCP

from . import configs
from . import logs  
from . import artifacts
from . import workspace
from . import metrics

# Alias for easier imports
configs_resources = configs
logs_resources = logs
artifacts_resources = artifacts
workspace_resources = workspace
metrics_resources = metrics


def register_all_resources(mcp: "FastMCP", get_client: Callable) -> None:
    """Register all resources with the FastMCP server.
    
    Args:
        mcp: The FastMCP server instance
        get_client: Function to get Jenkins client instance
    """
    # Register resources from each module
    if hasattr(configs, 'register_resources'):
        configs.register_resources(mcp, get_client)
    if hasattr(logs, 'register_resources'):
        logs.register_resources(mcp, get_client)
    if hasattr(artifacts, 'register_resources'):
        artifacts.register_resources(mcp, get_client)
    if hasattr(workspace, 'register_resources'):
        workspace.register_resources(mcp, get_client)
    if hasattr(metrics, 'register_resources'):
        metrics.register_resources(mcp, get_client)


__all__ = [
    "configs_resources",
    "logs_resources",
    "artifacts_resources", 
    "workspace_resources",
    "metrics_resources",
    "register_all_resources",
]