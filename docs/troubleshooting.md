# Troubleshooting

## AI Chat

### AI answers in wrong language or produces garbage

**Cause:** The `AI_SKILL_CHAT` system prompt is missing or has wrong language instruction.

**Fix:**
```bash
# Check current skill content
kubectl exec -n ai-local deploy/ai-local-ai-webui -- env | grep AI_SKILL_CHAT

# Edit skills.chat in values.yaml, ensure language is specified, then upgrade
helm upgrade ai-local /tmp/k8s-ai-helm --namespace ai-local -f values.yaml \
  --set webui.image.tag=$(kubectl get deploy -n ai-local ai-local-ai-webui \
    -o jsonpath='{.spec.template.spec.containers[0].image}' | cut -d: -f2)

kubectl rollout restart deployment -n ai-local ai-local-ai-webui
```

---

### Chat shows old data / wrong pod counts

**Cause:** Context was loaded earlier and cached in `session_state`.

**Fix:** Click **🔄 Refresh cluster data** in the chat tab header.
If the issue persists after refresh, the K8s API may be returning stale data. Check:
```bash
kubectl get pods --all-namespaces | wc -l
```

---

### Chat gives "I don't know" for live metrics

**Cause:** Grafana integration is offline — Prometheus metrics not included in context.

**Indicator:** Status bar shows `⚠️ Grafana MCP offline` instead of `✅ +Prometheus`.

