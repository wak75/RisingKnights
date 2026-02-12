"""Jenkins prompts package."""

from .troubleshooting import register_prompts as register_troubleshooting_prompts
from .best_practices import register_prompts as register_best_practices_prompts
from .templates import register_prompts as register_templates_prompts
from .security import register_prompts as register_security_prompts
from .migration import register_prompts as register_migration_prompts

def register_all_prompts(mcp):
    """Register all prompts with the MCP server."""
    register_troubleshooting_prompts(mcp)
    register_best_practices_prompts(mcp)
    register_templates_prompts(mcp)
    register_security_prompts(mcp)
    register_migration_prompts(mcp)