# Grafana Integration

## Overview

The application integrates with Grafana to enrich AI Chat context with real-time Prometheus metrics. This is handled by the `GrafanaMCPClient` class in `k8s_analyzer.py`.

> **Note:** Despite the name `GrafanaMCPClient`, the integration uses the **Grafana REST API directly** (not the MCP protocol). The original MCP sidecar approach was replaced because the MCP protocol requires a stateful `initialize` handshake that could not be reliably set up in the current deployment.

## Architecture

```
webui container
     │
     │  HTTP REST calls
     ▼
Grafana (monitoring namespace)
http://grafana.monitoring.svc.cluster.local:80
     │
     │  datasource proxy
     ▼
Prometheus → metrics
     │
     │  alerting API
     ▼
Alertmanager → firing alerts
```

The `mcp-grafana` sidecar container is still deployed (see `values.yaml grafanaMCP.enabled`) but is not used for queries.

## Configuration

Set via `values.yaml` (injected as pod environment variables):

```yaml
grafanaMCP:
  enabled: true
  grafanaUrl: "http://grafana.monitoring.svc.cluster.local:80"
  serviceAccountToken: "<YOUR_GRAFANA_SERVICE_ACCOUNT_TOKEN>"
```

Environment variables in the `webui` container:

| Variable | Source | Description |
|---|---|---|
| `GRAFANA_URL` | `grafanaMCP.grafanaUrl` | Grafana base URL (in-cluster) |
| `GRAFANA_SERVICE_ACCOUNT_TOKEN` | `grafanaMCP.serviceAccountToken` | Bearer token for auth |

## Grafana REST API Endpoints Used

### Health check
```
GET /api/health
```
Used by `is_available()` to detect if Grafana is reachable before making metric queries.

### Datasource discovery
```
GET /api/datasources
```
Used to find the Prometheus datasource UID. The client looks for the first datasource with `type == "prometheus"`.

### Prometheus query
```
GET /api/datasources/proxy/uid/{uid}/api/v1/query?query={promql}
```
Used to execute PromQL queries proxied through Grafana.

**Queries executed:**
| Metric | PromQL |
|---|---|
| CPU usage % | `100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)` |
| Memory usage % | `100 * (1 - sum(node_memory_MemAvailable_bytes) / sum(node_memory_MemTotal_bytes))` |
| Top 5 pods by CPU | `topk(5, sum(rate(container_cpu_usage_seconds_total{container!=""}[5m])) by (pod, namespace))` |
| Top 5 pods by memory | `topk(5, sum(container_memory_working_set_bytes{container!=""}) by (pod, namespace))` |

### Firing alerts
```
GET /api/alerting/alerts
```
Returns currently active Grafana-managed alerts. Only `state == "alerting"` alerts are included in the context.

## Service Account Token Requirements

Minimum permissions needed:

| Scope | Permission |
|---|---|
| Datasources | `datasources:read`, `datasources:query` |
| Alerting | `alert.rules:read` |

Use Grafana **Editor** role to guarantee these permissions. Viewer may be too restrictive for datasource proxy calls.

## GrafanaMCPClient Class Reference

```python
from k8s_analyzer import GrafanaMCPClient

# Auto-detect from environment variables
client = GrafanaMCPClient.detect()

if client and client.is_available():
    uid = client.get_prometheus_datasource_uid()
    metrics = client.get_cluster_metrics_summary(uid)
    # metrics = {"cpu_usage": "34.5", "memory_usage": "61.2",
    #            "top_pods_cpu": "...", "top_pods_memory": "..."}

    alerts = client.get_firing_alerts()
    # alerts = "ALERT: HighCPU on node <node-name> ..."
```

### Methods

| Method | Returns | Description |
|---|---|---|
| `detect()` | `GrafanaMCPClient \| None` | Factory — reads env vars, returns None if not configured |
| `is_available()` | `bool` | True if Grafana `/api/health` returns 200 |
| `get_prometheus_datasource_uid()` | `str \| None` | First Prometheus datasource UID |
| `get_cluster_metrics_summary(uid)` | `dict` | CPU%, memory%, top pods |
| `get_firing_alerts()` | `str \| None` | Formatted firing alerts or None |

## Troubleshooting

### `⚠️ Grafana MCP offline` in chat status bar

1. Check Grafana is running:
   ```bash
   kubectl get pods -n monitoring -l app.kubernetes.io/name=grafana
   ```

2. Check token is valid:
   ```bash
   curl -H "Authorization: Bearer glsa_..." \
     http://grafana.monitoring.svc.cluster.local/api/health
   ```
   (Run from inside the cluster via `kubectl exec`)

3. Check webui env vars are set:
   ```bash
   kubectl exec -n ai-local deploy/ai-local-ai-webui -- env | grep GRAFANA
   ```

4. Check webui logs for errors:
   ```bash
   kubectl logs -n ai-local -l app.kubernetes.io/name=webui -c webui --tail=100 | grep -i grafana
   ```

### Token expired

Generate a new token in Grafana UI → Administration → Service Accounts → add token.
Update `values.yaml` and run `helm upgrade`. No image rebuild needed.
