"""Jenkins job management tools."""

from typing import Any, Dict, List, Optional, Callable

from ..utils import (
    get_logger,
    validate_job_name,
    validate_xml_config,
    validate_job_parameters,
    JenkinsNotFoundError,
    JenkinsBuildError,
)


logger = get_logger("tools.jobs")


def register_tools(mcp, get_client: Callable):
    """Register job management tools with the MCP server."""
    
    @mcp.tool()
    async def jenkins_list_jobs(
        folder: Optional[str] = None,
        depth: int = 1
    ) -> Dict[str, Any]:
        """
        List all Jenkins jobs with optional folder filtering.
        
        Args:
            folder: Optional folder path to filter jobs (e.g., "MyFolder/SubFolder")
            depth: Depth of job tree to retrieve (default: 1)
        
        Returns:
            Dictionary containing list of jobs with their details
        """
        try:
            client = get_client()
            
            if folder:
                # Get jobs from specific folder
                folder_info = client.jenkins.get_job_info(folder, depth=depth)
                jobs = folder_info.get('jobs', [])
            else:
                # Get all jobs
                jobs = client.get_jobs()
            
            # Format job information
            formatted_jobs = []
            for job in jobs:
                formatted_job = {
                    "name": job.get("name"),
                    "url": job.get("url"),
                    "color": job.get("color"),
                    "buildable": job.get("buildable", False),
                    "class": job.get("_class", "Unknown"),
                }
                
                # Add last build info if available
                if "lastBuild" in job and job["lastBuild"]:
                    formatted_job["last_build"] = {
                        "number": job["lastBuild"].get("number"),
                        "url": job["lastBuild"].get("url"),
                    }
                
                formatted_jobs.append(formatted_job)
            
            return {
                "success": True,
                "jobs": formatted_jobs,
                "count": len(formatted_jobs),
                "folder": folder or "root"
            }
            
        except Exception as e:
            logger.error(f"Failed to list jobs: {e}")
            return {
                "success": False,
                "error": str(e),
                "jobs": [],
                "count": 0
            }
    
    @mcp.tool()
    async def jenkins_get_job_info(name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific Jenkins job.
        
        Args:
            name: The name of the Jenkins job
        
        Returns:
            Dictionary containing detailed job information
        """
        try:
            job_name = validate_job_name(name)
            client = get_client()
            
            job_info = client.get_job_info(job_name)
            
            # Format the response
            formatted_info = {
                "name": job_info.get("name"),
                "display_name": job_info.get("displayName"),
                "description": job_info.get("description", ""),
                "url": job_info.get("url"),
                "buildable": job_info.get("buildable", False),
                "color": job_info.get("color"),
                "class": job_info.get("_class"),
                "concurrent_build": job_info.get("concurrentBuild", False),
                "disabled": job_info.get("disabled", False),
                "keep_dependencies": job_info.get("keepDependencies", False),
                "next_build_number": job_info.get("nextBuildNumber"),
                "in_queue": job_info.get("inQueue", False),
                "builds": [],
                "health_report": [],
                "parameters": [],
                "scm": {},
                "triggers": []
            }
            
            # Add build history
            if "builds" in job_info and job_info["builds"]:
                formatted_info["builds"] = [
                    {
                        "number": build.get("number"),
                        "url": build.get("url")
                    }
                    for build in job_info["builds"][:10]  # Limit to last 10 builds
                ]
            
            # Add health report
            if "healthReport" in job_info:
                formatted_info["health_report"] = [
                    {
                        "description": report.get("description"),
                        "score": report.get("score")
                    }
                    for report in job_info["healthReport"]
                ]
            
            # Add last build info
            if "lastBuild" in job_info and job_info["lastBuild"]:
                formatted_info["last_build"] = {
                    "number": job_info["lastBuild"].get("number"),
                    "url": job_info["lastBuild"].get("url"),
                    "building": False
                }
                
                # Get last build details
                try:
                    last_build_info = client.get_build_info(
                        job_name, 
                        job_info["lastBuild"]["number"]
                    )
                    formatted_info["last_build"].update({
                        "result": last_build_info.get("result"),
                        "timestamp": last_build_info.get("timestamp"),
                        "duration": last_build_info.get("duration"),
                        "building": last_build_info.get("building", False)
                    })
                except Exception:
                    pass  # Continue if we can't get last build details
            
            # Add property information (parameters, etc.)
            if "property" in job_info:
                for prop in job_info["property"]:
                    if prop.get("_class") == "hudson.model.ParametersDefinitionProperty":
                        if "parameterDefinitions" in prop:
                            formatted_info["parameters"] = [
                                {
                                    "name": param.get("name"),
                                    "type": param.get("type"),
                                    "description": param.get("description", ""),
                                    "default_value": param.get("defaultParameterValue", {}).get("value")
                                }
                                for param in prop["parameterDefinitions"]
                            ]
            
            return {
                "success": True,
                "job": formatted_info
            }
            
        except JenkinsNotFoundError as e:
            return {
                "success": False,
                "error": f"Job not found: {e}",
                "job": None
            }
        except Exception as e:
            logger.error(f"Failed to get job info for '{name}': {e}")
            return {
                "success": False,
                "error": str(e),
                "job": None
            }
    
    @mcp.tool()
    async def jenkins_create_job(
        name: str,
        config_xml: str,
        folder: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new Jenkins job from XML configuration.
        
        Args:
            name: The name for the new job
            config_xml: XML configuration for the job
            folder: Optional folder to create the job in
        
        Returns:
            Dictionary containing creation result
        """
        try:
            job_name = validate_job_name(name)
            xml_config = validate_xml_config(config_xml)
            client = get_client()
            
            # If folder is specified, create job in folder
            if folder:
                full_name = f"{folder}/{job_name}"
            else:
                full_name = job_name
            
            client.create_job(full_name, xml_config)
            
            return {
                "success": True,
                "message": f"Job '{full_name}' created successfully",
                "job_name": full_name,
                "url": f"{client.config.url}/job/{full_name.replace('/', '/job/')}"
            }
            
        except JenkinsBuildError as e:
            return {
                "success": False,
                "error": str(e),
                "job_name": name
            }
        except Exception as e:
            logger.error(f"Failed to create job '{name}': {e}")
            return {
                "success": False,
                "error": str(e),
                "job_name": name
            }
    
    @mcp.tool()
    async def jenkins_update_job_config(
        name: str,
        config_xml: str
    ) -> Dict[str, Any]:
        """
        Update the XML configuration of an existing Jenkins job.
        
        Args:
            name: The name of the job to update
            config_xml: New XML configuration for the job
        
        Returns:
            Dictionary containing update result
        """
        try:
            job_name = validate_job_name(name)
            xml_config = validate_xml_config(config_xml)
            client = get_client()
            
            # Verify job exists first
            client.get_job_info(job_name)
            
            # Update job configuration
            client.jenkins.reconfig_job(job_name, xml_config)
            
            return {
                "success": True,
                "message": f"Job '{job_name}' configuration updated successfully",
                "job_name": job_name
            }
            
        except JenkinsNotFoundError as e:
            return {
                "success": False,
                "error": f"Job not found: {e}",
                "job_name": name
            }
        except Exception as e:
            logger.error(f"Failed to update job config for '{name}': {e}")
            return {
                "success": False,
                "error": str(e),
                "job_name": name
            }
    
    @mcp.tool()
    async def jenkins_copy_job(
        source_name: str,
        target_name: str,
        folder: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Copy an existing Jenkins job to create a new job.
        
        Args:
            source_name: Name of the source job to copy
            target_name: Name for the new copied job
            folder: Optional folder to create the copied job in
        
        Returns:
            Dictionary containing copy result
        """
        try:
            source_job_name = validate_job_name(source_name)
            target_job_name = validate_job_name(target_name)
            client = get_client()
            
            # If folder is specified, create job in folder
            if folder:
                full_target_name = f"{folder}/{target_job_name}"
            else:
                full_target_name = target_job_name
            
            client.jenkins.copy_job(source_job_name, full_target_name)
            
            return {
                "success": True,
                "message": f"Job '{source_job_name}' copied to '{full_target_name}' successfully",
                "source_job": source_job_name,
                "target_job": full_target_name,
                "url": f"{client.config.url}/job/{full_target_name.replace('/', '/job/')}"
            }
            
        except JenkinsNotFoundError as e:
            return {
                "success": False,
                "error": f"Source job not found: {e}",
                "source_job": source_name,
                "target_job": target_name
            }
        except JenkinsBuildError as e:
            return {
                "success": False,
                "error": str(e),
                "source_job": source_name,
                "target_job": target_name
            }
        except Exception as e:
            logger.error(f"Failed to copy job from '{source_name}' to '{target_name}': {e}")
            return {
                "success": False,
                "error": str(e),
                "source_job": source_name,
                "target_job": target_name
            }
    
    @mcp.tool()
    async def jenkins_delete_job(name: str) -> Dict[str, Any]:
        """
        Delete a Jenkins job permanently.
        
        Args:
            name: The name of the job to delete
        
        Returns:
            Dictionary containing deletion result
        """
        try:
            job_name = validate_job_name(name)
            client = get_client()
            
            # Verify job exists first
            client.get_job_info(job_name)
            
            # Delete the job
            client.delete_job(job_name)
            
            return {
                "success": True,
                "message": f"Job '{job_name}' deleted successfully",
                "job_name": job_name
            }
            
        except JenkinsNotFoundError as e:
            return {
                "success": False,
                "error": f"Job not found: {e}",
                "job_name": name
            }
        except Exception as e:
            logger.error(f"Failed to delete job '{name}': {e}")
            return {
                "success": False,
                "error": str(e),
                "job_name": name
            }
    
    @mcp.tool()
    async def jenkins_enable_job(name: str) -> Dict[str, Any]:
        """
        Enable a disabled Jenkins job.
        
        Args:
            name: The name of the job to enable
        
        Returns:
            Dictionary containing enable result
        """
        try:
            job_name = validate_job_name(name)
            client = get_client()
            
            client.jenkins.enable_job(job_name)
            
            return {
                "success": True,
                "message": f"Job '{job_name}' enabled successfully",
                "job_name": job_name
            }
            
        except JenkinsNotFoundError as e:
            return {
                "success": False,
                "error": f"Job not found: {e}",
                "job_name": name
            }
        except Exception as e:
            logger.error(f"Failed to enable job '{name}': {e}")
            return {
                "success": False,
                "error": str(e),
                "job_name": name
            }
    
    @mcp.tool()
    async def jenkins_disable_job(name: str) -> Dict[str, Any]:
        """
        Disable a Jenkins job to prevent it from being built.
        
        Args:
            name: The name of the job to disable
        
        Returns:
            Dictionary containing disable result
        """
        try:
            job_name = validate_job_name(name)
            client = get_client()
            
            client.jenkins.disable_job(job_name)
            
            return {
                "success": True,
                "message": f"Job '{job_name}' disabled successfully",
                "job_name": job_name
            }
            
        except JenkinsNotFoundError as e:
            return {
                "success": False,
                "error": f"Job not found: {e}",
                "job_name": name
            }
        except Exception as e:
            logger.error(f"Failed to disable job '{name}': {e}")
            return {
                "success": False,
                "error": str(e),
                "job_name": name
            }