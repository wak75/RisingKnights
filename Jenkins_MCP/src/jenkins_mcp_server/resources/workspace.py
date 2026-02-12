"""Jenkins workspace file resources."""

from typing import Any, Dict, Optional, Callable
from urllib.parse import unquote

from ..utils import (
    get_logger,
    validate_job_name,
    validate_file_path,
    JenkinsNotFoundError,
)


logger = get_logger("resources.workspace")


def register_resources(mcp, get_client: Callable):
    """Register workspace file resources with the MCP server."""
    
    @mcp.resource("jenkins://job/{job_name}/workspace")
    async def get_workspace_info(job_name: str) -> str:
        """
        Get information about the workspace for a job.
        
        Args:
            job_name: The name of the Jenkins job
            
        Returns:
            Formatted string containing workspace information
        """
        try:
            name = validate_job_name(unquote(job_name))
            client = get_client()
            
            # Get job info to verify it exists
            job_info = client.get_job_info(name)
            
            # Format workspace information
            output = f"Jenkins Workspace Information\n"
            output += f"Job: {name}\n"
            output += "=" * 40 + "\n\n"
            
            output += f"Job URL: {job_info.get('url', 'N/A')}\n"
            output += f"Workspace URL: {job_info.get('url', 'N/A')}ws/\n"
            
            # Note about workspace access
            output += "\nNote: Workspace file access requires additional Jenkins configuration\n"
            output += "and appropriate permissions. Consider using the Jenkins web interface\n"
            output += "or Jenkins CLI for direct workspace file access.\n"
            
            # Show recent builds that might have workspace changes
            if job_info.get('builds'):
                output += f"\nRecent Builds (may have workspace files):\n"
                for build in job_info['builds'][:5]:
                    output += f"  #{build.get('number', 'N/A')} - {build.get('url', 'N/A')}\n"
            
            return output
            
        except JenkinsNotFoundError:
            raise ValueError(f"Job '{job_name}' not found")
        except Exception as e:
            logger.error(f"Failed to get workspace info for '{job_name}': {e}")
            raise ValueError(f"Failed to get workspace info: {e}")
    
    @mcp.resource("jenkins://job/{job_name}/workspace/{file_path}")
    async def get_workspace_file(job_name: str, file_path: str) -> str:
        """
        Get content of a file from the job workspace.
        
        Args:
            job_name: The name of the Jenkins job
            file_path: Path to the file within the workspace
            
        Returns:
            File content as string
        """
        try:
            name = validate_job_name(unquote(job_name))
            path = validate_file_path(unquote(file_path))
            client = get_client()
            
            # Verify job exists
            job_info = client.get_job_info(name)
            
            # Note: This is a placeholder implementation
            # Full implementation would require additional Jenkins API calls
            # or custom HTTP requests to the workspace endpoint
            
            output = f"Workspace File Access\n"
            output += f"Job: {name}\n"
            output += f"File: {path}\n"
            output += "=" * 40 + "\n\n"
            
            output += "Direct workspace file access is not implemented in this version.\n"
            output += "To access workspace files:\n\n"
            output += f"1. Visit: {job_info.get('url', 'N/A')}ws/{path}\n"
            output += "2. Use Jenkins CLI: jenkins-cli.jar get-job-workspace\n"
            output += "3. Use Jenkins API with appropriate authentication\n"
            
            return output
            
        except JenkinsNotFoundError:
            raise ValueError(f"Job '{job_name}' not found")
        except Exception as e:
            logger.error(f"Failed to get workspace file '{file_path}' for '{job_name}': {e}")
            raise ValueError(f"Failed to get workspace file: {e}")