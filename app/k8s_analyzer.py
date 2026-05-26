import os
import base64
import tempfile
import time
import json
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import yaml
try:
    import requests as _requests
except ImportError:
    _requests = None


class GrafanaMCPClient:
    """
    Klient pro Grafana HTTP API — query Prometheus, Loki, Alerting.
    Název zachován pro kompatibilitu s app.py, ale používá Grafana REST API přímo
    (bez MCP protokolu — jednodušší a spolehlivější).
    """

    def __init__(self, grafana_url: str, token: str):
        self.url = grafana_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def is_available(self) -> bool:
        if _requests is None:
            return False
        try:
            r = _requests.get(f"{self.url}/api/health", headers=self.headers, timeout=3, verify=False)
            return r.status_code == 200
        except Exception:
            return False

    def get_prometheus_datasource_uid(self) -> str | None:
        """Vrátí UID prvního Prometheus datasource."""
        if _requests is None:
            return None
        try:
            r = _requests.get(
                f"{self.url}/api/datasources",
                headers=self.headers, timeout=5, verify=False
            )
            r.raise_for_status()
            for ds in r.json():
                if ds.get("type") in ("prometheus", "thanos"):
                    return ds.get("uid")
        except Exception as e:
            print(f"GrafanaAPI get_datasources failed: {e}")
        return None

    def _query_prometheus(self, uid: str, expr: str) -> str | None:
        """Spustí instant PromQL dotaz přes Grafana proxy."""
        if _requests is None:
            return None
        try:
            import urllib.parse
            params = {"query": expr}
            r = _requests.get(
                f"{self.url}/api/datasources/proxy/uid/{uid}/api/v1/query",
                params=params,
                headers=self.headers,
                timeout=8,
                verify=False,
            )
            r.raise_for_status()
            data = r.json()
            results = data.get("data", {}).get("result", [])
            if not results:
                return None
            lines = []
            for item in results[:10]:
                metric = item.get("metric", {})
                value = item.get("value", [None, None])[1]
                # Prefer FQDN nodename (from node_uname_info join) > pod > node
                # Fall back to instance with port stripped
                label = metric.get("nodename") or metric.get("pod") or metric.get("node")
                if not label:
                    raw = metric.get("instance", "")
                    label = raw.rsplit(":", 1)[0] if raw else str(metric)
                ns = metric.get("namespace", "")
                ns_str = f" ({ns})" if ns else ""
                try:
                    lines.append(f"  {label}{ns_str}: {float(value):.1f}")
                except Exception:
                    lines.append(f"  {label}{ns_str}: {value}")
            return "\n".join(lines)
        except Exception as e:
            print(f"GrafanaAPI query_prometheus failed ({expr[:40]}): {e}")
            return None

    def has_cluster_label(self, prometheus_uid: str) -> bool:
        """Vrátí True pokud Prometheus obsahuje label 'cluster' (multi-cluster setup)."""
        if _requests is None:
            return False
        try:
            r = _requests.get(
                f"{self.url}/api/datasources/proxy/uid/{prometheus_uid}/api/v1/labels",
                headers=self.headers, timeout=5, verify=False
            )
            r.raise_for_status()
            return "cluster" in r.json().get("data", [])
        except Exception:
            return False

    def get_cluster_metrics_summary(self, prometheus_uid: str, cluster: str = None) -> dict:
        """
        Vrátí metriky z Prometheus. Pokud je zadán 'cluster', přidá cluster label
        do všech PromQL selektorů — nutné pro multi-cluster Prometheus.
        """
        metrics = {}
        cl_extra = f', cluster="{cluster}"' if cluster else ''   # ', cluster="czplskbe1001"'

        # Node CPU usage % — join with node_uname_info to get FQDN nodename
        # (node_cpu_seconds_total carries instance=IP:port; node_uname_info maps it to nodename FQDN)
        if cluster:
            cpu_expr = (
                f'topk(5, 100 * sum by (nodename) ('
                f'rate(node_cpu_seconds_total{{mode!="idle",cluster="{cluster}"}}[5m])'
                f' * on(instance) group_left(nodename) node_uname_info{{cluster="{cluster}"}})'
                f' / sum by (nodename) ('
                f'rate(node_cpu_seconds_total{{cluster="{cluster}"}}[5m])'
                f' * on(instance) group_left(nodename) node_uname_info{{cluster="{cluster}"}})'
                f')'
            )
        else:
            cpu_expr = (
                'topk(5, 100 * sum by (nodename) ('
                'rate(node_cpu_seconds_total{mode!="idle"}[5m])'
                ' * on(instance) group_left(nodename) node_uname_info)'
                ' / sum by (nodename) ('
                'rate(node_cpu_seconds_total[5m])'
                ' * on(instance) group_left(nodename) node_uname_info)'
                ')'
            )
        cpu = self._query_prometheus(prometheus_uid, cpu_expr)
        if cpu:
            metrics["cpu_usage_per_node"] = cpu

        # Node memory usage % — join with node_uname_info for FQDN nodename
        if cluster:
            mem_expr = (
                f'topk(5, 100 * (1 -'
                f' sum by (nodename) (node_memory_MemAvailable_bytes{{cluster="{cluster}"}}'
                f' * on(instance) group_left(nodename) node_uname_info{{cluster="{cluster}"}})'
                f' / sum by (nodename) (node_memory_MemTotal_bytes{{cluster="{cluster}"}}'
                f' * on(instance) group_left(nodename) node_uname_info{{cluster="{cluster}"}}'
                f')))'
            )
        else:
            mem_expr = (
                'topk(5, 100 * (1 -'
                ' sum by (nodename) (node_memory_MemAvailable_bytes'
                ' * on(instance) group_left(nodename) node_uname_info)'
                ' / sum by (nodename) (node_memory_MemTotal_bytes'
                ' * on(instance) group_left(nodename) node_uname_info)'
                '))'
            )
        mem = self._query_prometheus(prometheus_uid, mem_expr)
        if mem:
            metrics["memory_usage_per_node"] = mem

        # Top 5 pods by CPU (millicores)
        top_cpu = self._query_prometheus(
            prometheus_uid,
            f'topk(5, sum by (pod, namespace) (rate(container_cpu_usage_seconds_total{{container!="",pod!=""{cl_extra}}}[5m])) * 1000)'
        )
        if top_cpu:
            metrics["top_cpu_pods"] = top_cpu

        # Top 5 pods by Memory (MiB)
        top_mem = self._query_prometheus(
            prometheus_uid,
            f'topk(5, sum by (pod, namespace) (container_memory_working_set_bytes{{container!="",pod!=""{cl_extra}}}) / 1024 / 1024)'
        )
        if top_mem:
            metrics["top_memory_pods"] = top_mem

        return metrics

    def get_loki_datasource_uid(self) -> str | None:
        """Vrátí UID Loki datasource z Grafany."""
        if _requests is None:
            return None
        try:
            r = _requests.get(
                f"{self.url}/api/datasources",
                headers=self.headers, timeout=5, verify=False
            )
            r.raise_for_status()
            for ds in r.json():
                if ds.get("type") == "loki":
                    return ds.get("uid")
        except Exception as e:
            print(f"GrafanaAPI get_loki_datasource_uid failed: {e}")
        return None

    def create_loki_client(self) -> 'LokiClient | None':
        """Vrátí LokiClient napojený přes Grafana datasource proxy."""
        uid = self.get_loki_datasource_uid()
        if not uid:
            return None
        proxy_url = f"{self.url}/api/datasources/proxy/uid/{uid}"
        client = LokiClient(proxy_url, verify_ssl=False, headers=self.headers)
        # Zjisti jestli Loki obsahuje cluster label
        labels = client.get_labels()
        client.has_cluster_label = 'cluster' in labels
        return client

    def get_firing_alerts(self) -> str | None:
        """Vrátí firing alerty z Grafana Alerting API."""
        if _requests is None:
            return None
        try:
            r = _requests.get(
                f"{self.url}/api/alerting/alerts",
                headers=self.headers, timeout=5, verify=False
            )
            r.raise_for_status()
            alerts = [a for a in r.json() if a.get("state") == "alerting"]
            if not alerts:
                return "No firing alerts."
            lines = [f"  🔴 {a.get('name', '?')} [{a.get('state')}] — {a.get('message', '')}" for a in alerts[:10]]
            return "\n".join(lines)
        except Exception as e:
            print(f"GrafanaAPI get_firing_alerts failed: {e}")
            return None

    @classmethod
    def detect(cls, mcp_url: str = None) -> 'GrafanaMCPClient | None':
        """Detekuje Grafanu a vrátí instanci pokud je dostupná."""
        grafana_url = os.environ.get("GRAFANA_URL", "http://grafana.monitoring.svc.cluster.local:80")
        token = os.environ.get("GRAFANA_SERVICE_ACCOUNT_TOKEN", "")
        if not token:
            return None
        instance = cls(grafana_url, token)
        if instance.is_available():
            return instance
        return None


