"""Kubernetes client wrapper for MCP Server."""

from typing import Optional, Dict, List, Any
from kubernetes import client, config as k8s_config
from kubernetes.client.rest import ApiException

from .config import KubernetesConfig


class KubernetesClient:
    """Wrapper for Kubernetes Python client."""
    
    def __init__(self, kube_config: KubernetesConfig):
        """Initialize Kubernetes client."""
        self.kube_config = kube_config
        self._core_v1: Optional[client.CoreV1Api] = None
        self._apps_v1: Optional[client.AppsV1Api] = None
        self._batch_v1: Optional[client.BatchV1Api] = None
        self._networking_v1: Optional[client.NetworkingV1Api] = None
        self._rbac_v1: Optional[client.RbacAuthorizationV1Api] = None
        self._custom_objects: Optional[client.CustomObjectsApi] = None
        self._initialized = False
    
    def _initialize(self):
        """Initialize the Kubernetes client."""
        if self._initialized:
            return
        
        try:
            # Load kubeconfig
            if self.kube_config.kubeconfig:
                k8s_config.load_kube_config(
                    config_file=self.kube_config.kubeconfig,
                    context=self.kube_config.context
                )
            else:
                # Try in-cluster config first, then kubeconfig
                try:
                    k8s_config.load_incluster_config()
                except k8s_config.ConfigException:
                    k8s_config.load_kube_config(context=self.kube_config.context)
            
            # Initialize API clients
            self._core_v1 = client.CoreV1Api()
            self._apps_v1 = client.AppsV1Api()
            self._batch_v1 = client.BatchV1Api()
            self._networking_v1 = client.NetworkingV1Api()
            self._rbac_v1 = client.RbacAuthorizationV1Api()
            self._custom_objects = client.CustomObjectsApi()
            self._initialized = True
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Kubernetes client: {e}")
    
    @property
    def core_v1(self) -> client.CoreV1Api:
        """Get Core V1 API client."""
        self._initialize()
        return self._core_v1
    
    @property
    def apps_v1(self) -> client.AppsV1Api:
        """Get Apps V1 API client."""
        self._initialize()
        return self._apps_v1
    
    @property
    def batch_v1(self) -> client.BatchV1Api:
        """Get Batch V1 API client."""
        self._initialize()
        return self._batch_v1
    
    @property
    def networking_v1(self) -> client.NetworkingV1Api:
        """Get Networking V1 API client."""
        self._initialize()
        return self._networking_v1
    
    @property
    def rbac_v1(self) -> client.RbacAuthorizationV1Api:
        """Get RBAC V1 API client."""
        self._initialize()
        return self._rbac_v1
    
    # ==================== Namespace Operations ====================
    
    def list_namespaces(self) -> List[Dict[str, Any]]:
        """List all namespaces."""
        result = self.core_v1.list_namespace()
        return [
            {
                "name": ns.metadata.name,
                "status": ns.status.phase,
                "created": ns.metadata.creation_timestamp.isoformat() if ns.metadata.creation_timestamp else None,
                "labels": ns.metadata.labels or {}
            }
            for ns in result.items
        ]
    
    def get_namespace(self, name: str) -> Dict[str, Any]:
        """Get namespace details."""
        ns = self.core_v1.read_namespace(name)
        return {
            "name": ns.metadata.name,
            "status": ns.status.phase,
            "created": ns.metadata.creation_timestamp.isoformat() if ns.metadata.creation_timestamp else None,
            "labels": ns.metadata.labels or {},
            "annotations": ns.metadata.annotations or {}
        }
    
    def create_namespace(self, name: str, labels: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create a namespace."""
        body = client.V1Namespace(
            metadata=client.V1ObjectMeta(name=name, labels=labels)
        )
        ns = self.core_v1.create_namespace(body)
        return {"name": ns.metadata.name, "status": "created"}
    
    def delete_namespace(self, name: str) -> Dict[str, Any]:
        """Delete a namespace."""
        self.core_v1.delete_namespace(name)
        return {"name": name, "status": "deleted"}
    
    # ==================== Pod Operations ====================
    
    def list_pods(self, namespace: Optional[str] = None, label_selector: Optional[str] = None) -> List[Dict[str, Any]]:
        """List pods in a namespace or all namespaces."""
        ns = namespace or self.kube_config.namespace
        if ns == "_all":
            result = self.core_v1.list_pod_for_all_namespaces(label_selector=label_selector)
        else:
            result = self.core_v1.list_namespaced_pod(ns, label_selector=label_selector)
        
        return [
            {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": pod.status.phase,
                "ready": self._get_pod_ready_status(pod),
                "restarts": self._get_pod_restarts(pod),
                "node": pod.spec.node_name,
                "ip": pod.status.pod_ip,
                "created": pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None,
                "containers": [c.name for c in pod.spec.containers]
            }
            for pod in result.items
        ]
    
    def get_pod(self, name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Get pod details."""
        ns = namespace or self.kube_config.namespace
        pod = self.core_v1.read_namespaced_pod(name, ns)
        return {
            "name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "status": pod.status.phase,
            "ready": self._get_pod_ready_status(pod),
            "restarts": self._get_pod_restarts(pod),
            "node": pod.spec.node_name,
            "ip": pod.status.pod_ip,
            "host_ip": pod.status.host_ip,
            "created": pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None,
            "labels": pod.metadata.labels or {},
            "annotations": pod.metadata.annotations or {},
            "containers": [
                {
                    "name": c.name,
                    "image": c.image,
                    "ports": [{"containerPort": p.container_port, "protocol": p.protocol} for p in (c.ports or [])]
                }
                for c in pod.spec.containers
            ],
            "conditions": [
                {"type": c.type, "status": c.status, "reason": c.reason}
                for c in (pod.status.conditions or [])
            ]
        }
    
    def get_pod_logs(self, name: str, namespace: Optional[str] = None, 
                     container: Optional[str] = None, tail_lines: int = 100,
                     previous: bool = False) -> str:
        """Get pod logs."""
        ns = namespace or self.kube_config.namespace
        return self.core_v1.read_namespaced_pod_log(
            name, ns,
            container=container,
            tail_lines=tail_lines,
            previous=previous
        )
    
    def delete_pod(self, name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Delete a pod."""
        ns = namespace or self.kube_config.namespace
        self.core_v1.delete_namespaced_pod(name, ns)
        return {"name": name, "namespace": ns, "status": "deleted"}
    
    def exec_command(self, name: str, command: List[str], 
                    namespace: Optional[str] = None, container: Optional[str] = None) -> str:
        """Execute command in a pod."""
        from kubernetes.stream import stream
        ns = namespace or self.kube_config.namespace
        
        resp = stream(
            self.core_v1.connect_get_namespaced_pod_exec,
            name, ns,
            command=command,
            container=container,
            stderr=True, stdin=False,
            stdout=True, tty=False
        )
        return resp
    
    # ==================== Deployment Operations ====================
    
    def list_deployments(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """List deployments."""
        ns = namespace or self.kube_config.namespace
        if ns == "_all":
            result = self.apps_v1.list_deployment_for_all_namespaces()
        else:
            result = self.apps_v1.list_namespaced_deployment(ns)
        
        return [
            {
                "name": dep.metadata.name,
                "namespace": dep.metadata.namespace,
                "replicas": dep.spec.replicas,
                "available": dep.status.available_replicas or 0,
                "ready": dep.status.ready_replicas or 0,
                "updated": dep.status.updated_replicas or 0,
                "created": dep.metadata.creation_timestamp.isoformat() if dep.metadata.creation_timestamp else None,
                "images": [c.image for c in dep.spec.template.spec.containers]
            }
            for dep in result.items
        ]
    
    def get_deployment(self, name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Get deployment details."""
        ns = namespace or self.kube_config.namespace
        dep = self.apps_v1.read_namespaced_deployment(name, ns)
        return {
            "name": dep.metadata.name,
            "namespace": dep.metadata.namespace,
            "replicas": dep.spec.replicas,
            "available": dep.status.available_replicas or 0,
            "ready": dep.status.ready_replicas or 0,
            "updated": dep.status.updated_replicas or 0,
            "created": dep.metadata.creation_timestamp.isoformat() if dep.metadata.creation_timestamp else None,
            "labels": dep.metadata.labels or {},
            "selector": dep.spec.selector.match_labels or {},
            "strategy": dep.spec.strategy.type,
            "containers": [
                {
                    "name": c.name,
                    "image": c.image,
                    "resources": {
                        "requests": c.resources.requests if c.resources else None,
                        "limits": c.resources.limits if c.resources else None
                    }
                }
                for c in dep.spec.template.spec.containers
            ],
            "conditions": [
                {"type": c.type, "status": c.status, "reason": c.reason, "message": c.message}
                for c in (dep.status.conditions or [])
            ]
        }
    
    def scale_deployment(self, name: str, replicas: int, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Scale a deployment."""
        ns = namespace or self.kube_config.namespace
        body = {"spec": {"replicas": replicas}}
        dep = self.apps_v1.patch_namespaced_deployment_scale(name, ns, body)
        return {
            "name": name,
            "namespace": ns,
            "replicas": replicas,
            "status": "scaled"
        }
    
    def restart_deployment(self, name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Restart a deployment by updating its annotation."""
        import datetime
        ns = namespace or self.kube_config.namespace
        now = datetime.datetime.utcnow().isoformat()
        body = {
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "kubectl.kubernetes.io/restartedAt": now
                        }
                    }
                }
            }
        }
        self.apps_v1.patch_namespaced_deployment(name, ns, body)
        return {"name": name, "namespace": ns, "status": "restarting"}
    
    def delete_deployment(self, name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Delete a deployment."""
        ns = namespace or self.kube_config.namespace
        self.apps_v1.delete_namespaced_deployment(name, ns)
        return {"name": name, "namespace": ns, "status": "deleted"}
    
    # ==================== Service Operations ====================
    
    def list_services(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """List services."""
        ns = namespace or self.kube_config.namespace
        if ns == "_all":
            result = self.core_v1.list_service_for_all_namespaces()
        else:
            result = self.core_v1.list_namespaced_service(ns)
        
        return [
            {
                "name": svc.metadata.name,
                "namespace": svc.metadata.namespace,
                "type": svc.spec.type,
                "cluster_ip": svc.spec.cluster_ip,
                "external_ip": svc.spec.external_i_ps[0] if svc.spec.external_i_ps else None,
                "ports": [
                    {"port": p.port, "targetPort": p.target_port, "protocol": p.protocol, "nodePort": p.node_port}
                    for p in (svc.spec.ports or [])
                ],
                "selector": svc.spec.selector or {}
            }
            for svc in result.items
        ]
    
    def get_service(self, name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Get service details."""
        ns = namespace or self.kube_config.namespace
        svc = self.core_v1.read_namespaced_service(name, ns)
        return {
            "name": svc.metadata.name,
            "namespace": svc.metadata.namespace,
            "type": svc.spec.type,
            "cluster_ip": svc.spec.cluster_ip,
            "external_ips": svc.spec.external_i_ps or [],
            "ports": [
                {"port": p.port, "targetPort": p.target_port, "protocol": p.protocol, "nodePort": p.node_port}
                for p in (svc.spec.ports or [])
            ],
            "selector": svc.spec.selector or {},
            "labels": svc.metadata.labels or {},
            "created": svc.metadata.creation_timestamp.isoformat() if svc.metadata.creation_timestamp else None
        }
    
    def delete_service(self, name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Delete a service."""
        ns = namespace or self.kube_config.namespace
        self.core_v1.delete_namespaced_service(name, ns)
        return {"name": name, "namespace": ns, "status": "deleted"}
    
    # ==================== ConfigMap Operations ====================
    
    def list_configmaps(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """List ConfigMaps."""
        ns = namespace or self.kube_config.namespace
        result = self.core_v1.list_namespaced_config_map(ns)
        return [
            {
                "name": cm.metadata.name,
                "namespace": cm.metadata.namespace,
                "data_keys": list(cm.data.keys()) if cm.data else [],
                "created": cm.metadata.creation_timestamp.isoformat() if cm.metadata.creation_timestamp else None
            }
            for cm in result.items
        ]
    
    def get_configmap(self, name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Get ConfigMap details."""
        ns = namespace or self.kube_config.namespace
        cm = self.core_v1.read_namespaced_config_map(name, ns)
        return {
            "name": cm.metadata.name,
            "namespace": cm.metadata.namespace,
            "data": cm.data or {},
            "labels": cm.metadata.labels or {},
            "created": cm.metadata.creation_timestamp.isoformat() if cm.metadata.creation_timestamp else None
        }
    
    def delete_configmap(self, name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Delete a ConfigMap."""
        ns = namespace or self.kube_config.namespace
        self.core_v1.delete_namespaced_config_map(name, ns)
        return {"name": name, "namespace": ns, "status": "deleted"}
    
    # ==================== Secret Operations ====================
    
    def list_secrets(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Secrets (without data)."""
        ns = namespace or self.kube_config.namespace
        result = self.core_v1.list_namespaced_secret(ns)
        return [
            {
                "name": s.metadata.name,
                "namespace": s.metadata.namespace,
                "type": s.type,
                "data_keys": list(s.data.keys()) if s.data else [],
                "created": s.metadata.creation_timestamp.isoformat() if s.metadata.creation_timestamp else None
            }
            for s in result.items
        ]
    
    def get_secret(self, name: str, namespace: Optional[str] = None, decode: bool = False) -> Dict[str, Any]:
        """Get Secret details (optionally decode data)."""
        import base64
        ns = namespace or self.kube_config.namespace
        s = self.core_v1.read_namespaced_secret(name, ns)
        
        data = {}
        if s.data:
            if decode:
                data = {k: base64.b64decode(v).decode('utf-8', errors='replace') for k, v in s.data.items()}
            else:
                data = {"keys": list(s.data.keys()), "note": "Data is base64 encoded. Use decode=True to decode."}
        
        return {
            "name": s.metadata.name,
            "namespace": s.metadata.namespace,
            "type": s.type,
            "data": data,
            "labels": s.metadata.labels or {},
            "created": s.metadata.creation_timestamp.isoformat() if s.metadata.creation_timestamp else None
        }
    
    # ==================== Node Operations ====================
    
    def list_nodes(self) -> List[Dict[str, Any]]:
        """List cluster nodes."""
        result = self.core_v1.list_node()
        return [
            {
                "name": node.metadata.name,
                "status": self._get_node_status(node),
                "roles": self._get_node_roles(node),
                "version": node.status.node_info.kubelet_version,
                "os": node.status.node_info.os_image,
                "cpu": node.status.capacity.get('cpu'),
                "memory": node.status.capacity.get('memory'),
                "pods": node.status.capacity.get('pods'),
                "created": node.metadata.creation_timestamp.isoformat() if node.metadata.creation_timestamp else None
            }
            for node in result.items
        ]
    
    def get_node(self, name: str) -> Dict[str, Any]:
        """Get node details."""
        node = self.core_v1.read_node(name)
        return {
            "name": node.metadata.name,
            "status": self._get_node_status(node),
            "roles": self._get_node_roles(node),
            "version": node.status.node_info.kubelet_version,
            "os": node.status.node_info.os_image,
            "kernel": node.status.node_info.kernel_version,
            "container_runtime": node.status.node_info.container_runtime_version,
            "capacity": {
                "cpu": node.status.capacity.get('cpu'),
                "memory": node.status.capacity.get('memory'),
                "pods": node.status.capacity.get('pods')
            },
            "allocatable": {
                "cpu": node.status.allocatable.get('cpu'),
                "memory": node.status.allocatable.get('memory'),
                "pods": node.status.allocatable.get('pods')
            },
            "conditions": [
                {"type": c.type, "status": c.status, "reason": c.reason}
                for c in (node.status.conditions or [])
            ],
            "labels": node.metadata.labels or {},
            "taints": [
                {"key": t.key, "value": t.value, "effect": t.effect}
                for t in (node.spec.taints or [])
            ]
        }
    
    def cordon_node(self, name: str) -> Dict[str, Any]:
        """Cordon a node (mark as unschedulable)."""
        body = {"spec": {"unschedulable": True}}
        self.core_v1.patch_node(name, body)
        return {"name": name, "status": "cordoned"}
    
    def uncordon_node(self, name: str) -> Dict[str, Any]:
        """Uncordon a node (mark as schedulable)."""
        body = {"spec": {"unschedulable": False}}
        self.core_v1.patch_node(name, body)
        return {"name": name, "status": "uncordoned"}
    
    # ==================== Events ====================
    
    def list_events(self, namespace: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List events."""
        ns = namespace or self.kube_config.namespace
        if ns == "_all":
            result = self.core_v1.list_event_for_all_namespaces(limit=limit)
        else:
            result = self.core_v1.list_namespaced_event(ns, limit=limit)
        
        return [
            {
                "namespace": e.metadata.namespace,
                "name": e.involved_object.name,
                "kind": e.involved_object.kind,
                "type": e.type,
                "reason": e.reason,
                "message": e.message,
                "count": e.count,
                "first_seen": e.first_timestamp.isoformat() if e.first_timestamp else None,
                "last_seen": e.last_timestamp.isoformat() if e.last_timestamp else None
            }
            for e in sorted(result.items, key=lambda x: x.last_timestamp or x.first_timestamp or "", reverse=True)
        ]
    
    # ==================== Ingress Operations ====================
    
    def list_ingresses(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """List ingresses."""
        ns = namespace or self.kube_config.namespace
        if ns == "_all":
            result = self.networking_v1.list_ingress_for_all_namespaces()
        else:
            result = self.networking_v1.list_namespaced_ingress(ns)
        
        return [
            {
                "name": ing.metadata.name,
                "namespace": ing.metadata.namespace,
                "hosts": [rule.host for rule in (ing.spec.rules or [])],
                "class": ing.spec.ingress_class_name,
                "created": ing.metadata.creation_timestamp.isoformat() if ing.metadata.creation_timestamp else None
            }
            for ing in result.items
        ]
    
    # ==================== StatefulSet Operations ====================
    
    def list_statefulsets(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """List StatefulSets."""
        ns = namespace or self.kube_config.namespace
        if ns == "_all":
            result = self.apps_v1.list_stateful_set_for_all_namespaces()
        else:
            result = self.apps_v1.list_namespaced_stateful_set(ns)
        
        return [
            {
                "name": ss.metadata.name,
                "namespace": ss.metadata.namespace,
                "replicas": ss.spec.replicas,
                "ready": ss.status.ready_replicas or 0,
                "created": ss.metadata.creation_timestamp.isoformat() if ss.metadata.creation_timestamp else None
            }
            for ss in result.items
        ]
    
    # ==================== DaemonSet Operations ====================
    
    def list_daemonsets(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """List DaemonSets."""
        ns = namespace or self.kube_config.namespace
        if ns == "_all":
            result = self.apps_v1.list_daemon_set_for_all_namespaces()
        else:
            result = self.apps_v1.list_namespaced_daemon_set(ns)
        
        return [
            {
                "name": ds.metadata.name,
                "namespace": ds.metadata.namespace,
                "desired": ds.status.desired_number_scheduled,
                "current": ds.status.current_number_scheduled,
                "ready": ds.status.number_ready,
                "created": ds.metadata.creation_timestamp.isoformat() if ds.metadata.creation_timestamp else None
            }
            for ds in result.items
        ]
    
    # ==================== Job Operations ====================
    
    def list_jobs(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Jobs."""
        ns = namespace or self.kube_config.namespace
        if ns == "_all":
            result = self.batch_v1.list_job_for_all_namespaces()
        else:
            result = self.batch_v1.list_namespaced_job(ns)
        
        return [
            {
                "name": job.metadata.name,
                "namespace": job.metadata.namespace,
                "completions": job.spec.completions,
                "succeeded": job.status.succeeded or 0,
                "failed": job.status.failed or 0,
                "active": job.status.active or 0,
                "created": job.metadata.creation_timestamp.isoformat() if job.metadata.creation_timestamp else None
            }
            for job in result.items
        ]
    
    # ==================== CronJob Operations ====================
    
    def list_cronjobs(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """List CronJobs."""
        ns = namespace or self.kube_config.namespace
        if ns == "_all":
            result = self.batch_v1.list_cron_job_for_all_namespaces()
        else:
            result = self.batch_v1.list_namespaced_cron_job(ns)
        
        return [
            {
                "name": cj.metadata.name,
                "namespace": cj.metadata.namespace,
                "schedule": cj.spec.schedule,
                "suspend": cj.spec.suspend,
                "active": len(cj.status.active) if cj.status.active else 0,
                "last_schedule": cj.status.last_schedule_time.isoformat() if cj.status.last_schedule_time else None
            }
            for cj in result.items
        ]
    
    # ==================== PersistentVolume Operations ====================
    
    def list_pvs(self) -> List[Dict[str, Any]]:
        """List PersistentVolumes."""
        result = self.core_v1.list_persistent_volume()
        return [
            {
                "name": pv.metadata.name,
                "capacity": pv.spec.capacity.get('storage') if pv.spec.capacity else None,
                "access_modes": pv.spec.access_modes,
                "reclaim_policy": pv.spec.persistent_volume_reclaim_policy,
                "status": pv.status.phase,
                "claim": f"{pv.spec.claim_ref.namespace}/{pv.spec.claim_ref.name}" if pv.spec.claim_ref else None,
                "storage_class": pv.spec.storage_class_name
            }
            for pv in result.items
        ]
    
    def list_pvcs(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """List PersistentVolumeClaims."""
        ns = namespace or self.kube_config.namespace
        if ns == "_all":
            result = self.core_v1.list_persistent_volume_claim_for_all_namespaces()
        else:
            result = self.core_v1.list_namespaced_persistent_volume_claim(ns)
        
        return [
            {
                "name": pvc.metadata.name,
                "namespace": pvc.metadata.namespace,
                "status": pvc.status.phase,
                "volume": pvc.spec.volume_name,
                "capacity": pvc.status.capacity.get('storage') if pvc.status.capacity else None,
                "access_modes": pvc.spec.access_modes,
                "storage_class": pvc.spec.storage_class_name
            }
            for pvc in result.items
        ]
    
    # ==================== Helper Methods ====================
    
    def _get_pod_ready_status(self, pod) -> str:
        """Get pod ready status as string."""
        if not pod.status.container_statuses:
            return "0/0"
        ready = sum(1 for c in pod.status.container_statuses if c.ready)
        total = len(pod.status.container_statuses)
        return f"{ready}/{total}"
    
    def _get_pod_restarts(self, pod) -> int:
        """Get total pod restarts."""
        if not pod.status.container_statuses:
            return 0
        return sum(c.restart_count for c in pod.status.container_statuses)
    
    def _get_node_status(self, node) -> str:
        """Get node status."""
        for condition in (node.status.conditions or []):
            if condition.type == "Ready":
                return "Ready" if condition.status == "True" else "NotReady"
        return "Unknown"
    
    def _get_node_roles(self, node) -> List[str]:
        """Get node roles from labels."""
        roles = []
        for label in (node.metadata.labels or {}):
            if label.startswith("node-role.kubernetes.io/"):
                roles.append(label.split("/")[1])
        return roles if roles else ["<none>"]
    
    # ==================== Cluster Info ====================
    
    def get_cluster_info(self) -> Dict[str, Any]:
        """Get cluster information."""
        # Get version info
        version_api = client.VersionApi()
        version = version_api.get_code()
        
        # Get node count
        nodes = self.core_v1.list_node()
        
        # Get namespace count
        namespaces = self.core_v1.list_namespace()
        
        return {
            "version": {
                "major": version.major,
                "minor": version.minor,
                "git_version": version.git_version,
                "platform": version.platform
            },
            "nodes": len(nodes.items),
            "namespaces": len(namespaces.items),
            "context": self.kube_config.context or "current"
        }