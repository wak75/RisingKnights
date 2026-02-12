"""Jenkins user management tools."""

from typing import Any, Dict, List, Optional, Callable

from ..utils import (
    get_logger,
    validate_username,
    JenkinsNotFoundError,
    JenkinsPermissionError,
)


logger = get_logger("tools.users")


def register_tools(mcp, get_client: Callable):
    """Register user management tools with the MCP server."""
    
    @mcp.tool()
    async def jenkins_whoami() -> Dict[str, Any]:
        """
        Get information about the current authenticated user.
        
        Returns:
            Dictionary containing current user information
        """
        try:
            client = get_client()
            
            user_info = client.jenkins.get_whoami()
            
            formatted_info = {
                "id": user_info.get("id"),
                "full_name": user_info.get("fullName"),
                "description": user_info.get("description", ""),
                "absolute_url": user_info.get("absoluteUrl", ""),
                "authorities": user_info.get("authorities", [])
            }
            
            return {
                "success": True,
                "user": formatted_info
            }
            
        except Exception as e:
            logger.error(f"Failed to get current user info: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def jenkins_get_user_info(username: str) -> Dict[str, Any]:
        """
        Get information about a specific user.
        
        Args:
            username: The username to look up
        
        Returns:
            Dictionary containing user information
        """
        try:
            user_name = validate_username(username)
            client = get_client()
            
            # Note: Jenkins python client doesn't have a direct get_user_info method
            # This would require a custom API call
            user_url = f"user/{user_name}/api/json"
            
            try:
                # This is a placeholder - would need to implement custom API call
                user_info = {
                    "id": user_name,
                    "full_name": user_name,
                    "description": "",
                    "absolute_url": f"{client.config.url}/user/{user_name}",
                    "note": "Detailed user information requires additional API implementation"
                }
                
                return {
                    "success": True,
                    "user": user_info
                }
            except Exception:
                raise JenkinsNotFoundError(f"User '{user_name}' not found")
            
        except JenkinsNotFoundError as e:
            return {
                "success": False,
                "error": str(e),
                "username": username
            }
        except Exception as e:
            logger.error(f"Failed to get user info for '{username}': {e}")
            return {
                "success": False,
                "error": str(e),
                "username": username
            }
    
    @mcp.tool()
    async def jenkins_list_users() -> Dict[str, Any]:
        """
        List all Jenkins users.
        
        Returns:
            Dictionary containing list of users
        """
        try:
            client = get_client()
            
            # Note: This is a simplified implementation
            # Full implementation would require additional API calls
            current_user = client.jenkins.get_whoami()
            
            users = [
                {
                    "id": current_user.get("id"),
                    "full_name": current_user.get("fullName"),
                    "description": current_user.get("description", ""),
                    "is_current_user": True
                }
            ]
            
            return {
                "success": True,
                "users": users,
                "count": len(users),
                "note": "Full user listing requires additional Jenkins API implementation"
            }
            
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            return {
                "success": False,
                "error": str(e),
                "users": [],
                "count": 0
            }