# Deployment Guide

## Prerequisites

- Kubernetes 1.24+
- Helm 3.10+
- Docker with access to `central-system-repo.app.corp:10443`
- `kubectl` with cluster-admin access
- Grafana running in `monitoring` namespace with a Service Account token

## Quick Deploy

```bash
# Build and push image
cd /home/jartymyt/k8s-ai
docker build -t central-system-repo.app.corp:10443/9tech/ai/webui:v2026-05-15-17 .
docker push central-system-repo.app.corp:10443/9tech/ai/webui:v2026-05-15-17

# Deploy via Helm
KUBECONFIG=/home/jartymyt/kubeconfig/eudrpkbe0001.kubeconfig \
helm upgrade --install ai-local /home/jartymyt/k8s-ai/helm \
  --namespace ai-local --create-namespace \
  -f helm/values.yaml \
  --set webui.image.tag=v2026-05-15-17
```

Or use the helper script:

```bash
./scripts/build-deploy.sh v2026-05-15-17
```

## Helm Values Reference

### webui

```yaml
webui:
  enabled: true
  replicaCount: 1
  image:
    repository: central-system-repo.app.corp:10443/9tech/ai/webui
    tag: v2026-03-17-17
    pullPolicy: Always
  ingress:
    enabled: true
    className: traefik
    hosts:
      - host: ai.apps.eudrpkbe0001.k8s.corp
  env:
    - name: RANCHER_GATEWAYS
      value: "https://rancher.apps.eudrpkbe0001.k8s.corp"
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
    kubernetes.io/hostname: eudrpkxs1101.eudrpkbe0001.k8s.corp
```

> **Note:** Ollama runs CPU-only. It is pinned to `eudrpkxs1101` which has 24 cores available. Do not change `nodeSelector` without verifying the target node has sufficient CPU.

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
# 1. Edit values.yaml (skills, config changes)
vim /home/jartymyt/k8s-ai/values.yaml

# 2. If code changed — build new image
docker build -t central-system-repo.app.corp:10443/9tech/ai/webui:<new-tag> .
docker push central-system-repo.app.corp:10443/9tech/ai/webui:<new-tag>

# 3. Deploy
rsync -a --exclude='venv/' --exclude='__pycache__/' --exclude='.git/' --exclude='*.pyc' \
  /home/jartymyt/k8s-ai/ /tmp/k8s-ai-helm/

KUBECONFIG=/home/jartymyt/kubeconfig/eudrpkbe0001.kubeconfig \
helm upgrade ai-local /tmp/k8s-ai-helm \
  --namespace ai-local \
  -f /home/jartymyt/k8s-ai/values.yaml \
  --set webui.image.tag=<new-tag>
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
