# Deployment Guide

## Prerequisites

- Kubernetes 1.24+
- Helm 3.10+
- Docker with access to your image registry
- `kubectl` with cluster-admin access
- Grafana running in `monitoring` namespace with a Service Account token

## Quick Deploy

```bash
# Build and push image
docker build -t <registry>/<image>:<tag> .
docker push <registry>/<image>:<tag>

# Deploy via Helm
helm upgrade --install ai-local ./helm \
  --namespace ai-local --create-namespace \
  -f helm/values.yaml \
  -f helm/values-<cluster>.yaml
```

Or use the helper script:

```bash
./scripts/build-deploy.sh <tag>
```

## Helm Values Reference

### webui

```yaml
webui:
  enabled: true
  replicaCount: 1
  image:
    repository: <registry>/<image>
    tag: <tag>
    pullPolicy: Always
  ingress:
    enabled: true
    className: traefik
    hosts:
      - host: ai.apps.<cluster>.example.com
  env:
    - name: RANCHER_GATEWAYS
      value: "https://rancher.apps.<cluster>.example.com"
```

### skills — AI system prompts

```yaml
skills:
  insights: |
    You are an expert Kubernetes L2/L3 support engineer...
    # Full text in values.yaml — edit without rebuilding image
  chat: |
    You are an expert Kubernetes L2/L3 support engineer assistant...
```

Changes to `skills` take effect with `helm upgrade` only (no docker build needed).
See [skills.md](skills.md) for details.

### grafanaMCP — Grafana integration

```yaml
grafanaMCP:
  enabled: true
  grafanaUrl: "http://grafana.monitoring.svc.cluster.local:80"
  serviceAccountToken: "glsa_..."  # Editor role required
```

### ollama

```yaml
ollama:
  enabled: true
  model: "phi3.5"
  persistentVolume:
    enabled: true
    size: 30Gi
    storageClass: "ontap-nas"
  resources:
    requests:
      cpu: "4"
      memory: "8Gi"
    limits:
      cpu: "26"
      memory: "16Gi"
  nodeSelector:
    kubernetes.io/hostname: <node-hostname>
```

> **Note:** Ollama runs CPU-only. Pin it to a node with sufficient CPU cores via `nodeSelector`. Do not change `nodeSelector` without verifying the target node has sufficient CPU.

## Grafana Service Account Setup

1. Open Grafana → Administration → Service Accounts
2. Create a new service account with **Editor** role
3. Generate a token → copy to `grafanaMCP.serviceAccountToken` in `values.yaml`

Minimum required permissions (fine-grained):
```
datasources:read
datasources:query
alert.rules:read
annotations:read
dashboards:read
```

## Upgrade Procedure

```bash
# 1. If code changed — build new image
docker build -t <registry>/<image>:<new-tag> .
docker push <registry>/<image>:<new-tag>

# 2. Deploy
helm upgrade ai-local ./helm \
  --namespace ai-local \
  -f helm/values.yaml \
  -f helm/values-<cluster>.yaml
```

## Verify Deployment

```bash
# Check pods — webui should show 2/2 (webui + mcp-grafana)
kubectl get pods -n ai-local

# Check webui logs
kubectl logs -n ai-local -l app.kubernetes.io/name=webui -c webui --tail=50

# Check mcp-grafana sidecar
kubectl logs -n ai-local -l app.kubernetes.io/name=webui -c mcp-grafana --tail=20

# Check active skills (env vars)
kubectl exec -n ai-local deploy/ai-local-ai-webui -- env | grep AI_SKILL
```

## Image Tagging Convention

Format: `v<YYYY-MM-DD>-<seq>`

Examples:
- `v2026-03-17-17` — 17th image on March 17, 2026
- Increment `<seq>` for each build in a day

## Namespace and RBAC

The webui ServiceAccount needs `get/list/watch` on:
- `pods`, `nodes`, `namespaces`, `events`, `deployments`, `services`

This is automatically created by the Helm chart (`templates/webui/webui-rbac.yaml`).
