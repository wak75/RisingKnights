"""Jenkins build operation tools."""

from typing import Any, Dict, List, Optional, Callable
import time

from ..utils import (
    get_logger,
    validate_job_name,
    validate_build_number,
    validate_job_parameters,
    JenkinsNotFoundError,
    JenkinsBuildError,
)


logger = get_logger("tools.builds")


def register_tools(mcp, get_client: Callable):
    """Register build operation tools with the MCP server."""
    
    @mcp.tool()
    async def jenkins_build_job(
        name: str,
        parameters: Optional[Dict[str, Any]] = None,
        wait: bool = False,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Trigger a build for a Jenkins job.
        
        Args:
            name: The name of the job to build
            parameters: Optional build parameters as key-value pairs
            wait: Whether to wait for the build to complete
            timeout: Timeout in seconds if wait=True (default: 300)
        
        Returns:
            Dictionary containing build trigger result and build number
        """
        try:
            job_name = validate_job_name(name)
            client = get_client()
            
            # Validate parameters if provided
            if parameters:
                parameters = validate_job_parameters(parameters)
            
            # Get next build number before triggering
            job_info = client.get_job_info(job_name)
            next_build_number = job_info.get("nextBuildNumber", 1)
            
            # Trigger the build
            if parameters:
                queue_item_number = client.jenkins.build_job(job_name, parameters)
            else:
                queue_item_number = client.jenkins.build_job(job_name)
            
            result = {
                "success": True,
                "message": f"Build triggered for job '{job_name}'",
                "job_name": job_name,
                "queue_item": queue_item_number,
                "expected_build_number": next_build_number,
                "parameters": parameters or {}
            }
            
            if wait:
                # Wait for build to start and complete
                build_started = False
                start_time = time.time()
                
                while time.time() - start_time < timeout:
                    try:
                        # Check if build has started
                        build_info = client.get_build_info(job_name, next_build_number)
                        build_started = True
                        
                        if not build_info.get("building", False):
                            # Build completed
                            result.update({
                                "build_number": next_build_number,
                                "result": build_info.get("result"),
                                "duration": build_info.get("duration"),
                                "timestamp": build_info.get("timestamp"),
                                "completed": True
                            })
                            break
                        
                    except JenkinsNotFoundError:
                        # Build hasn't started yet
                        pass
                    
                    time.sleep(2)  # Wait 2 seconds before checking again
                
                if not build_started:
                    result["warning"] = f"Build did not start within {timeout} seconds"
                elif result.get("completed", False) is False:
                    result["warning"] = f"Build did not complete within {timeout} seconds"
                    result["build_number"] = next_build_number
                    result["building"] = True
            
            return result
            
        except JenkinsNotFoundError as e:
            return {
                "success": False,
                "error": f"Job not found: {e}",
                "job_name": name
            }
        except Exception as e:
            logger.error(f"Failed to build job '{name}': {e}")
            return {
                "success": False,
                "error": str(e),
                "job_name": name
            }
    
    @mcp.tool()
    async def jenkins_get_build_info(
        name: str,
        number: int
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific build.
        
        Args:
            name: The name of the job
            number: The build number
        
        Returns:
            Dictionary containing detailed build information
        """
        try:
            job_name = validate_job_name(name)
            build_number = validate_build_number(number)
            client = get_client()
            
            build_info = client.get_build_info(job_name, build_number)
            
            # Format the response
            formatted_info = {
                "number": build_info.get("number"),
                "id": build_info.get("id"),
                "display_name": build_info.get("displayName"),
                "full_display_name": build_info.get("fullDisplayName"),
                "description": build_info.get("description", ""),
                "url": build_info.get("url"),
                "result": build_info.get("result"),
                "timestamp": build_info.get("timestamp"),
                "duration": build_info.get("duration"),
                "estimated_duration": build_info.get("estimatedDuration"),
                "building": build_info.get("building", False),
                "keep_log": build_info.get("keepLog", False),
                "queue_id": build_info.get("queueId"),
                "built_on": build_info.get("builtOn", ""),
                "parameters": [],
                "artifacts": [],
                "causes": [],
                "changesets": [],
                "culprits": []
            }
            
            # Add build parameters
            if "actions" in build_info:
                for action in build_info["actions"]:
                    if action and action.get("_class") == "hudson.model.ParametersAction":
                        if "parameters" in action:
                            for param in action["parameters"]:
                                formatted_info["parameters"].append({
                                    "name": param.get("name"),
                                    "value": param.get("value")
                                })
                    
                    # Add build causes
                    elif action and action.get("_class") == "hudson.model.CauseAction":
                        if "causes" in action:
                            for cause in action["causes"]:
                                cause_info = {
                                    "class": cause.get("_class", "Unknown"),
                                    "short_description": cause.get("shortDescription", "")
                                }
                                if "userId" in cause:
                                    cause_info["user_id"] = cause["userId"]
                                if "userName" in cause:
                                    cause_info["user_name"] = cause["userName"]
                                formatted_info["causes"].append(cause_info)
            
            # Add artifacts
            if "artifacts" in build_info:
                for artifact in build_info["artifacts"]:
                    formatted_info["artifacts"].append({
                        "display_path": artifact.get("displayPath"),
                        "file_name": artifact.get("fileName"),
                        "relative_path": artifact.get("relativePath")
                    })
            
            # Add changeset information
            if "changeSet" in build_info:
                changeset = build_info["changeSet"]
                if "items" in changeset:
                    for item in changeset["items"]:
                        formatted_info["changesets"].append({
                            "commit_id": item.get("commitId"),
                            "author": item.get("author", {}).get("fullName", "Unknown"),
                            "msg": item.get("msg", ""),
                            "timestamp": item.get("timestamp"),
                            "paths": [path.get("file") for path in item.get("paths", [])]
                        })
            
            # Add culprits
            if "culprits" in build_info:
                for culprit in build_info["culprits"]:
                    formatted_info["culprits"].append({
                        "full_name": culprit.get("fullName"),
                        "absolute_url": culprit.get("absoluteUrl")
                    })
            
            return {
                "success": True,
                "build": formatted_info
            }
            
        except JenkinsNotFoundError as e:
            return {
                "success": False,
                "error": f"Build not found: {e}",
                "job_name": name,
                "build_number": number
            }
        except Exception as e:
            logger.error(f"Failed to get build info for '{name}' #{number}: {e}")
            return {
                "success": False,
                "error": str(e),
                "job_name": name,
                "build_number": number
            }
    
    @mcp.tool()
    async def jenkins_get_build_log(
        name: str,
        number: int,
        start: int = 0,
        html: bool = False
    ) -> Dict[str, Any]:
        """
        Get console output (log) for a specific build.
        
        Args:
            name: The name of the job
            number: The build number
            start: Starting position in the log (for pagination)
            html: Whether to return HTML-formatted log (default: False)
        
        Returns:
            Dictionary containing build log and metadata
        """
        try:
            job_name = validate_job_name(name)
            build_number = validate_build_number(number)
            client = get_client()
            
            # Get build info first to check if build exists and get status
            build_info = client.get_build_info(job_name, build_number)
            
            # Get console output
            if html:
                log_url = f"job/{job_name}/{build_number}/logText/progressiveHtml"
                params = {"start": start} if start > 0 else None
                log_content = client.jenkins.jenkins_open(
                    client.jenkins._build_url(log_url, params)
                ).read().decode('utf-8')
            else:
                log_content = client.get_build_console_output(job_name, build_number)
            
            # If start position is specified, get progressive log
            if start > 0:
                lines = log_content.split('\n')
                log_content = '\n'.join(lines[start:])
            
            return {
                "success": True,
                "job_name": job_name,
                "build_number": build_number,
                "log": log_content,
                "building": build_info.get("building", False),
                "result": build_info.get("result"),
                "start_position": start,
                "log_size": len(log_content),
                "html_formatted": html
            }
            
        except JenkinsNotFoundError as e:
            return {
                "success": False,
                "error": f"Build not found: {e}",
                "job_name": name,
                "build_number": number
            }
        except Exception as e:
            logger.error(f"Failed to get build log for '{name}' #{number}: {e}")
            return {
                "success": False,
                "error": str(e),
                "job_name": name,
                "build_number": number
            }
    
    @mcp.tool()
    async def jenkins_stop_build(
        name: str,
        number: int
    ) -> Dict[str, Any]:
        """
        Stop a running build.
        
        Args:
            name: The name of the job
            number: The build number to stop
        
        Returns:
            Dictionary containing stop operation result
        """
        try:
            job_name = validate_job_name(name)
            build_number = validate_build_number(number)
            client = get_client()
            
            # Check if build exists and is running
            build_info = client.get_build_info(job_name, build_number)
            
            if not build_info.get("building", False):
                return {
                    "success": False,
                    "error": "Build is not currently running",
                    "job_name": job_name,
                    "build_number": build_number,
                    "current_result": build_info.get("result")
                }
            
            # Stop the build
            client.jenkins.stop_build(job_name, build_number)
            
            return {
                "success": True,
                "message": f"Build #{build_number} for job '{job_name}' has been stopped",
                "job_name": job_name,
                "build_number": build_number
            }
            
        except JenkinsNotFoundError as e:
            return {
                "success": False,
                "error": f"Build not found: {e}",
                "job_name": name,
                "build_number": number
            }
        except Exception as e:
            logger.error(f"Failed to stop build '{name}' #{number}: {e}")
            return {
                "success": False,
                "error": str(e),
                "job_name": name,
                "build_number": number
            }
    
    @mcp.tool()
    async def jenkins_get_build_artifacts(
        name: str,
        number: int
    ) -> Dict[str, Any]:
        """
        Get list of artifacts for a specific build.
        
        Args:
            name: The name of the job
            number: The build number
        
        Returns:
            Dictionary containing list of build artifacts
        """
        try:
            job_name = validate_job_name(name)
            build_number = validate_build_number(number)
            client = get_client()
            
            build_info = client.get_build_info(job_name, build_number)
            
            artifacts = []
            if "artifacts" in build_info:
                for artifact in build_info["artifacts"]:
                    artifact_info = {
                        "display_path": artifact.get("displayPath"),
                        "file_name": artifact.get("fileName"),
                        "relative_path": artifact.get("relativePath"),
                        "download_url": f"{build_info['url']}artifact/{artifact.get('relativePath')}"
                    }
                    artifacts.append(artifact_info)
            
            return {
                "success": True,
                "job_name": job_name,
                "build_number": build_number,
                "artifacts": artifacts,
                "count": len(artifacts),
                "build_url": build_info.get("url")
            }
            
        except JenkinsNotFoundError as e:
            return {
                "success": False,
                "error": f"Build not found: {e}",
                "job_name": name,
                "build_number": number,
                "artifacts": []
            }
        except Exception as e:
            logger.error(f"Failed to get artifacts for '{name}' #{number}: {e}")
            return {
                "success": False,
                "error": str(e),
                "job_name": name,
                "build_number": number,
                "artifacts": []
            }
    
    @mcp.tool()
    async def jenkins_get_queue_info() -> Dict[str, Any]:
        """
        Get information about the Jenkins build queue.
        
        Returns:
            Dictionary containing queue information
        """
        try:
            client = get_client()
            
            queue_info = client.jenkins.get_queue_info()
            
            formatted_queue = []
            for item in queue_info:
                queue_item = {
                    "id": item.get("id"),
                    "task_name": item.get("task", {}).get("name", "Unknown"),
                    "task_url": item.get("task", {}).get("url"),
                    "why": item.get("why"),
                    "blocked": item.get("blocked", False),
                    "buildable": item.get("buildable", False),
                    "stuck": item.get("stuck", False),
                    "in_queue_since": item.get("inQueueSince"),
                    "build_start_milliseconds": item.get("buildStartMilliseconds"),
                    "params": item.get("params", "")
                }
                
                # Add actions information
                if "actions" in item:
                    for action in item["actions"]:
                        if action and "parameters" in action:
                            queue_item["parameters"] = [
                                {
                                    "name": param.get("name"),
                                    "value": param.get("value")
                                }
                                for param in action["parameters"]
                            ]
                            break
                
                formatted_queue.append(queue_item)
            
            return {
                "success": True,
                "queue": formatted_queue,
                "count": len(formatted_queue)
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue info: {e}")
            return {
                "success": False,
                "error": str(e),
                "queue": [],
                "count": 0
            }
    
    @mcp.tool()
    async def jenkins_cancel_queue_item(item_id: int) -> Dict[str, Any]:
        """
        Cancel a queued build item.
        
        Args:
            item_id: The ID of the queue item to cancel
        
        Returns:
            Dictionary containing cancellation result
        """
        try:
            client = get_client()
            
            client.jenkins.cancel_queue(item_id)
            
            return {
                "success": True,
                "message": f"Queue item {item_id} has been cancelled",
                "item_id": item_id
            }
            
        except Exception as e:
            logger.error(f"Failed to cancel queue item {item_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "item_id": item_id
            }