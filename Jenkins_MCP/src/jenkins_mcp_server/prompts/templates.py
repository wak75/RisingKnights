"""Jenkins pipeline and configuration templates."""


def register_prompts(mcp):
    """Register template prompts with the MCP server."""
    
    @mcp.prompt("jenkins_pipeline_templates")
    async def pipeline_templates() -> str:
        """Provide common Jenkins pipeline templates."""
        return "# Jenkins Pipeline Templates\n\nBasic pipeline examples for Jenkins automation."

    @mcp.prompt("jenkins_best_practices")
    async def best_practices() -> str:
        """Provide Jenkins best practices."""
        return "# Jenkins Best Practices\n\nKey guidelines for Jenkins usage."

    @mcp.prompt("jenkins_troubleshooting")
    async def troubleshooting_guide() -> str:
        """Provide Jenkins troubleshooting guide."""
        return "# Jenkins Troubleshooting\n\nCommon issues and solutions."