class LokiClient:
    """Jednoduchý klient pro Loki Log Query API."""

    def __init__(self, loki_url: str, verify_ssl=True, headers=None):
        self.url = loki_url.rstrip('/')
        self.verify = verify_ssl
        self.headers = headers or {}

    @classmethod
    def detect(cls, verify_ssl=True):
        """Pokusí se auto-detekovat Loki ze známých service URLs v clusteru.
        Preferuje centrální Loki (více clusterů), pak lokální.
        """
        # Centrální Loki má cluster label → preferován
        central_candidates = [
            'http://loki-central-gateway.logging-central.svc.cluster.local:80',
        ]
        local_candidates = [
            'http://eudrpkbe0001-loki.monitoring-system.svc.cluster.local:3100',
            'http://loki.monitoring.svc.cluster.local:3100',
            'http://loki-gateway.monitoring.svc.cluster.local:80',
        ]
        if _requests is None:
            return None
        for url in central_candidates + local_candidates:
            try:
                r = _requests.get(f'{url}/loki/api/v1/labels', timeout=3, verify=verify_ssl)
                if r.status_code == 200:
                    labels = r.json().get('data', [])
                    instance = cls(url, verify_ssl)
                    # Zjisti jestli Loki používá cluster label (multi-cluster)
                    instance.has_cluster_label = 'cluster' in labels
                    return instance
            except Exception:
                continue
        return None

    def query_range(self, logql: str, start_ns: int = None, end_ns: int = None,
                    limit: int = 200) -> list:
        """Spustí LogQL range query a vrátí list řetězců."""
        if _requests is None:
            return []
        now = int(time.time() * 1e9)
        params = {
            'query': logql,
            'start': str(start_ns or (now - 3600 * int(1e9))),
            'end': str(end_ns or now),
            'limit': str(limit),
            'direction': 'backward',
        }
        try:
            r = _requests.get(f'{self.url}/loki/api/v1/query_range',
                              params=params, headers=self.headers, timeout=15, verify=self.verify)
            r.raise_for_status()
            results = r.json().get('data', {}).get('result', [])
            lines = []
            for stream in results:
                for ts, msg in stream.get('values', []):
                    lines.append(msg)
            return list(reversed(lines))
        except Exception as e:
            return [f'[Loki error] {e}']

    def get_pod_logs(self, namespace: str, pod: str, container: str = None,
                     tail_lines: int = 200, hours: int = 1, cluster: str = None) -> list:
        """Dotaz na logy konkrétního podu z Loki."""
        parts = []
        if cluster and getattr(self, 'has_cluster_label', False):
            parts.append(f'cluster=~"{cluster}"')
        parts.append(f'namespace=~"{namespace}"')
        parts.append(f'pod=~"{pod}"')
        if container:
            parts.append(f'container=~"{container}"')
        sel = '{' + ','.join(parts) + '}'
        now = int(time.time() * 1e9)
        start = now - hours * 3600 * int(1e9)
        return self.query_range(sel, start_ns=start, limit=tail_lines)

    def get_labels(self) -> list:
        """Vrátí list dostupných labelů v Loki."""
        if _requests is None:
            return []
        try:
            r = _requests.get(f'{self.url}/loki/api/v1/labels', headers=self.headers, timeout=5, verify=self.verify)
            r.raise_for_status()
            return r.json().get('data', [])
        except Exception as e:
            return [f'[error] {e}']

    def get_label_values(self, label: str, match: str = None, cluster: str = None) -> list:
        """Vrátí hodnoty konkrétního labelu."""
        if _requests is None:
            return []
        try:
            params = {}
            if match:
                params['match[]'] = match
            elif cluster and getattr(self, 'has_cluster_label', False):
                params['match[]'] = f'{{cluster=~"{cluster}"}}'
            r = _requests.get(f'{self.url}/loki/api/v1/label/{label}/values',
                              params=params, headers=self.headers, timeout=5, verify=self.verify)
            r.raise_for_status()
            return r.json().get('data', [])
        except Exception as e:
            return [f'[error] {e}']

    def is_available(self) -> bool:
        if _requests is None:
            return False
        try:
            r = _requests.get(f'{self.url}/loki/api/v1/labels', headers=self.headers, timeout=3, verify=self.verify)
            return r.status_code == 200
        except Exception:
            return False

