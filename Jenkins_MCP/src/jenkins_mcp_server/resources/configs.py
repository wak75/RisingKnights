"""Jenkins job configuration resources."""

from typing import Any, Dict, Optional, Callable
from urllib.parse import unquote

from ..utils import (
    get_logger,
    validate_job_name,
    JenkinsNotFoundError,
)


logger = get_logger("resources.configs")


def register_resources(mcp, get_client: Callable):
    """Register job configuration resources with the MCP server."""
    
    @mcp.resource("jenkins://job/{name}/config")
    async def get_job_config(name: str) -> str:
        """
        Get the XML configuration for a Jenkins job.
        
        Args:
            name: The name of the Jenkins job
            
        Returns:
            XML configuration string
        """
        try:
            # URL decode the job name
            job_name = validate_job_name(unquote(name))
            client = get_client()
            
            config_xml = client.get_job_config(job_name)
            return config_xml
            
        except JenkinsNotFoundError:
            raise ValueError(f"Job '{name}' not found")
        except Exception as e:
            logger.error(f"Failed to get job config for '{name}': {e}")
            raise ValueError(f"Failed to get job config: {e}")
    
    @mcp.resource("jenkins://jobs/list")
    async def get_jobs_list() -> str:
        """
        Get a formatted list of all Jenkins jobs.
        
        Returns:
            Formatted string containing job information
        """
        try:
            client = get_client()
            jobs = client.get_jobs()
            
            # Format jobs list
            output = "Jenkins Jobs Summary\n"
            output += "=" * 50 + "\n\n"
            
            if not jobs:
                output += "No jobs found.\n"
            else:
                for job in jobs:
                    output += f"Job: {job.get('name', 'Unknown')}\n"
                    output += f"  URL: {job.get('url', 'N/A')}\n"
                    output += f"  Status: {job.get('color', 'unknown')}\n"
                    output += f"  Buildable: {job.get('buildable', False)}\n"
                    
                    if job.get('lastBuild'):
                        output += f"  Last Build: #{job['lastBuild'].get('number', 'N/A')}\n"
                    
                    output += "\n"
                
                output += f"\nTotal Jobs: {len(jobs)}\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Failed to get jobs list: {e}")
            raise ValueError(f"Failed to get jobs list: {e}")
    
    @mcp.resource("jenkins://job/{name}/info")
    async def get_job_info_resource(name: str) -> str:
        """
        Get formatted information about a Jenkins job.
        
        Args:
            name: The name of the Jenkins job
            
        Returns:
            Formatted string containing job information
        """
        try:
            job_name = validate_job_name(unquote(name))
            client = get_client()
            
            job_info = client.get_job_info(job_name)
            
            # Format job information
            output = f"Jenkins Job Information: {job_name}\n"
            output += "=" * (30 + len(job_name)) + "\n\n"
            
            output += f"Name: {job_info.get('name', 'N/A')}\n"
            output += f"Display Name: {job_info.get('displayName', 'N/A')}\n"
            output += f"Description: {job_info.get('description', 'No description')}\n"
            output += f"URL: {job_info.get('url', 'N/A')}\n"
            output += f"Buildable: {job_info.get('buildable', False)}\n"
            output += f"Color: {job_info.get('color', 'unknown')}\n"
            output += f"Disabled: {job_info.get('disabled', False)}\n"
            output += f"In Queue: {job_info.get('inQueue', False)}\n"
            output += f"Next Build Number: {job_info.get('nextBuildNumber', 'N/A')}\n"
            
            # Last build info
            if job_info.get('lastBuild'):
                last_build = job_info['lastBuild']
                output += f"\nLast Build:\n"
                output += f"  Number: #{last_build.get('number', 'N/A')}\n"
                output += f"  URL: {last_build.get('url', 'N/A')}\n"
            
            # Recent builds
            if job_info.get('builds'):
                output += f"\nRecent Builds:\n"
                for build in job_info['builds'][:5]:  # Show last 5 builds
                    output += f"  #{build.get('number', 'N/A')} - {build.get('url', 'N/A')}\n"
            
            # Health report
            if job_info.get('healthReport'):
                output += f"\nHealth Report:\n"
                for report in job_info['healthReport']:
                    output += f"  Score: {report.get('score', 'N/A')}/100\n"
                    output += f"  Description: {report.get('description', 'N/A')}\n"
            
            return output
            
        except JenkinsNotFoundError:
            raise ValueError(f"Job '{name}' not found")
        except Exception as e:
            logger.error(f"Failed to get job info for '{name}': {e}")
            raise ValueError(f"Failed to get job info: {e}")