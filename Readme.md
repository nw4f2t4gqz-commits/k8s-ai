# K8s AI Analyzer

AI-powered Kubernetes analysis platform deployed via Helm. Provides a web UI for cluster health monitoring, AI-driven analysis, and interactive chat — all powered by local LLMs (Ollama) running fully in-cluster.

## Quick Start

```bash
# Build and deploy
./scripts/build-deploy.sh <tag>

# Access
https://<your-ingress-host>
```

## Features

- **AI Insights** — automated cluster health, problematic pods, resource, and security analysis
- **AI Chat** — conversational assistant with live K8s + Prometheus context
- **Logs** — Loki log browser with filtering
- **Egress / Network Test** — TCP connectivity test s SNAT IP lookup via Cilium BPF + FW ticket XLS generátor
- **Multi-cluster** — switch between clusters in the sidebar
- **Local LLMs** — Ollama with phi3.5 / qwen3.5:2b / qwen3:8b, no external AI calls
- **Grafana integration** — Prometheus metrics and firing alerts in chat context
- **K8sGPT** — automated K8s issue analysis via k8sgpt-operator

## Documentation

| Document | Description |
|---|---|
| [docs/architecture.md](docs/architecture.md) | Component overview, data flows, environment variables |
| [docs/deployment.md](docs/deployment.md) | Helm install, upgrade, values reference |
| [docs/ai-chat.md](docs/ai-chat.md) | AI Chat tab usage, context, examples |
| [docs/ai-insights.md](docs/ai-insights.md) | AI Insights tab usage and analysis types |
| [docs/grafana-integration.md](docs/grafana-integration.md) | Grafana REST API integration details |
| [docs/skills.md](docs/skills.md) | Customizing AI system prompts via values.yaml |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Common issues and fixes |

## Deployment Info

| Item | Value |
|---|---|
| Namespace | `ai-local` (configurable) |
| Helm release | `ai-local` (configurable) |
| Image registry | Set `webui.image.repository` in your env-specific values file |
| Kubeconfig | Pass via `--kubeconfig` or `KUBECONFIG` env var |

Environment-specific values (registry, ingress host, tokens, nodeSelector) go in a local `helm/values-<cluster>.yaml` — see [docs/deployment.md](docs/deployment.md).

## Repository Structure

```
k8s-ai/
├── app/                      # Python application
│   ├── app.py                # Streamlit web application
│   ├── k8s_analyzer.py       # K8s API + Grafana client
│   ├── rancher_client.py     # Rancher multi-cluster support
│   ├── translations.py       # CZ/EN UI translations
│   ├── requirements.txt      # Python dependencies
│   └── ca-bundle.pem         # Corporate CA bundle
├── helm/                     # Helm chart
│   ├── Chart.yaml            # Chart metadata
│   ├── values.yaml           # Generic defaults (in git)
│   ├── values-<cluster>.yaml # Env-specific overrides (NOT in git)
│   ├── charts/               # Helm subchart archives
│   ├── crds/                 # K8sGPT CRDs (apply manually)
│   └── templates/            # Helm templates
├── Dockerfile                # Container image
├── scripts/                  # Build, deploy, and debug scripts
└── docs/                     # Documentation
```

## Customizing AI Behavior

Edit `skills.insights` or `skills.chat` in `values.yaml`, then run `helm upgrade` (no image rebuild needed). See [docs/skills.md](docs/skills.md).
