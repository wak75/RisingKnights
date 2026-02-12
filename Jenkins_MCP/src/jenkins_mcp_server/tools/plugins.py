"""Jenkins plugin management tools."""

from typing import Any, Dict, List, Optional, Callable

from ..utils import (
    get_logger,
    validate_plugin_name,
    JenkinsBuildError,
)


logger = get_logger("tools.plugins")


def register_tools(mcp, get_client: Callable):
    """Register plugin management tools with the MCP server."""
    
    @mcp.tool()
    async def jenkins_list_plugins(
        depth: int = 2,
        installed_only: bool = False
    ) -> Dict[str, Any]:
        """
        List Jenkins plugins.
        
        Args:
            depth: Information depth to retrieve (default: 2)
            installed_only: If True, only show installed plugins
        
        Returns:
            Dictionary containing list of plugins
        """
        try:
            client = get_client()
            plugins_info = client.get_plugins()
            
            formatted_plugins = []
            for plugin_name, plugin_data in plugins_info.items():
                if installed_only and not plugin_data.get("enabled", False):
                    continue
                
                plugin_info = {
                    "short_name": plugin_name,
                    "long_name": plugin_data.get("longName", plugin_name),
                    "version": plugin_data.get("version", "Unknown"),
                    "enabled": plugin_data.get("enabled", False),
                    "active": plugin_data.get("active", False),
                    "has_update": plugin_data.get("hasUpdate", False),
                    "pinned": plugin_data.get("pinned", False),
                    "deleted": plugin_data.get("deleted", False),
                    "url": plugin_data.get("url", ""),
                    "supports_dynamic_load": plugin_data.get("supportsDynamicLoad", False),
                    "backup_version": plugin_data.get("backupVersion"),
                    "dependencies": []
                }
                
                # Add dependency information
                if "dependencies" in plugin_data:
                    for dep in plugin_data["dependencies"]:
                        dependency = {
                            "short_name": dep.get("shortName"),
                            "version": dep.get("version"),
                            "optional": dep.get("optional", False)
                        }
                        plugin_info["dependencies"].append(dependency)
                
                formatted_plugins.append(plugin_info)
            
            # Sort plugins by name
            formatted_plugins.sort(key=lambda x: x["short_name"])
            
            return {
                "success": True,
                "plugins": formatted_plugins,
                "count": len(formatted_plugins),
                "installed_only": installed_only
            }
            
        except Exception as e:
            logger.error(f"Failed to list plugins: {e}")
            return {
                "success": False,
                "error": str(e),
                "plugins": [],
                "count": 0
            }
    
    @mcp.tool()
    async def jenkins_get_plugin_info(name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific plugin.
        
        Args:
            name: The short name of the plugin
        
        Returns:
            Dictionary containing detailed plugin information
        """
        try:
            plugin_name = validate_plugin_name(name)
            client = get_client()
            
            plugins_info = client.get_plugins()
            
            if plugin_name not in plugins_info:
                return {
                    "success": False,
                    "error": f"Plugin '{plugin_name}' not found",
                    "plugin_name": plugin_name
                }
            
            plugin_data = plugins_info[plugin_name]
            
            plugin_info = {
                "short_name": plugin_name,
                "long_name": plugin_data.get("longName", plugin_name),
                "version": plugin_data.get("version", "Unknown"),
                "enabled": plugin_data.get("enabled", False),
                "active": plugin_data.get("active", False),
                "has_update": plugin_data.get("hasUpdate", False),
                "pinned": plugin_data.get("pinned", False),
                "deleted": plugin_data.get("deleted", False),
                "url": plugin_data.get("url", ""),
                "supports_dynamic_load": plugin_data.get("supportsDynamicLoad", False),
                "backup_version": plugin_data.get("backupVersion"),
                "dependencies": [],
                "dependents": []
            }
            
            # Add dependency information
            if "dependencies" in plugin_data:
                for dep in plugin_data["dependencies"]:
                    dependency = {
                        "short_name": dep.get("shortName"),
                        "version": dep.get("version"),
                        "optional": dep.get("optional", False)
                    }
                    plugin_info["dependencies"].append(dependency)
            
            # Find plugins that depend on this one
            for other_name, other_data in plugins_info.items():
                if other_name != plugin_name and "dependencies" in other_data:
                    for dep in other_data["dependencies"]:
                        if dep.get("shortName") == plugin_name:
                            dependent = {
                                "short_name": other_name,
                                "long_name": other_data.get("longName", other_name),
                                "version": other_data.get("version", "Unknown"),
                                "dependency_optional": dep.get("optional", False)
                            }
                            plugin_info["dependents"].append(dependent)
            
            return {
                "success": True,
                "plugin": plugin_info
            }
            
        except Exception as e:
            logger.error(f"Failed to get plugin info for '{name}': {e}")
            return {
                "success": False,
                "error": str(e),
                "plugin_name": name
            }
    
    @mcp.tool()
    async def jenkins_install_plugin(
        name: str,
        include_dependencies: bool = True
    ) -> Dict[str, Any]:
        """
        Install a Jenkins plugin.
        
        Args:
            name: The short name of the plugin to install
            include_dependencies: Whether to install dependencies (default: True)
        
        Returns:
            Dictionary containing installation result
        """
        try:
            plugin_name = validate_plugin_name(name)
            client = get_client()
            
            success = client.install_plugin(plugin_name)
            
            if success:
                return {
                    "success": True,
                    "message": f"Plugin '{plugin_name}' installation initiated",
                    "plugin_name": plugin_name,
                    "include_dependencies": include_dependencies,
                    "note": "Jenkins may require a restart to complete the installation"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to install plugin '{plugin_name}'",
                    "plugin_name": plugin_name
                }
            
        except JenkinsBuildError as e:
            return {
                "success": False,
                "error": str(e),
                "plugin_name": name
            }
        except Exception as e:
            logger.error(f"Failed to install plugin '{name}': {e}")
            return {
                "success": False,
                "error": str(e),
                "plugin_name": name
            }