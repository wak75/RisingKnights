# Kubernetes MCP Server

MCP (Model Context Protocol) Server for Kubernetes cluster management. This server provides comprehensive tools for managing Kubernetes resources through AI assistants.

## Features

### Tools (35 total)

#### Cluster & Namespace
- `health_check` - Check server and cluster health
- `get_cluster_info` - Get cluster version and stats
- `list_namespaces` - List all namespaces
- `get_namespace` - Get namespace details
- `create_namespace` - Create a namespace
- `delete_namespace` - Delete a namespace

#### Pods
- `list_pods` - List pods (with filtering)
- `get_pod` - Get pod details
- `get_pod_logs` - Get pod logs
- `delete_pod` - Delete a pod
- `exec_in_pod` - Execute command in pod

#### Deployments
- `list_deployments` - List deployments
- `get_deployment` - Get deployment details
- `scale_deployment` - Scale deployment replicas
- `restart_deployment` - Rolling restart
- `delete_deployment` - Delete deployment

#### Services
- `list_services` - List services
- `get_service` - Get service details
- `delete_service` - Delete service

#### ConfigMaps & Secrets
- `list_configmaps` - List ConfigMaps
- `get_configmap` - Get ConfigMap with data
- `delete_configmap` - Delete ConfigMap
- `list_secrets` - List Secrets
- `get_secret` - Get Secret (with decode option)

#### Nodes
- `list_nodes` - List cluster nodes
- `get_node` - Get node details
- `cordon_node` - Mark node unschedulable
- `uncordon_node` - Mark node schedulable

#### Workloads
- `list_statefulsets` - List StatefulSets
- `list_daemonsets` - List DaemonSets
- `list_jobs` - List Jobs
- `list_cronjobs` - List CronJobs

#### Storage
- `list_pvs` - List PersistentVolumes
- `list_pvcs` - List PersistentVolumeClaims

#### Events & Networking
- `list_events` - List cluster events
- `list_ingresses` - List Ingresses

## Installation

```bash
cd Kubernetes_MCP

# Create virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e .
```

## Configuration

Copy `.env` and configure:

```bash
cp .env.example .env
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `KUBECONFIG` | Path to kubeconfig file | ~/.kube/config |
| `KUBE_CONTEXT` | Kubernetes context to use | Current context |
| `KUBE_NAMESPACE` | Default namespace | default |
| `SERVER_HOST` | Server bind address | 0.0.0.0 |
| `SERVER_PORT` | Server port | 8001 |
| `TRANSPORT` | Transport mode (sse/stdio) | sse |

## Usage

### Start the Server

```bash
kubernetes-mcp-server
```

Or run directly:
```bash
python -m kubernetes_mcp_server.main
```

### Connect to Orchestrator

Add to Orchestrator's `.env`:
```env
KUBERNETES_MCP_URL=http://localhost:8001/sse
KUBERNETES_MCP_ENABLED=true
```

## Example Operations

### List all pods in kube-system
```
"List all pods in the kube-system namespace"
```

### Scale a deployment
```
"Scale the nginx deployment to 5 replicas"
```

### Get pod logs
```
"Show me the logs from the nginx-pod in default namespace"
```

### Check node status
```
"What's the status of all cluster nodes?"
```

## Requirements

- Python 3.10+
- Kubernetes cluster access (kubeconfig or in-cluster)
- kubectl configured (for kubeconfig)

## License

MIT