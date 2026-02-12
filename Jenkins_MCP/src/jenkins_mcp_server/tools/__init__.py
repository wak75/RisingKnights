"""Jenkins MCP Server Tools."""

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from fastmcp import FastMCP

from . import jobs
from . import builds
from . import nodes
from . import plugins
from . import system
from . import users

# Alias for easier imports
jobs_tools = jobs
builds_tools = builds
nodes_tools = nodes
plugins_tools = plugins
system_tools = system
users_tools = users


def register_all_tools(mcp: "FastMCP", get_client: Callable) -> None:
    """Register all tools with the FastMCP server.
    
    Args:
        mcp: The FastMCP server instance
        get_client: Function to get Jenkins client instance
    """
    # Register tools from each module
    if hasattr(jobs, 'register_tools'):
        jobs.register_tools(mcp, get_client)
    if hasattr(builds, 'register_tools'):
        builds.register_tools(mcp, get_client)
    if hasattr(nodes, 'register_tools'):
        nodes.register_tools(mcp, get_client)
    if hasattr(plugins, 'register_tools'):
        plugins.register_tools(mcp, get_client)
    if hasattr(system, 'register_tools'):
        system.register_tools(mcp, get_client)
    if hasattr(users, 'register_tools'):
        users.register_tools(mcp, get_client)


__all__ = [
    "jobs_tools",
    "builds_tools", 
    "nodes_tools",
    "plugins_tools",
    "system_tools",
    "users_tools",
    "register_all_tools",
]