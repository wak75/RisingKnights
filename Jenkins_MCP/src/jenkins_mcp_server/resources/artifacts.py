"""Jenkins build artifacts resources."""

from typing import Any, Dict, Optional, Callable
from urllib.parse import unquote

from ..utils import (
    get_logger,
    validate_job_name,
    validate_build_number,
    JenkinsNotFoundError,
)


logger = get_logger("resources.artifacts")


def register_resources(mcp, get_client: Callable):
    """Register build artifact resources with the MCP server."""
    
    @mcp.resource("jenkins://build/{job_name}/{build_number}/artifacts")
    async def get_build_artifacts_list(job_name: str, build_number: str) -> str:
        """
        Get a formatted list of artifacts for a specific build.
        
        Args:
            job_name: The name of the Jenkins job
            build_number: The build number
            
        Returns:
            Formatted string containing artifact information
        """
        try:
            name = validate_job_name(unquote(job_name))
            number = validate_build_number(int(build_number))
            client = get_client()
            
            build_info = client.get_build_info(name, number)
            
            # Format artifacts list
            output = f"Build Artifacts\n"
            output += f"Job: {name} | Build: #{number}\n"
            output += "=" * 40 + "\n\n"
            
            if not build_info.get('artifacts'):
                output += "No artifacts found for this build.\n"
            else:
                for artifact in build_info['artifacts']:
                    output += f"File: {artifact.get('fileName', 'N/A')}\n"
                    output += f"  Path: {artifact.get('relativePath', 'N/A')}\n"
                    output += f"  Display Path: {artifact.get('displayPath', 'N/A')}\n"
                    output += f"  Download URL: {build_info['url']}artifact/{artifact.get('relativePath', '')}\n"
                    output += "\n"
                
                output += f"Total Artifacts: {len(build_info['artifacts'])}\n"
            
            return output
            
        except JenkinsNotFoundError:
            raise ValueError(f"Build #{build_number} for job '{job_name}' not found")
        except Exception as e:
            logger.error(f"Failed to get artifacts for '{job_name}' #{build_number}: {e}")
            raise ValueError(f"Failed to get artifacts: {e}")
    
    @mcp.resource("jenkins://job/{job_name}/lastSuccessfulBuild/artifacts")
    async def get_last_successful_build_artifacts(job_name: str) -> str:
        """
        Get artifacts from the last successful build of a job.
        
        Args:
            job_name: The name of the Jenkins job
            
        Returns:
            Formatted string containing artifact information
        """
        try:
            name = validate_job_name(unquote(job_name))
            client = get_client()
            
            job_info = client.get_job_info(name)
            
            if not job_info.get('lastSuccessfulBuild'):
                raise ValueError(f"No successful builds found for job '{job_name}'")
            
            build_number = job_info['lastSuccessfulBuild']['number']
            build_info = client.get_build_info(name, build_number)
            
            # Format artifacts list
            output = f"Last Successful Build Artifacts\n"
            output += f"Job: {name} | Build: #{build_number}\n"
            output += "=" * 50 + "\n\n"
            
            if not build_info.get('artifacts'):
                output += "No artifacts found for the last successful build.\n"
            else:
                for artifact in build_info['artifacts']:
                    output += f"File: {artifact.get('fileName', 'N/A')}\n"
                    output += f"  Path: {artifact.get('relativePath', 'N/A')}\n"
                    output += f"  Download URL: {build_info['url']}artifact/{artifact.get('relativePath', '')}\n"
                    output += "\n"
                
                output += f"Total Artifacts: {len(build_info['artifacts'])}\n"
            
            return output
            
        except JenkinsNotFoundError:
            raise ValueError(f"Job '{job_name}' not found")
        except Exception as e:
            logger.error(f"Failed to get last successful build artifacts for '{job_name}': {e}")
            raise ValueError(f"Failed to get last successful build artifacts: {e}")