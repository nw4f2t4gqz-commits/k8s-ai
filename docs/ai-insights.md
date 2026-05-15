# AI Insights

## Overview

The **AI Insights** tab provides automated, on-demand analysis of your Kubernetes cluster. Unlike the AI Chat (which is conversational), AI Insights runs a structured analysis of the current cluster state and returns a formatted report.

## Analysis Types

Select one from the dropdown before generating:

| Analysis Type | Description |
|---|---|
| **General Cluster Health** | Overview of all nodes, pods, events, deployments — with recommendations |
| **Problematic Pods** | Focuses on pods in Pending, CrashLoopBackOff, Error, OOMKilled states |
| **Resource Optimization** | Identifies over-provisioned or under-resourced deployments |
| **Security Check** | Highlights pods running as root, missing resource limits, privileged containers |

## How to Generate

1. Open the **AI Insights** tab
2. Select the cluster from the sidebar (if multiple are configured)
3. Select an **Analysis Type** from the dropdown
4. Click **🚀 Generate AI Analysis**
5. Wait for the spinner — K8s API data is fetched first, then LLM tokens stream in

## Expected Output Format

```
## Kubernetes Cluster Health Analysis

### 1. Cluster Overview
- Total nodes: 3 (all Ready)
- Total pods: 147 (Running: 142, Pending: 2, Failed: 3)
...

### 2. Identified Issues
1. Pod `myapp-7d9f8b-xxxx` in namespace `production` — CrashLoopBackOff
   - Last exit code: 1
   - Recommended action: kubectl logs myapp-7d9f8b-xxxx -n production
...

### 3. Recommendations
...
```

Output is streamed token-by-token — the report appears progressively as the model generates it.

## Technical Details

### Data flow

```
[Generate AI Analysis clicked]
         │
         ▼
  K8s API query  ──────────────────────────────────────────────────┐
  (nodes, pods, events, deployments, namespaces)                   │
         │                                                          │
         ▼                                                          ▼
  [Cluster data assembled] ─────────────────> Ollama streaming API
  + Analysis type as task                          │
  + AI_SKILL_INSIGHTS system prompt                │
                                                   ▼
                                         [Report streamed to UI]
```

### `/no_think` prefix

For Qwen3-family models, the app prepends `/no_think` to the analysis request. This disables the model's chain-of-thought reasoning phase and produces output faster without the `<think>...</think>` block. For other models (phi3.5) this prefix has no effect.

### Temperature

Inference is run with `temperature=0.1` — low temperature for deterministic, factual output. This is appropriate for cluster analysis where hallucination should be minimized.

## Customizing the Insights Skill

The system prompt for AI Insights is stored in `values.yaml` under `skills.insights`.
No image rebuild is needed — only `helm upgrade`. See [skills.md](skills.md).

## Limitations

- Analysis is based on **current cluster state** only (no historical data)
- Grafana metrics are NOT included in Insights context (only K8s API data)
- Very large clusters with many namespaces may hit LLM context limits
- Output quality depends on selected model — use `qwen3:8b` for most thorough analysis

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Output in wrong language | Bad system prompt | Edit `skills.insights` in `values.yaml`, `helm upgrade` |
| `<think>` block in output | Model is Qwen3 but `/no_think` not triggering | Check model name detection in `app.py` |
| Blank/empty output | Ollama unreachable | Check `kubectl get pods -n ai-local` |
| Report stops mid-sentence | Context too large | Reduce the number of analyzed namespaces or switch to `qwen3:8b` |
