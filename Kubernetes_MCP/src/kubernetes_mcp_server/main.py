"""Main entry point for the Kubernetes MCP Server."""

import json
from typing import Optional
from fastmcp import FastMCP

from .config import ServerConfig
from .client import KubernetesClient


def main():
    """Main entry point for the Kubernetes MCP Server."""
    print("Starting Kubernetes MCP Server...")
    
    # Load configuration
    server_config = ServerConfig()
    kube_config = server_config.kubernetes_config
    
    print(f"Namespace: {kube_config.namespace}")
    print(f"Transport: {server_config.transport}")
    print(f"Server: {server_config.host}:{server_config.port}")
    
    # Create FastMCP server
    mcp = FastMCP("Kubernetes MCP Server")
    
    # Create client factory function
    def get_client() -> KubernetesClient:
        """Get Kubernetes client instance."""
        return KubernetesClient(kube_config)
    
    # ==================== Health Check ====================
    
    @mcp.tool()
    def k8s_health_check() -> str:
        """Check the health status of the Kubernetes MCP Server and cluster connection."""
        try:
            client = get_client()
            info = client.get_cluster_info()
            return json.dumps({
                "status": "healthy",
                "cluster": info
            }, indent=2)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            }, indent=2)
    
    # ==================== Cluster Info ====================
    
    @mcp.tool()
    def k8s_get_cluster_info() -> str:
        """Get Kubernetes cluster information including version and node count."""
        client = get_client()
        info = client.get_cluster_info()
        return json.dumps(info, indent=2)
    
    # ==================== Namespace Tools ====================
    
    @mcp.tool()
    def k8s_list_namespaces() -> str:
        """List all Kubernetes namespaces."""
        client = get_client()
        namespaces = client.list_namespaces()
        return json.dumps(namespaces, indent=2)
    
    @mcp.tool()
    def k8s_get_namespace(name: str) -> str:
        """Get details of a specific Kubernetes namespace."""
        client = get_client()
        ns = client.get_namespace(name)
        return json.dumps(ns, indent=2)
    
    @mcp.tool()
    def k8s_create_namespace(name: str, labels: Optional[str] = None) -> str:
        """Create a new Kubernetes namespace. Labels should be JSON string like '{"env": "prod"}'."""
        client = get_client()
        label_dict = json.loads(labels) if labels else None
        result = client.create_namespace(name, label_dict)
        return json.dumps(result, indent=2)
    
    @mcp.tool()
    def k8s_delete_namespace(name: str) -> str:
        """Delete a Kubernetes namespace. WARNING: This will delete all resources in the namespace."""
        client = get_client()
        result = client.delete_namespace(name)
        return json.dumps(result, indent=2)
    
    # ==================== Pod Tools ====================
    
    @mcp.tool()
    def k8s_list_pods(namespace: Optional[str] = None, label_selector: Optional[str] = None) -> str:
        """
        List Kubernetes pods in a namespace. Use '_all' for all namespaces.
        
        Args:
            namespace: Namespace to list pods from. Default is 'default'. Use '_all' for all namespaces.
            label_selector: Filter pods by labels, e.g., 'app=nginx,tier=frontend'
        """
        client = get_client()
        pods = client.list_pods(namespace, label_selector)
        return json.dumps(pods, indent=2)
    
    @mcp.tool()
    def k8s_get_pod(name: str, namespace: Optional[str] = None) -> str:
        """Get detailed information about a specific Kubernetes pod."""
        client = get_client()
        pod = client.get_pod(name, namespace)
        return json.dumps(pod, indent=2)
    
    @mcp.tool()
    def k8s_get_pod_logs(
        name: str,
        namespace: Optional[str] = None,
        container: Optional[str] = None,
        tail_lines: int = 100,
        previous: bool = False
    ) -> str:
        """
        Get logs from a Kubernetes pod.
        
        Args:
            name: Pod name
            namespace: Namespace (default: 'default')
            container: Container name (required if pod has multiple containers)
            tail_lines: Number of lines to return from the end
            previous: Get logs from previous container instance
        """
        client = get_client()
        logs = client.get_pod_logs(name, namespace, container, tail_lines, previous)
        return logs
    
    @mcp.tool()
    def k8s_delete_pod(name: str, namespace: Optional[str] = None) -> str:
        """Delete a Kubernetes pod."""
        client = get_client()
        result = client.delete_pod(name, namespace)
        return json.dumps(result, indent=2)
    
    @mcp.tool()
    def k8s_exec_in_pod(
        name: str,
        command: str,
        namespace: Optional[str] = None,
        container: Optional[str] = None
    ) -> str:
        """
        Execute a command in a Kubernetes pod.
        
        Args:
            name: Pod name
            command: Command to execute (space-separated)
            namespace: Namespace (default: 'default')
            container: Container name (required if pod has multiple containers)
        """
        client = get_client()
        cmd_list = command.split()
        result = client.exec_command(name, cmd_list, namespace, container)
        return result
    
    # ==================== Deployment Tools ====================
    
    @mcp.tool()
    def k8s_list_deployments(namespace: Optional[str] = None) -> str:
        """List Kubernetes deployments in a namespace. Use '_all' for all namespaces."""
        client = get_client()
        deployments = client.list_deployments(namespace)
        return json.dumps(deployments, indent=2)
    
    @mcp.tool()
    def k8s_get_deployment(name: str, namespace: Optional[str] = None) -> str:
        """Get detailed information about a specific Kubernetes deployment."""
        client = get_client()
        deployment = client.get_deployment(name, namespace)
        return json.dumps(deployment, indent=2)
    
    @mcp.tool()
    def k8s_scale_deployment(name: str, replicas: int, namespace: Optional[str] = None) -> str:
        """Scale a Kubernetes deployment to the specified number of replicas."""
        client = get_client()
        result = client.scale_deployment(name, replicas, namespace)
        return json.dumps(result, indent=2)
    
    @mcp.tool()
    def k8s_restart_deployment(name: str, namespace: Optional[str] = None) -> str:
        """Restart a Kubernetes deployment by triggering a rolling restart."""
        client = get_client()
        result = client.restart_deployment(name, namespace)
        return json.dumps(result, indent=2)
    
    @mcp.tool()
    def k8s_delete_deployment(name: str, namespace: Optional[str] = None) -> str:
        """Delete a Kubernetes deployment."""
        client = get_client()
        result = client.delete_deployment(name, namespace)
        return json.dumps(result, indent=2)
    
    # ==================== Service Tools ====================
    
    @mcp.tool()
    def k8s_list_services(namespace: Optional[str] = None) -> str:
        """List Kubernetes services in a namespace. Use '_all' for all namespaces."""
        client = get_client()
        services = client.list_services(namespace)
        return json.dumps(services, indent=2)
    
    @mcp.tool()
    def k8s_get_service(name: str, namespace: Optional[str] = None) -> str:
        """Get detailed information about a specific Kubernetes service."""
        client = get_client()
        service = client.get_service(name, namespace)
        return json.dumps(service, indent=2)
    
    @mcp.tool()
    def k8s_delete_service(name: str, namespace: Optional[str] = None) -> str:
        """Delete a Kubernetes service."""
        client = get_client()
        result = client.delete_service(name, namespace)
        return json.dumps(result, indent=2)
    
    # ==================== ConfigMap Tools ====================
    
    @mcp.tool()
    def k8s_list_configmaps(namespace: Optional[str] = None) -> str:
        """List Kubernetes ConfigMaps in a namespace."""
        client = get_client()
        configmaps = client.list_configmaps(namespace)
        return json.dumps(configmaps, indent=2)
    
    @mcp.tool()
    def k8s_get_configmap(name: str, namespace: Optional[str] = None) -> str:
        """Get detailed information about a specific Kubernetes ConfigMap including its data."""
        client = get_client()
        configmap = client.get_configmap(name, namespace)
        return json.dumps(configmap, indent=2)
    
    @mcp.tool()
    def k8s_delete_configmap(name: str, namespace: Optional[str] = None) -> str:
        """Delete a Kubernetes ConfigMap."""
        client = get_client()
        result = client.delete_configmap(name, namespace)
        return json.dumps(result, indent=2)
    
    # ==================== Secret Tools ====================
    
    @mcp.tool()
    def k8s_list_secrets(namespace: Optional[str] = None) -> str:
        """List Kubernetes Secrets in a namespace (data is not shown for security)."""
        client = get_client()
        secrets = client.list_secrets(namespace)
        return json.dumps(secrets, indent=2)
    
    @mcp.tool()
    def k8s_get_secret(name: str, namespace: Optional[str] = None, decode: bool = False) -> str:
        """
        Get Kubernetes Secret details. Set decode=True to decode base64 data.
        WARNING: Decoded secrets will be visible in plain text.
        """
        client = get_client()
        secret = client.get_secret(name, namespace, decode)
        return json.dumps(secret, indent=2)
    
    # ==================== Node Tools ====================
    
    @mcp.tool()
    def k8s_list_nodes() -> str:
        """List all Kubernetes cluster nodes with their status and resources."""
        client = get_client()
        nodes = client.list_nodes()
        return json.dumps(nodes, indent=2)
    
    @mcp.tool()
    def k8s_get_node(name: str) -> str:
        """Get detailed information about a specific Kubernetes node."""
        client = get_client()
        node = client.get_node(name)
        return json.dumps(node, indent=2)
    
    @mcp.tool()
    def k8s_cordon_node(name: str) -> str:
        """Cordon a Kubernetes node (mark as unschedulable). New pods won't be scheduled on this node."""
        client = get_client()
        result = client.cordon_node(name)
        return json.dumps(result, indent=2)
    
    @mcp.tool()
    def k8s_uncordon_node(name: str) -> str:
        """Uncordon a Kubernetes node (mark as schedulable). New pods can be scheduled on this node."""
        client = get_client()
        result = client.uncordon_node(name)
        return json.dumps(result, indent=2)
    
    # ==================== Event Tools ====================
    
    @mcp.tool()
    def k8s_list_events(namespace: Optional[str] = None, limit: int = 50) -> str:
        """
        List recent Kubernetes events in a namespace. Use '_all' for all namespaces.
        Events are sorted by last occurrence time.
        """
        client = get_client()
        events = client.list_events(namespace, limit)
        return json.dumps(events, indent=2)
    
    # ==================== Ingress Tools ====================
    
    @mcp.tool()
    def k8s_list_ingresses(namespace: Optional[str] = None) -> str:
        """List Kubernetes Ingress resources in a namespace. Use '_all' for all namespaces."""
        client = get_client()
        ingresses = client.list_ingresses(namespace)
        return json.dumps(ingresses, indent=2)
    
    # ==================== StatefulSet Tools ====================
    
    @mcp.tool()
    def k8s_list_statefulsets(namespace: Optional[str] = None) -> str:
        """List Kubernetes StatefulSets in a namespace. Use '_all' for all namespaces."""
        client = get_client()
        statefulsets = client.list_statefulsets(namespace)
        return json.dumps(statefulsets, indent=2)
    
    # ==================== DaemonSet Tools ====================
    
    @mcp.tool()
    def k8s_list_daemonsets(namespace: Optional[str] = None) -> str:
        """List Kubernetes DaemonSets in a namespace. Use '_all' for all namespaces."""
        client = get_client()
        daemonsets = client.list_daemonsets(namespace)
        return json.dumps(daemonsets, indent=2)
    
    # ==================== Job Tools ====================
    
    @mcp.tool()
    def k8s_list_jobs(namespace: Optional[str] = None) -> str:
        """List Kubernetes Jobs in a namespace. Use '_all' for all namespaces."""
        client = get_client()
        jobs = client.list_jobs(namespace)
        return json.dumps(jobs, indent=2)
    
    # ==================== CronJob Tools ====================
    
    @mcp.tool()
    def k8s_list_cronjobs(namespace: Optional[str] = None) -> str:
        """List Kubernetes CronJobs in a namespace. Use '_all' for all namespaces."""
        client = get_client()
        cronjobs = client.list_cronjobs(namespace)
        return json.dumps(cronjobs, indent=2)
    
    # ==================== PersistentVolume Tools ====================
    
    @mcp.tool()
    def k8s_list_pvs() -> str:
        """List all Kubernetes PersistentVolumes in the cluster."""
        client = get_client()
        pvs = client.list_pvs()
        return json.dumps(pvs, indent=2)
    
    @mcp.tool()
    def k8s_list_pvcs(namespace: Optional[str] = None) -> str:
        """List Kubernetes PersistentVolumeClaims in a namespace. Use '_all' for all namespaces."""
        client = get_client()
        pvcs = client.list_pvcs(namespace)
        return json.dumps(pvcs, indent=2)
    
    # ==================== Start Server ====================
    
    print(f"Kubernetes MCP Server starting on {server_config.host}:{server_config.port} ({server_config.transport} transport)")
    print("Registered tools: 35 (all prefixed with k8s_)")
    
    # Run the server
    mcp.run(
        transport=server_config.transport,
        host=server_config.host,
        port=server_config.port,
    )


if __name__ == "__main__":
    main()