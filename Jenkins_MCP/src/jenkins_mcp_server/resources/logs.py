"""Jenkins build log resources."""

from typing import Any, Dict, Optional, Callable
from urllib.parse import unquote

from ..utils import (
    get_logger,
    validate_job_name,
    validate_build_number,
    JenkinsNotFoundError,
)


logger = get_logger("resources.logs")


def register_resources(mcp, get_client: Callable):
    """Register build log resources with the MCP server."""
    
    @mcp.resource("jenkins://build/{job_name}/{build_number}/log")
    async def get_build_log(job_name: str, build_number: str) -> str:
        """
        Get the console output log for a specific build.
        
        Args:
            job_name: The name of the Jenkins job
            build_number: The build number
            
        Returns:
            Console output log as string
        """
        try:
            name = validate_job_name(unquote(job_name))
            number = validate_build_number(int(build_number))
            client = get_client()
            
            log_content = client.get_build_console_output(name, number)
            return log_content
            
        except JenkinsNotFoundError:
            raise ValueError(f"Build #{build_number} for job '{job_name}' not found")
        except Exception as e:
            logger.error(f"Failed to get build log for '{job_name}' #{build_number}: {e}")
            raise ValueError(f"Failed to get build log: {e}")
    
    @mcp.resource("jenkins://build/{job_name}/{build_number}/log/tail")
    async def get_build_log_tail(job_name: str, build_number: str) -> str:
        """
        Get the last 100 lines of console output for a specific build.
        
        Args:
            job_name: The name of the Jenkins job
            build_number: The build number
            
        Returns:
            Last 100 lines of console output
        """
        try:
            name = validate_job_name(unquote(job_name))
            number = validate_build_number(int(build_number))
            client = get_client()
            
            log_content = client.get_build_console_output(name, number)
            
            # Get last 100 lines
            lines = log_content.split('\n')
            tail_lines = lines[-100:] if len(lines) > 100 else lines
            
            return '\n'.join(tail_lines)
            
        except JenkinsNotFoundError:
            raise ValueError(f"Build #{build_number} for job '{job_name}' not found")
        except Exception as e:
            logger.error(f"Failed to get build log tail for '{job_name}' #{build_number}: {e}")
            raise ValueError(f"Failed to get build log tail: {e}")
    
    @mcp.resource("jenkins://job/{job_name}/lastBuild/log")
    async def get_last_build_log(job_name: str) -> str:
        """
        Get the console output log for the last build of a job.
        
        Args:
            job_name: The name of the Jenkins job
            
        Returns:
            Console output log as string
        """
        try:
            name = validate_job_name(unquote(job_name))
            client = get_client()
            
            # Get job info to find last build number
            job_info = client.get_job_info(name)
            
            if not job_info.get('lastBuild'):
                raise ValueError(f"No builds found for job '{job_name}'")
            
            last_build_number = job_info['lastBuild']['number']
            log_content = client.get_build_console_output(name, last_build_number)
            
            return log_content
            
        except JenkinsNotFoundError:
            raise ValueError(f"Job '{job_name}' not found")
        except Exception as e:
            logger.error(f"Failed to get last build log for '{job_name}': {e}")
            raise ValueError(f"Failed to get last build log: {e}")
    
    @mcp.resource("jenkins://build/{job_name}/{build_number}/info")
    async def get_build_info_resource(job_name: str, build_number: str) -> str:
        """
        Get formatted information about a specific build.
        
        Args:
            job_name: The name of the Jenkins job
            build_number: The build number
            
        Returns:
            Formatted string containing build information
        """
        try:
            name = validate_job_name(unquote(job_name))
            number = validate_build_number(int(build_number))
            client = get_client()
            
            build_info = client.get_build_info(name, number)
            
            # Format build information
            output = f"Jenkins Build Information\n"
            output += f"Job: {name} | Build: #{number}\n"
            output += "=" * 50 + "\n\n"
            
            output += f"Build Number: #{build_info.get('number', 'N/A')}\n"
            output += f"Display Name: {build_info.get('displayName', 'N/A')}\n"
            output += f"Full Display Name: {build_info.get('fullDisplayName', 'N/A')}\n"
            output += f"URL: {build_info.get('url', 'N/A')}\n"
            output += f"Result: {build_info.get('result', 'N/A')}\n"
            output += f"Building: {build_info.get('building', False)}\n"
            output += f"Duration: {build_info.get('duration', 'N/A')} ms\n"
            output += f"Estimated Duration: {build_info.get('estimatedDuration', 'N/A')} ms\n"
            
            # Timestamp
            if build_info.get('timestamp'):
                import datetime
                timestamp = datetime.datetime.fromtimestamp(build_info['timestamp'] / 1000)
                output += f"Started: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            output += f"Built On: {build_info.get('builtOn', 'N/A')}\n"
            output += f"Keep Log: {build_info.get('keepLog', False)}\n"
            
            # Build parameters
            if build_info.get('actions'):
                params = []
                for action in build_info['actions']:
                    if action and action.get('_class') == 'hudson.model.ParametersAction':
                        if 'parameters' in action:
                            params.extend(action['parameters'])
                
                if params:
                    output += f"\nBuild Parameters:\n"
                    for param in params:
                        output += f"  {param.get('name', 'N/A')}: {param.get('value', 'N/A')}\n"
            
            # Artifacts
            if build_info.get('artifacts'):
                output += f"\nBuild Artifacts:\n"
                for artifact in build_info['artifacts']:
                    output += f"  {artifact.get('fileName', 'N/A')} ({artifact.get('relativePath', 'N/A')})\n"
            
            # Changesets
            if build_info.get('changeSet') and build_info['changeSet'].get('items'):
                output += f"\nChanges:\n"
                for change in build_info['changeSet']['items']:
                    output += f"  Commit: {change.get('commitId', 'N/A')[:8]}\n"
                    output += f"  Author: {change.get('author', {}).get('fullName', 'N/A')}\n"
                    output += f"  Message: {change.get('msg', 'N/A')}\n\n"
            
            return output
            
        except JenkinsNotFoundError:
            raise ValueError(f"Build #{build_number} for job '{job_name}' not found")
        except Exception as e:
            logger.error(f"Failed to get build info for '{job_name}' #{build_number}: {e}")
            raise ValueError(f"Failed to get build info: {e}")