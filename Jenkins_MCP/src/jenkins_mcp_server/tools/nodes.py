"""Jenkins node management tools."""

from typing import Any, Dict, List, Optional, Callable

from ..utils import (
    get_logger,
    validate_node_name,
    JenkinsNotFoundError,
    JenkinsBuildError,
)


logger = get_logger("tools.nodes")


def register_tools(mcp, get_client: Callable):
    """Register node management tools with the MCP server."""
    
    @mcp.tool()
    async def jenkins_list_nodes() -> Dict[str, Any]:
        """
        List all Jenkins nodes (agents).
        
        Returns:
            Dictionary containing list of nodes with their details
        """
        try:
            client = get_client()
            nodes = client.get_nodes()
            
            formatted_nodes = []
            for node in nodes:
                formatted_node = {
                    "name": node.get("name"),
                    "offline": node.get("offline", False),
                    "temporarily_offline": node.get("temporarilyOffline", False),
                    "idle": node.get("idle", False),
                    "launch_supported": node.get("launchSupported", False),
                    "manual_launch_allowed": node.get("manualLaunchAllowed", False),
                    "num_executors": node.get("numExecutors", 0),
                    "description": node.get("description", ""),
                    "computer_class": node.get("_class", "Unknown")
                }
                formatted_nodes.append(formatted_node)
            
            return {
                "success": True,
                "nodes": formatted_nodes,
                "count": len(formatted_nodes)
            }
            
        except Exception as e:
            logger.error(f"Failed to list nodes: {e}")
            return {
                "success": False,
                "error": str(e),
                "nodes": [],
                "count": 0
            }
    
    @mcp.tool()
    async def jenkins_get_node_info(name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific Jenkins node.
        
        Args:
            name: The name of the node (use "master" for master node)
        
        Returns:
            Dictionary containing detailed node information
        """
        try:
            node_name = validate_node_name(name) if name != "master" else name
            client = get_client()
            
            node_info = client.get_node_info(node_name)
            
            formatted_info = {
                "name": node_info.get("displayName", name),
                "description": node_info.get("description", ""),
                "num_executors": node_info.get("numExecutors", 0),
                "mode": node_info.get("mode", "NORMAL"),
                "offline": node_info.get("offline", False),
                "temporarily_offline": node_info.get("temporarilyOffline", False),
                "offline_cause": node_info.get("offlineCause"),
                "offline_cause_reason": node_info.get("offlineCauseReason", ""),
                "idle": node_info.get("idle", False),
                "launch_supported": node_info.get("launchSupported", False),
                "manual_launch_allowed": node_info.get("manualLaunchAllowed", False),
                "one_off_executor": node_info.get("oneOffExecutor", False),
                "class": node_info.get("_class", "Unknown"),
                "executors": [],
                "monitoring_data": {}
            }
            
            # Add executor information
            if "executors" in node_info:
                for executor in node_info["executors"]:
                    exec_info = {
                        "number": executor.get("number", 0),
                        "idle": executor.get("idle", True),
                        "likely_stuck": executor.get("likelyStuck", False)
                    }
                    
                    if "currentExecutable" in executor and executor["currentExecutable"]:
                        exec_info["current_build"] = {
                            "url": executor["currentExecutable"].get("url"),
                            "full_display_name": executor["currentExecutable"].get("fullDisplayName")
                        }
                    
                    formatted_info["executors"].append(exec_info)
            
            # Add monitoring data if available
            if "monitorData" in node_info:
                monitor_data = node_info["monitorData"]
                formatted_info["monitoring_data"] = {
                    "architecture": monitor_data.get("hudson.node_monitors.ArchitectureMonitor", {}).get("data"),
                    "clock_difference": monitor_data.get("hudson.node_monitors.ClockMonitor", {}).get("diff"),
                    "disk_space": monitor_data.get("hudson.node_monitors.DiskSpaceMonitor", {}).get("size"),
                    "response_time": monitor_data.get("hudson.node_monitors.ResponseTimeMonitor", {}).get("average"),
                    "swap_space": monitor_data.get("hudson.node_monitors.SwapSpaceMonitor", {}).get("availableSwapSpace"),
                    "temp_space": monitor_data.get("hudson.node_monitors.TemporarySpaceMonitor", {}).get("size")
                }
            
            return {
                "success": True,
                "node": formatted_info
            }
            
        except JenkinsNotFoundError as e:
            return {
                "success": False,
                "error": f"Node not found: {e}",
                "node_name": name
            }
        except Exception as e:
            logger.error(f"Failed to get node info for '{name}': {e}")
            return {
                "success": False,
                "error": str(e),
                "node_name": name
            }
    
    @mcp.tool()
    async def jenkins_toggle_node_offline(
        name: str,
        offline: bool,
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Take a node online or offline.
        
        Args:
            name: The name of the node
            offline: True to take offline, False to bring online
            message: Optional message explaining why node is being taken offline
        
        Returns:
            Dictionary containing operation result
        """
        try:
            node_name = validate_node_name(name) if name != "master" else name
            client = get_client()
            
            if offline:
                client.jenkins.disable_node(node_name, msg=message or "Taken offline via MCP")
                action = "taken offline"
            else:
                client.jenkins.enable_node(node_name)
                action = "brought online"
            
            return {
                "success": True,
                "message": f"Node '{node_name}' has been {action}",
                "node_name": node_name,
                "offline": offline,
                "offline_message": message if offline else None
            }
            
        except JenkinsNotFoundError as e:
            return {
                "success": False,
                "error": f"Node not found: {e}",
                "node_name": name
            }
        except Exception as e:
            logger.error(f"Failed to toggle node '{name}' offline status: {e}")
            return {
                "success": False,
                "error": str(e),
                "node_name": name
            }