**Fix:** See [grafana-integration.md — Troubleshooting](grafana-integration.md#troubleshooting).

---

## AI Insights

### `<think>...</think>` block appears in output

**Cause:** A Qwen3-family model is selected but the `/no_think` prefix is not being applied.

**Check in `app.py`:**
```python
# Should appear before the prompt construction:
if "qwen3" in model_name.lower():
    prompt = "/no_think\n" + prompt
```

If this code is missing, add it or use a different model.

---

### AI Insights output is empty or stream stops immediately

**Cause:** Ollama pod is not running or restarting.

**Check:**
```bash
kubectl get pods -n ai-local
kubectl logs -n ai-local -l app=ollama --tail=50
```

If Ollama is OOMKilled:
```bash
# Increase memory in values.yaml
ollama:
  resources:
    limits:
      memory: "20Gi"
```

---

### AI Insights analysis is truncated mid-sentence

**Cause:** Context too large for the model's context window.

**Options:**
1. Switch to `qwen3:8b` (handles longer contexts better)
2. Reduce the scope in `app.py` — limit events to last 20 instead of 50
3. Filter to specific namespaces before analysis

---

## Grafana

### `⚠️ Grafana MCP offline` in chat

See [grafana-integration.md — Troubleshooting](grafana-integration.md#troubleshooting).

---

### PromQL queries return empty results

**Cause:** Prometheus datasource UID changed, or node_exporter labels differ.

**Debug:**
```bash
# Get datasource list
kubectl exec -n ai-local deploy/ai-local-ai-webui -- \
  curl -s -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" \
  $GRAFANA_URL/api/datasources | python3 -m json.tool | grep -E '"uid|"type'

# Test a query manually
kubectl exec -n ai-local deploy/ai-local-ai-webui -- \
  curl -s -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" \
  "$GRAFANA_URL/api/datasources/proxy/uid/<uid>/api/v1/query?query=up" | python3 -m json.tool
```

---

## Pod / Deployment

### Pod shows `0/2` (not ready)

**Cause:** One of the two containers is not starting. Check which container is failing:

```bash
kubectl describe pod -n ai-local -l app.kubernetes.io/name=webui
```

If `mcp-grafana` container is failing, disable it:
```yaml
# values.yaml
grafanaMCP:
  enabled: false
```

```bash
helm upgrade ai-local /tmp/k8s-ai-helm --namespace ai-local -f values.yaml ...
```

---

### `ImagePullBackOff`

**Cause:** Registry is unreachable or image tag does not exist.

**Check:**
```bash
kubectl describe pod -n ai-local <pod-name> | grep -A5 Events

# Verify the image exists in registry
docker manifest inspect <registry>/<image>:<tag>
```

---

### Webui is running but 503 in browser

**Cause:** Ingress → Service → Pod connectivity issue.

**Debug:**
```bash
# Check service endpoints
kubectl get endpoints -n ai-local

# Check ingress
kubectl describe ingress -n ai-local

# Test from inside cluster
kubectl run curl-test --image=curlimages/curl -it --rm -- \
  curl -s http://ai-local-ai-webui.ai-local.svc.cluster.local:8501
```

---

## Ollama / Models

### Inference is very slow

Ollama runs CPU-only. Performance depends on allocated CPU cores.

**Check current allocation:**
```bash
kubectl get deploy -n ai-local -l app=ollama -o jsonpath='{.items[0].spec.template.spec.containers[0].resources}'
```

**Tune in `values.yaml`:**
```yaml
ollama:
  resources:
    requests:
      cpu: "8"
    limits:
      cpu: "26"
```

> Ollama runs CPU-only. Setting CPU limit above the node's physical core count may cause throttling.

---

## Egress / Network Test

### Skutečná odchozí IP se nepodaří zjistit (debug: "0.0.0.0")

**Příčina:** `cilium bpf egress list` obsahuje vyplněnou Egress IP **pouze na gateway nodu**. Na ostatních nodech je Egress IP = `0.0.0.0`.

**Ověření — zjisti gateway node:**
```bash
kubectl get nodes -l cilium.io/egress-gateway-node=true \
  --kubeconfig /path/to/kubeconfig
```

**Ověření — přečti egress list přímo z gateway nodu:**
```bash
GW_NODE=$(kubectl get nodes -l cilium.io/egress-gateway-node=true \
  --kubeconfig /path/to/kubeconfig \
  -o jsonpath='{.items[0].metadata.name}')

GW_CILIUM=$(kubectl get pod -n kube-system \
  --kubeconfig /path/to/kubeconfig \
  -l k8s-app=cilium --field-selector spec.nodeName=$GW_NODE \
  -o jsonpath='{.items[0].metadata.name}')

kubectl exec -n kube-system $GW_CILIUM \
  --kubeconfig /path/to/kubeconfig \
  -- cilium bpf egress list
```

**Očekávaný výstup** (gateway node):
```
Source IP     Destination CIDR   Egress IP       Gateway IP
10.0.0.10     10.0.0.0/16        192.168.1.100   Excluded CIDR
10.0.0.10     0.0.0.0/0          192.168.1.100   192.168.1.1
```

---

### Debug ukazuje "VIP nenalezena v egress listu"

**Příčina:** `get_snat_ip()` nečte ze správného podu, nebo policy není aktivní v BPF.

**Ověření policy:**
```bash
kubectl get ciliumegressgatewaypolicies \
  --kubeconfig /path/to/kubeconfig -o yaml | \
  grep -E "egressIP|namespaceSelector"
```

Ujisti se, že `spec.egressGateway.egressIP` odpovídá IP ve sloupci Egress IP v egress listu.

---

### K8sGPT objekt nenasazen po `helm install`

**Příčina:** Helm 3 neinstaluje CRDs ze subchartů automaticky.

**Fix — nainstaluj CRDs ručně:**
```bash
kubectl apply -f ./helm/crds/k8sgpt-crds.yaml \
  --kubeconfig /path/to/kubeconfig

helm upgrade ai-local ./helm \
  --namespace ai-local \
  --kubeconfig /path/to/kubeconfig \
  -f helm/values.yaml \
  -f helm/values-<cluster>.yaml
```

---

### k8sgpt-operator crashloop — "failed to wait for mutation caches to sync"

**Příčina:** `mutations.core.k8sgpt.ai` CRD chybí v clusteru.

**Fix:**
```bash
helm show crds ./helm/charts/k8sgpt-operator-*.tgz | \
  kubectl apply -f - --kubeconfig /path/to/kubeconfig
```

---

### Model not loading / `model not found`

```bash
# List available models
kubectl exec -n ai-local -l app=ollama -- ollama list

# Pull a model manually (persisted to PVC)
kubectl exec -n ai-local -l app=ollama -- ollama pull phi3.5
```

---

## Logs Tab

### No logs appearing

**Cause:** Loki is not configured or unreachable.

**Check:**
```bash
# Loki URL is read from env var LOKI_URL
kubectl exec -n ai-local deploy/ai-local-ai-webui -- env | grep LOKI
```

**Values.yaml:**
```yaml
webui:
  env:
    - name: LOKI_URL
      value: "http://loki.monitoring.svc.cluster.local:3100"
```

---

## General

### How to get all webui logs since last restart

```bash
kubectl logs -n ai-local -l app.kubernetes.io/name=webui -c webui \
  --since-time=$(kubectl get pod -n ai-local -l app.kubernetes.io/name=webui \
    -o jsonpath='{.items[0].status.containerStatuses[0].state.running.startedAt}')
```

### How to force webui restart

```bash
kubectl rollout restart deployment -n ai-local ai-local-ai-webui
kubectl rollout status deployment -n ai-local ai-local-ai-webui
```
