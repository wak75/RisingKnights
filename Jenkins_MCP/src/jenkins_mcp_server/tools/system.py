"""Jenkins system operation tools."""

from typing import Any, Dict, List, Optional, Callable
import time

from ..utils import (
    get_logger,
    JenkinsBuildError,
    JenkinsPermissionError,
)
from ..client import create_jenkins_client


logger = get_logger("tools.system")


def register_tools(mcp, get_client: Callable):
    """Register system operation tools with the MCP server."""
    
    @mcp.tool()
    async def jenkins_get_system_info() -> Dict[str, Any]:
        """
        Get Jenkins system information and statistics.
        
        Returns:
            Dictionary containing comprehensive system information
        """
        try:
            client = get_client()
            
            # Get basic Jenkins info
            version = client.get_version()
            nodes = client.get_nodes()
            jobs = client.get_jobs()
            queue = client.jenkins.get_queue_info()
            
            # Calculate statistics
            total_executors = sum(node.get("numExecutors", 0) for node in nodes)
            online_nodes = sum(1 for node in nodes if not node.get("offline", False))
            offline_nodes = sum(1 for node in nodes if node.get("offline", False))
            busy_executors = 0
            
            for node in nodes:
                if "executors" in node:
                    busy_executors += sum(1 for executor in node["executors"] 
                                        if not executor.get("idle", True))
            
            # Get user info if available
            user_info = {}
            try:
                user_info = client.jenkins.get_whoami()
            except Exception:
                pass  # User info not available
            
            system_info = {
                "jenkins_version": version,
                "server_url": client.config.url,
                "user": user_info,
                "statistics": {
                    "total_jobs": len(jobs),
                    "total_nodes": len(nodes),
                    "online_nodes": online_nodes,
                    "offline_nodes": offline_nodes,
                    "total_executors": total_executors,
                    "busy_executors": busy_executors,
                    "idle_executors": total_executors - busy_executors,
                    "queue_length": len(queue)
                },
                "node_summary": [],
                "queue_summary": {
                    "total_items": len(queue),
                    "blocked_items": sum(1 for item in queue if item.get("blocked", False)),
                    "buildable_items": sum(1 for item in queue if item.get("buildable", False)),
                    "stuck_items": sum(1 for item in queue if item.get("stuck", False))
                }
            }
            
            # Add node summary
            for node in nodes:
                node_summary = {
                    "name": node.get("name"),
                    "offline": node.get("offline", False),
                    "num_executors": node.get("numExecutors", 0),
                    "description": node.get("description", "")[:100]  # Truncate long descriptions
                }
                system_info["node_summary"].append(node_summary)
            
            return {
                "success": True,
                "system": system_info
            }
            
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def jenkins_quiet_down(
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Put Jenkins into quiet-down mode to prepare for shutdown.
        
        Args:
            message: Optional message to display to users
        
        Returns:
            Dictionary containing operation result
        """
        try:
            client = get_client()
            
            client.jenkins.quiet_down()
            
            return {
                "success": True,
                "message": "Jenkins has been put into quiet-down mode",
                "note": "No new builds will be started. Existing builds will complete.",
                "quiet_down_message": message
            }
            
        except JenkinsPermissionError as e:
            return {
                "success": False,
                "error": f"Permission denied: {e}",
                "note": "Administrator privileges required for this operation"
            }
        except Exception as e:
            logger.error(f"Failed to put Jenkins into quiet-down mode: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def jenkins_cancel_quiet_down() -> Dict[str, Any]:
        """
        Cancel quiet-down mode and resume normal operation.
        
        Returns:
            Dictionary containing operation result
        """
        try:
            client = get_client()
            
            client.jenkins.cancel_quiet_down()
            
            return {
                "success": True,
                "message": "Jenkins quiet-down mode has been cancelled",
                "note": "Normal operation has resumed"
            }
            
        except JenkinsPermissionError as e:
            return {
                "success": False,
                "error": f"Permission denied: {e}",
                "note": "Administrator privileges required for this operation"
            }
        except Exception as e:
            logger.error(f"Failed to cancel quiet-down mode: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def jenkins_restart(
        safe: bool = True,
        wait: bool = False,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Restart Jenkins server.
        
        Args:
            safe: If True, wait for running builds to complete before restart
            wait: If True, wait for Jenkins to come back online
            timeout: Timeout in seconds if wait=True (default: 300)
        
        Returns:
            Dictionary containing restart operation result
        """
        try:
            client = get_client()
            
            if safe:
                client.jenkins.safe_restart()
                restart_type = "safe restart"
            else:
                client.jenkins.restart()
                restart_type = "immediate restart"
            
            result = {
                "success": True,
                "message": f"Jenkins {restart_type} has been initiated",
                "restart_type": restart_type,
                "safe": safe
            }
            
            if wait:
                # Wait for Jenkins to come back online
                start_time = time.time()
                while time.time() - start_time < timeout:
                    try:
                        time.sleep(10)  # Wait 10 seconds between checks
                        test_client = create_jenkins_client(client.config)
                        test_client.get_version()  # Test if Jenkins is responsive
                        result.update({
                            "online": True,
                            "restart_duration": int(time.time() - start_time),
                            "message": f"Jenkins {restart_type} completed successfully"
                        })
                        break
                    except Exception:
                        continue  # Jenkins not ready yet
                else:
                    result.update({
                        "online": False,
                        "warning": f"Jenkins did not come back online within {timeout} seconds",
                        "restart_duration": timeout
                    })
            
            return result
            
        except JenkinsPermissionError as e:
            return {
                "success": False,
                "error": f"Permission denied: {e}",
                "note": "Administrator privileges required for this operation"
            }
        except Exception as e:
            logger.error(f"Failed to restart Jenkins: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def jenkins_get_system_log(
        level: str = "INFO",
        lines: int = 100
    ) -> Dict[str, Any]:
        """
        Get Jenkins system log entries.
        
        Args:
            level: Log level filter (DEBUG, INFO, WARNING, ERROR)
            lines: Number of log lines to retrieve (default: 100)
        
        Returns:
            Dictionary containing system log entries
        """
        try:
            client = get_client()
            
            # Note: This is a simplified implementation
            # In a real implementation, you would need to access Jenkins' log files
            # or use the Jenkins REST API for log management if available
            
            log_info = {
                "level_filter": level,
                "lines_requested": lines,
                "note": "System log access requires specific Jenkins configuration",
                "suggestion": "Use Jenkins web interface -> Manage Jenkins -> System Log for detailed logs"
            }
            
            return {
                "success": True,
                "log_info": log_info,
                "logs": []  # Would contain actual log entries in full implementation
            }
            
        except Exception as e:
            logger.error(f"Failed to get system log: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def jenkins_run_groovy_script(script: str) -> Dict[str, Any]:
        """
        Execute a Groovy script on the Jenkins master.
        
        Args:
            script: Groovy script to execute
        
        Returns:
            Dictionary containing script execution result
        """
        try:
            client = get_client()
            
            result = client.jenkins.run_script(script)
            
            return {
                "success": True,
                "message": "Groovy script executed successfully",
                "script": script,
                "result": result,
                "warning": "Be careful with Groovy scripts as they have full system access"
            }
            
        except JenkinsPermissionError as e:
            return {
                "success": False,
                "error": f"Permission denied: {e}",
                "note": "Administrator privileges required to run Groovy scripts"
            }
        except Exception as e:
            logger.error(f"Failed to run Groovy script: {e}")
            return {
                "success": False,
                "error": str(e),
                "script": script
            }