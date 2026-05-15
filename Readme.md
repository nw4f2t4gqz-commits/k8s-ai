# K8s AI Analyzer

AI-powered Kubernetes analysis platform deployed via Helm. Provides a web UI for cluster health monitoring, AI-driven analysis, and interactive chat — all powered by local LLMs (Ollama) running fully in-cluster.

## Quick Start

```bash
# Build and deploy
./scripts/build-deploy.sh v2026-05-15-17

# Access
https://ai.apps.eudrpkbe0001.k8s.corp
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
| Cluster | `eudrpkbe0001` |
| Namespace | `ai-local` |
| Helm release | `ai-local` |
| Image registry | `central-system-repo.app.corp:10443/9tech/ai/webui` |
| Kubeconfig | `kubeconfig/eudrpkbe0001.kubeconfig` |

## Repository Structure

```
k8s-ai/
├── app.py                    # Streamlit web application
├── k8s_analyzer.py           # K8s API + Grafana client
├── rancher_client.py         # Rancher multi-cluster support
├── requirements.txt          # Python dependencies
├── Dockerfile                # Container image
├── values.yaml               # Helm values (models, skills, Grafana)
├── Chart.yaml                # Helm chart metadata
├── ca-bundle.pem             # Corporate CA bundle
├── charts/                   # Helm subchart archives
├── templates/                # Helm templates
│   ├── common/               # RBAC, SA, ConfigMaps
│   └── webui/                # Deployment, Ingress, Skills ConfigMap
├── scripts/                  # Build, deploy, and debug scripts
└── docs/                     # Documentation
```

## Customizing AI Behavior

Edit `skills.insights` or `skills.chat` in `values.yaml`, then run `helm upgrade` (no image rebuild needed). See [docs/skills.md](docs/skills.md).
