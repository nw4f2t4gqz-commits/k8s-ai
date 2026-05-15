# AI Chat

## Overview

The **AI Chat** tab provides an interactive assistant that answers questions about your Kubernetes cluster using live data. It combines real-time cluster state from the Kubernetes API and Prometheus metrics from Grafana into a context block, then uses an Ollama-hosted LLM to generate answers.

## How It Works

```
[User question]
      │
      ▼
[Context Block] ─── loaded ONCE per session ───> K8s API (pods, nodes, events, deployments)
      │                                           Grafana REST API (CPU, memory, alerts)
      │
      ▼
[Ollama LLM]  →  streaming response
      │
      ▼
[Answer in chat]
```

Key properties:
- Context is fetched **once** when the tab is opened or when the user clicks `🔄 Refresh cluster data`
- Context is tied to the active cluster — switching clusters auto-invalidates the cache
- LLM receives: system skill prompt + cluster context block + full chat history + new question

## Status Bar

At the top of the chat tab:

```
📊 Cluster data: 14:32:17  |  ✅ +Prometheus  |  🔄 Refresh cluster data
```

| Indicator | Meaning |
|---|---|
| `📊 Cluster data: HH:MM:SS` | Time of last context fetch |
| `✅ +Prometheus (my-cluster)` | Grafana reachable, metrics filtered for the selected cluster |
| `✅ +Prometheus` | Grafana reachable, no cluster filter (kubeconfig mode) |
| `⚠️ Grafana offline` | Grafana unreachable — only K8s data available |
| `🔄 Refresh cluster data` | Force re-fetch context from K8s API + Grafana |

## What's in the Context

### Kubernetes API data

- Total pods, running/pending/failed/unknown counts
- Per-namespace breakdown with pod counts
- Per-node: CPU allocatable, memory allocatable, **max pod capacity**, current running pod count
- Recent warning events (last 50)
- Deployments with replica counts

### Prometheus data (via Grafana REST API)

- Cluster-wide CPU usage %
- Cluster-wide memory usage %
- Top 5 pods by CPU usage
- Top 5 pods by memory usage

## Example Questions

### Works well ✅

```
How many pods are running in the cluster?
Which namespace has the most pods?
Are there any nodes with high memory usage?
What are the top CPU-consuming pods right now?
Are there any recent warning events?
Is node <node-name> overloaded?
How much pod capacity is left on each node?
Are there any firing alerts in Grafana?
```

### Limitations ⚠️

```
Show me pod logs from namespace X       # Not supported — chat has no log access
What happened yesterday at 3pm?         # No historical data, only current state
Deploy a new version of service Y       # Chat is read-only, no write access
```

## Chat History

- Chat history is kept in `st.session_state` — it persists for the duration of the browser session
- The full history is sent with each new message (LLM sees the whole conversation)
- Click **🗑️ Clear Chat** to reset the history

## Model Selection Effect

Use the model selector in the sidebar:

| Model | Speed | Intelligence | Notes |
|---|---|---|---|
| `phi3.5:latest` (2.2GB) | Fastest | Good | Best for most questions |
| `qwen3.5:2b` (2.7GB) | Fast | Good | Adds `/no_think` prefix for efficiency |
| `qwen3:8b` (5.2GB) | Slow | Best | Higher quality, noticeably slower on CPU |

> All models run **CPU-only**. Inference speed depends on Ollama pod CPU allocation (currently 26 cores).

## Customizing the Chat Skill

The system prompt for the chat is stored in `values.yaml` under `skills.chat`.
No image rebuild is needed — only `helm upgrade`. See [skills.md](skills.md).