class K8sAnalyzer:
    def __init__(self, kubeconfig_file=None):
        self.kubeconfig_file = kubeconfig_file
        self.v1 = None
        self.v1_core = None
        self._load_config()

    def _load_config(self):
        """Load Kubernetes configuration from uploaded file or default"""
        try:
            if self.kubeconfig_file:
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                    content = self.kubeconfig_file.getvalue().decode('utf-8')
                    f.write(content)
                    temp_path = f.name

                config.load_kube_config(temp_path)
                os.unlink(temp_path)  # Clean up temp file
            else:
                config.load_kube_config()

            self.v1 = client.CoreV1Api()
            self.v1_apps = client.AppsV1Api()
            self.v1_batch = client.BatchV1Api()

        except Exception as e:
            raise Exception(f"Failed to load Kubernetes config: {str(e)}")

    @classmethod
    def from_rancher(cls, rancher_url: str, cluster_id: str, access_key: str, secret_key: str, verify_ssl=True, bearer_token: str = None):
        """
        Vytvoří K8sAnalyzer s přímým připojením přes Rancher proxy.

        Nastaví credentials přímo v kubernetes Configuration bez kubeconfig souboru.
        Podporuje dva způsoby auth:
          - bearer_token: Authorization: Bearer <token>  (z username/password login)
          - access_key + secret_key: Authorization: Bearer <key>:<secret>  (API key)
        Rancher proxy /k8s/clusters/<id> akceptuje oba formáty.

        Args:
            rancher_url: URL Rancher serveru
            cluster_id: ID clusteru v Rancher (např. "c-xxxxx")
            access_key: Rancher API access key (prázdný při bearer_token auth)
            secret_key: Rancher API secret key (prázdný při bearer_token auth)
            verify_ssl: False = skip SSL; True = system CA; str = cesta k CA certifikátu
            bearer_token: Bearer token z username/password login (priorita před access_key:secret_key)
        """
        instance = cls.__new__(cls)
        instance.kubeconfig_file = None
        instance.v1 = None
        instance.v1_apps = None
        instance.v1_batch = None

        try:
            configuration = client.Configuration()
            configuration.host = f"{rancher_url.rstrip('/')}/k8s/clusters/{cluster_id}"

            # SSL konfigurace
            if verify_ssl is False:
                configuration.verify_ssl = False
            elif isinstance(verify_ssl, str) and os.path.exists(verify_ssl):
                configuration.ssl_ca_cert = verify_ssl
                configuration.verify_ssl = True
            else:
                configuration.verify_ssl = True

            # Explicitní ApiClient – izolovaný od globálního stavu, každý cluster má svůj
            api_client = client.ApiClient(configuration)

            # DŮLEŽITÉ: api_key mechanismus v novém kubernetes Python klientu
            # NEPŘIDÁVÁ Authorization header automaticky.
            # Musíme ho nastavit přímo přes default_headers na ApiClient instanci.
            if bearer_token:
                # Username/password login → Bearer token z Rancher session
                # DŮLEŽITÉ: lowercase 'authorization' — ws_client.create_websocket hledá přesně
                # tento klíč (case-sensitive) pro WebSocket handshake přes Rancher proxy
                api_client.default_headers['authorization'] = f'Bearer {bearer_token}'
            else:
                # API key → Bearer access_key:secret_key
                api_client.default_headers['authorization'] = f'Bearer {access_key}:{secret_key}'

            instance.v1 = client.CoreV1Api(api_client)
            instance.v1_apps = client.AppsV1Api(api_client)
            instance.v1_batch = client.BatchV1Api(api_client)

        except Exception as e:
            raise Exception(f"Failed to initialize Rancher K8s client: {str(e)}")

        return instance

    def get_nodes(self):
        """Get all nodes in the cluster"""
        try:
            if not self.v1:
                return []
            return self.v1.list_node().items
        except Exception as e:
            print(f"Error getting nodes: {e}")
            return []

    def get_pods(self, namespace=None):
        """Get all pods, optionally filtered by namespace"""
        try:
            if not self.v1:
                return []
            if namespace:
                return self.v1.list_namespaced_pod(namespace).items
            else:
                return self.v1.list_pod_for_all_namespaces().items
        except Exception as e:
            print(f"Error getting pods: {e}")
            return []

    def get_namespaces(self):
        """Get all namespaces"""
        try:
            if not self.v1:
                return []
            return self.v1.list_namespace().items
        except Exception as e:
            print(f"Error getting namespaces: {e}")
            return []

    def test_connection(self):
        """Test connection to the cluster"""
        try:
            if not self.v1:
                return False, "Kubernetes client not initialized"
            # Use list_namespace as a reliable connectivity test
            self.v1.list_namespace(limit=1)
            return True, "Connection successful"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def get_services(self, namespace=None):
        """Get all services"""
        try:
            if namespace:
                return self.v1.list_namespaced_service(namespace).items
            else:
                return self.v1.list_service_for_all_namespaces().items
        except ApiException as e:
            print(f"Error getting services: {e}")
            return []

    def get_deployments(self, namespace=None):
        """Get all deployments"""
        try:
            if namespace:
                return self.v1_apps.list_namespaced_deployment(namespace).items
            else:
                return self.v1_apps.list_deployment_for_all_namespaces().items
        except ApiException as e:
            print(f"Error getting deployments: {e}")
            return []

    def get_events(self, namespace=None):
        """Get recent events"""
        try:
            if namespace:
                return self.v1.list_namespaced_event(namespace).items
            else:
                return self.v1.list_event_for_all_namespaces().items
        except ApiException as e:
            print(f"Error getting events: {e}")
            return []

    def get_pods_in_namespace(self, namespace: str):
        """Get pods in a specific namespace"""
        try:
            if not self.v1:
                return []
            return self.v1.list_namespaced_pod(namespace).items
        except Exception as e:
            print(f"Error getting pods in {namespace}: {e}")
            return []

    def get_pod_containers(self, pod_name: str, namespace: str) -> list:
        """Get container names for a pod"""
        try:
            pod = self.v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            return [c.name for c in (pod.spec.containers or [])]
        except Exception:
            return []

    def get_loki_client(self, verify_ssl=True):
        """Vrátí LokiClient — preferuje Grafana datasource proxy, jinak přímý Loki."""
        # Zkus nejdříve Grafana MCP (datasource proxy — nevyžaduje přímý přístup na Loki)
        grafana = GrafanaMCPClient.detect()
        if grafana:
            loki = grafana.create_loki_client()
            if loki:
                return loki
        # Fallback: přímé připojení na Loki
        return LokiClient.detect(verify_ssl=verify_ssl)

    def get_pod_logs(self, pod_name, namespace, container=None, tail_lines=100):
        """Get logs from a specific pod via Kubernetes API"""
        try:
            logs = self.v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container,
                tail_lines=tail_lines
            )
            return logs
        except ApiException as e:
            return f"Error getting logs: {e}"

    def get_cluster_summary(self):
        """Get basic cluster summary for AI analysis"""
        nodes = self.get_nodes()
        pods = self.get_pods()
        namespaces = self.get_namespaces()

        problematic_pods = [
            pod for pod in pods
            if pod.status.phase in ['Pending', 'Failed', 'CrashLoopBackOff']
        ]

        return {
            'nodes': len(nodes),
            'pods': len(pods),
            'namespaces': len(namespaces),
            'problematic_pods': len(problematic_pods),
            'node_status': [node.status.conditions[-1].type for node in nodes if node.status.conditions],
            'pod_status_distribution': {
                status: len([p for p in pods if p.status.phase == status])
                for status in set(p.status.phase for p in pods)
            }
        }

    def analyze_pod_health(self, pod):
        """Analyze individual pod health"""
        analysis = {
            'name': pod.metadata.name,
            'namespace': pod.metadata.namespace,
            'status': pod.status.phase,
            'issues': []
        }

        # Check for restarts
        if pod.status.container_statuses:
            for container in pod.status.container_statuses:
                if container.restart_count > 0:
                    analysis['issues'].append(f"Container {container.name} restarted {container.restart_count} times")

        # Check status
        if pod.status.phase == 'Pending':
            analysis['issues'].append("Pod is in Pending state")
        elif pod.status.phase == 'Failed':
            analysis['issues'].append("Pod has Failed")
        elif pod.status.phase == 'CrashLoopBackOff':
            analysis['issues'].append("Pod is in CrashLoopBackOff")

        return analysis

    def get_recent_events(self, hours=1):
        """Get events from the last N hours"""
        import datetime
        now = datetime.datetime.utcnow()
        cutoff = now - datetime.timedelta(hours=hours)

        events = self.get_events()
        recent_events = []

        for event in events:
            if event.last_timestamp:
                event_time = event.last_timestamp.replace(tzinfo=None)
                if event_time > cutoff:
                    recent_events.append({
                        'time': event.last_timestamp,
                        'type': event.type,
                        'reason': event.reason,
                        'message': event.message,
                        'source': event.source.component if event.source else 'Unknown',
                        'namespace': event.metadata.namespace,
                        'object': f"{event.involved_object.kind}/{event.involved_object.name}"
                    })

        return sorted(recent_events, key=lambda x: x['time'], reverse=True)

    def get_egress_gateway_policies(self, namespace: str = None) -> list:
        """List CiliumEgressGatewayPolicy CRDs. Optionally filter by namespace selector."""
        try:
            custom_api = client.CustomObjectsApi(self.v1.api_client)
            resp = custom_api.list_cluster_custom_object(
                group="cilium.io",
                version="v2",
                plural="ciliumegressgatewaypolicies",
            )
            policies = resp.get("items", [])
            if namespace is None:
                return policies
            # Filter: keep policies whose selectors mention the namespace (or have no NS restriction)
            matching = []
            for p in policies:
                spec = p.get("spec", {})
                selectors = spec.get("selectors", [])
                for sel in selectors:
                    ns_sel = sel.get("namespaceSelector", {})
                    ns_labels = ns_sel.get("matchLabels", {})
                    ns_expr = ns_sel.get("matchExpressions", [])
                    # No namespaceSelector → applies to all namespaces
                    if not ns_labels and not ns_expr:
                        matching.append(p)
                        break
                    # Explicit kubernetes.io/metadata.name match
                    if ns_labels.get("kubernetes.io/metadata.name") == namespace:
                        matching.append(p)
                        break
                    # matchExpressions with In operator
                    for expr in ns_expr:
                        if (expr.get("key") == "kubernetes.io/metadata.name"
                                and expr.get("operator") == "In"
                                and namespace in expr.get("values", [])):
                            matching.append(p)
                            break
                    else:
                        continue
                    break
            return matching
        except ApiException as e:
            if e.status == 404:
                return []  # CRD not installed
            raise
        except Exception as e:
            print(f"Error getting CiliumEgressGatewayPolicies: {e}")
            return []

    def get_pod_ips_in_namespace(self, namespace: str) -> list:
        """Return list of dicts {name, ip, phase, node} for pods in namespace."""
        pods = self.get_pods_in_namespace(namespace)
        result = []
        for pod in pods:
            result.append({
                "name": pod.metadata.name,
                "ip": pod.status.pod_ip or "",
                "phase": pod.status.phase or "Unknown",
                "node": pod.spec.node_name or "",
            })
        return result

    def exec_in_pod(self, pod_name: str, namespace: str, command: list, timeout: int = 12) -> str:
        """Exec a command in a running pod and return combined stdout+stderr."""
        try:
            from kubernetes.stream import stream as k8s_stream
            resp = k8s_stream(
                self.v1.connect_get_namespaced_pod_exec,
                pod_name,
                namespace,
                command=command,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False,
                _preload_content=False,
                _request_timeout=timeout,
            )
            resp.run_forever(timeout=timeout)
            stdout = resp.read_stdout() or ""
            stderr = resp.read_stderr() or ""
            return (stdout + stderr).strip() or ""
        except Exception as e:
            return f"[exec error] {e}"

    def get_snat_ip(self, pod_ip: str, dest_ip: str, dest_port: str, node_name: str = "", expected_vip: str = "") -> tuple:
        """
        Ověří skutečnou odchozí (SNAT) IP pomocí CiliumEgressGatewayPolicy.
        Strategie: hledá v egress listu záznam kde Egress IP == expected_vip
        a Gateway IP je validní IP → policy je aktivní v BPF.
        Pokud expected_vip není zadán, hledá jakýkoliv aktivní záznam pro 0.0.0.0/0.
        Vrátí (snat_ip, debug_str).
        """
        import ipaddress
        debug_lines = []
        try:
            # Egress list s vyplněnými Egress IP je POUZE na gateway nodu!
            # Na ostatních nodech je Egress IP = 0.0.0.0 → musíme číst z gateway nodu.
            # Gateway node má label: cilium.io/egress-gateway-node=true
            gw_nodes = self.v1.list_node(
                label_selector="cilium.io/egress-gateway-node=true"
            )
            if gw_nodes.items:
                gw_node_name = gw_nodes.items[0].metadata.name
                debug_lines.append(f"Gateway node: {gw_node_name}")
                pods = self.v1.list_namespaced_pod(
                    namespace="kube-system",
                    label_selector="k8s-app=cilium",
                    field_selector=f"spec.nodeName={gw_node_name}",
                )
            else:
                debug_lines.append("Gateway node nenalezen — zkouším libovolný cilium pod")
                pods = self.v1.list_namespaced_pod(
                    namespace="kube-system",
                    label_selector="k8s-app=cilium",
                )

            if not pods.items:
                debug_lines.append("ERROR: žádný cilium pod nenalezen")
                return "", "\n".join(debug_lines)

            cilium_pod = pods.items[0].metadata.name
            debug_lines.append(f"Cilium pod: {cilium_pod}")

            # cilium bpf egress list — hledej záznam kde Egress IP == expected_vip
            # Formát: Source IP  Destination CIDR  Egress IP  Gateway IP
            egress_output = self.exec_in_pod(
                pod_name=cilium_pod,
                namespace="kube-system",
                command=["cilium", "bpf", "egress", "list"],
                timeout=15,
            )
            debug_lines.append(f"egress list ({len(egress_output)} chars)")

            for line in egress_output.splitlines():
                parts = line.split()
                if len(parts) < 4 or parts[0] == "Source":
                    continue
                egress_ip_candidate = parts[2]
                gateway_val = " ".join(parts[3:])
                dest_cidr_str = parts[1]
                # Přeskoč Excluded CIDR záznamy
                if "Excluded" in gateway_val:
                    continue
                # Gateway musí být validní IP
                try:
                    ipaddress.ip_address(gateway_val.split()[0])
                except ValueError:
                    continue
                # Pokud máme expected_vip, hledej přesnou shodu
                if expected_vip:
                    if egress_ip_candidate == expected_vip:
                        debug_lines.append(f"✅ Policy aktivní v BPF: {line.strip()}")
                        return egress_ip_candidate, "\n".join(debug_lines)
                else:
                    # Bez expected_vip — hledej 0.0.0.0/0 záznam
                    if dest_cidr_str == "0.0.0.0/0":
                        debug_lines.append(f"Nalezen 0.0.0.0/0 záznam: {line.strip()}")
                        return egress_ip_candidate, "\n".join(debug_lines)

            if expected_vip:
                debug_lines.append(f"⚠️ VIP {expected_vip} nenalezena v egress listu — policy možná není aktivní")
            else:
                debug_lines.append("Žádný aktivní egress záznam nenalezen")

        except Exception as e:
            debug_lines.append(f"EXCEPTION: {e}")
        return "", "\n".join(debug_lines)

    def run_pod_command(self, namespace: str, command: str, timeout: int = 40) -> tuple:
        """
        Spustí příkaz v dočasném busybox podu v daném namespace.
        Pod se automaticky smaže po dokončení. Vrátí výstup (logy).
        Vhodné jako náhrada za exec do multi-container podů.
        """
        import time
        import uuid

        pod_name = f"nettest-{uuid.uuid4().hex[:8]}"
        pod_manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": pod_name, "namespace": namespace,
                         "labels": {"app": "k8s-ai-nettest"}},
            "spec": {
                "restartPolicy": "Never",
                "containers": [{
                    "name": "nettest",
                    "image": "busybox:1.36",
                    "command": ["sh", "-c", command],
                    "resources": {
                        "requests": {"cpu": "10m", "memory": "16Mi"},
                        "limits":   {"cpu": "50m", "memory": "32Mi"},
                    },
                }],
                "tolerations": [{"operator": "Exists"}],
            },
        }

        try:
            self.v1.create_namespaced_pod(namespace=namespace, body=pod_manifest)
        except Exception as e:
            return f"[pod create error] {e}", "", ""

        pod_ip = ""
        node_name = ""
        try:
            deadline = time.time() + timeout
            phase = "Pending"
            # Fáze 1: čekej na Running → přečti pod IP (Cilium má pod v BPF mapě)
            while time.time() < deadline:
                pod = self.v1.read_namespaced_pod(name=pod_name, namespace=namespace)
                phase = pod.status.phase or "Pending"
                if phase == "Running":
                    pod_ip = (pod.status.pod_ip or "").strip()
                    node_name = pod.spec.node_name or ""
                    break
                if phase in ("Succeeded", "Failed"):
                    # Pod doběhl příliš rychle — IP možná v status
                    pod_ip = (pod.status.pod_ip or "").strip()
                    node_name = pod.spec.node_name or ""
                    break
                time.sleep(0.5)

            # Fáze 2: čekej na Succeeded/Failed
            while time.time() < deadline and phase not in ("Succeeded", "Failed"):
                pod = self.v1.read_namespaced_pod(name=pod_name, namespace=namespace)
                phase = pod.status.phase or phase
                time.sleep(1)

            if phase not in ("Succeeded", "Failed"):
                return f"[timeout] Pod neskončil do {timeout}s (phase={phase})", node_name, pod_ip

            logs = self.v1.read_namespaced_pod_log(name=pod_name, namespace=namespace,
                                                    container="nettest") or ""
            return logs.strip(), node_name, pod_ip
        except Exception as e:
            return f"[pod run error] {e}", node_name, pod_ip
        finally:
            try:
                self.v1.delete_namespaced_pod(name=pod_name, namespace=namespace,
                                              body=client.V1DeleteOptions(grace_period_seconds=0))
            except Exception:
                pass