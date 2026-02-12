"""Jenkins system metrics resources."""

from typing import Any, Dict, Optional, Callable

from ..utils import (
    get_logger,
    JenkinsConnectionError,
)


logger = get_logger("resources.metrics")


def register_resources(mcp, get_client: Callable):
    """Register system metrics resources with the MCP server."""
    
    @mcp.resource("jenkins://system/metrics")
    async def get_system_metrics() -> str:
        """
        Get formatted Jenkins system metrics and statistics.
        
        Returns:
            Formatted string containing system metrics
        """
        try:
            client = get_client()
            
            # Get system information
            version = client.get_version()
            nodes = client.get_nodes()
            jobs = client.get_jobs()
            queue = client.jenkins.get_queue_info()
            
            # Format metrics
            output = f"Jenkins System Metrics\n"
            output += f"Generated at: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            output += "=" * 50 + "\n\n"
            
            # Basic system info
            output += f"Jenkins Version: {version}\n"
            output += f"Server URL: {client.config.url}\n\n"
            
            # Job statistics
            output += "Job Statistics:\n"
            output += "-" * 20 + "\n"
            output += f"Total Jobs: {len(jobs)}\n"
            
            # Count jobs by status
            job_colors = {}
            buildable_jobs = 0
            for job in jobs:
                color = job.get('color', 'unknown')
                job_colors[color] = job_colors.get(color, 0) + 1
                if job.get('buildable', False):
                    buildable_jobs += 1
            
            output += f"Buildable Jobs: {buildable_jobs}\n"
            output += f"Job Status Distribution:\n"
            for color, count in sorted(job_colors.items()):
                output += f"  {color}: {count}\n"
            
            output += "\n"
            
            # Node statistics
            output += "Node Statistics:\n"
            output += "-" * 20 + "\n"
            output += f"Total Nodes: {len(nodes)}\n"
            
            online_nodes = 0
            offline_nodes = 0
            total_executors = 0
            busy_executors = 0
            
            for node in nodes:
                if node.get('offline', False):
                    offline_nodes += 1
                else:
                    online_nodes += 1
                
                total_executors += node.get('numExecutors', 0)
                
                # Count busy executors (this is simplified)
                if not node.get('idle', True):
                    busy_executors += node.get('numExecutors', 0)
            
            output += f"Online Nodes: {online_nodes}\n"
            output += f"Offline Nodes: {offline_nodes}\n"
            output += f"Total Executors: {total_executors}\n"
            output += f"Busy Executors: {busy_executors}\n"
            output += f"Idle Executors: {total_executors - busy_executors}\n"
            
            if total_executors > 0:
                utilization = (busy_executors / total_executors) * 100
                output += f"Executor Utilization: {utilization:.1f}%\n"
            
            output += "\n"
            
            # Queue statistics
            output += "Build Queue Statistics:\n"
            output += "-" * 25 + "\n"
            output += f"Total Queued Items: {len(queue)}\n"
            
            blocked_items = sum(1 for item in queue if item.get('blocked', False))
            buildable_items = sum(1 for item in queue if item.get('buildable', False))
            stuck_items = sum(1 for item in queue if item.get('stuck', False))
            
            output += f"Blocked Items: {blocked_items}\n"
            output += f"Buildable Items: {buildable_items}\n"
            output += f"Stuck Items: {stuck_items}\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            raise ValueError(f"Failed to get system metrics: {e}")
    
    @mcp.resource("jenkins://nodes/status")
    async def get_nodes_status() -> str:
        """
        Get detailed status information for all Jenkins nodes.
        
        Returns:
            Formatted string containing node status information
        """
        try:
            client = get_client()
            nodes = client.get_nodes()
            
            # Format node status
            output = f"Jenkins Nodes Status\n"
            output += f"Generated at: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            output += "=" * 40 + "\n\n"
            
            if not nodes:
                output += "No nodes found.\n"
            else:
                for node in nodes:
                    output += f"Node: {node.get('displayName', node.get('name', 'Unknown'))}\n"
                    output += f"  Status: {'OFFLINE' if node.get('offline', False) else 'ONLINE'}\n"
                    output += f"  Temporarily Offline: {node.get('temporarilyOffline', False)}\n"
                    output += f"  Idle: {node.get('idle', True)}\n"
                    output += f"  Executors: {node.get('numExecutors', 0)}\n"
                    output += f"  Launch Supported: {node.get('launchSupported', False)}\n"
                    
                    if node.get('offlineCauseReason'):
                        output += f"  Offline Reason: {node['offlineCauseReason']}\n"
                    
                    if node.get('description'):
                        desc = node['description'][:100] + ('...' if len(node['description']) > 100 else '')
                        output += f"  Description: {desc}\n"
                    
                    output += "\n"
                
                output += f"Total Nodes: {len(nodes)}\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Failed to get nodes status: {e}")
            raise ValueError(f"Failed to get nodes status: {e}")
    
    @mcp.resource("jenkins://queue/status")
    async def get_queue_status() -> str:
        """
        Get detailed information about the Jenkins build queue.
        
        Returns:
            Formatted string containing queue status information
        """
        try:
            client = get_client()
            queue = client.jenkins.get_queue_info()
            
            # Format queue status
            output = f"Jenkins Build Queue Status\n"
            output += f"Generated at: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            output += "=" * 45 + "\n\n"
            
            if not queue:
                output += "Build queue is empty.\n"
            else:
                for item in queue:
                    task_name = item.get('task', {}).get('name', 'Unknown')
                    output += f"Queue Item #{item.get('id', 'N/A')}: {task_name}\n"
                    output += f"  Why: {item.get('why', 'No reason specified')}\n"
                    output += f"  Blocked: {item.get('blocked', False)}\n"
                    output += f"  Buildable: {item.get('buildable', False)}\n"
                    output += f"  Stuck: {item.get('stuck', False)}\n"
                    
                    if item.get('inQueueSince'):
                        import datetime
                        queued_since = datetime.datetime.fromtimestamp(item['inQueueSince'] / 1000)
                        output += f"  In Queue Since: {queued_since.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    
                    # Show parameters if available
                    if item.get('actions'):
                        for action in item['actions']:
                            if action and 'parameters' in action:
                                output += f"  Parameters:\n"
                                for param in action['parameters'][:3]:  # Show first 3 parameters
                                    output += f"    {param.get('name', 'N/A')}: {param.get('value', 'N/A')}\n"
                                break
                    
                    output += "\n"
                
                output += f"Total Queued Items: {len(queue)}\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Failed to get queue status: {e}")
            raise ValueError(f"Failed to get queue status: {e}")